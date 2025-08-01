# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable


import logging
import re
from pathlib import Path
from typing import Any

import pytest
from faker import Faker

from .helpers.monkeypatch_envs import load_dotenv, setenvs_from_dict
from .helpers.typing_env import EnvVarsDict

_logger = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser):
    simcore_group = parser.getgroup("simcore")
    simcore_group.addoption(
        "--external-envfile",
        action="store",
        type=Path,
        default=None,
        help="Path to an env file. Replaces .env-devel in the tests by an external envfile."
        "e.g. consider "
        " `ln -s /path/to/osparc-ops-config/repo.config .secrets` and then "
        " `pytest --external-envfile=.secrets --pdb tests/unit/test_core_settings.py`",
    )


@pytest.fixture(scope="session")
def external_envfile_dict(
    request: pytest.FixtureRequest, osparc_simcore_root_dir: Path
) -> EnvVarsDict:
    """
    If a file under test folder prefixed with `.env-secret` is present,
    then this fixture captures it.

    This technique allows reusing the same tests to check against
    external development/production servers
    """
    envs = {}
    if envfile := request.config.getoption("--external-envfile"):
        _logger.warning(
            "🚨 EXTERNAL `envfile` option detected. Loading '%s' ...", envfile
        )

        assert isinstance(envfile, Path)
        assert envfile.exists()
        assert envfile.is_file()

        envfile = envfile.resolve()
        osparc_simcore_root_dir = osparc_simcore_root_dir.resolve()

        if osparc_simcore_root_dir in envfile.parents and not any(
            term in envfile.name.lower() for term in ("ignore", "secret")
        ):
            _logger.warning(
                "🚨 CAUTION: The external envfile '%s' may contain sensitive data and could be accidentally versioned. "
                "To prevent this, include the words 'secret' or 'ignore' in the filename.",
                envfile.name,
            )

        envs = load_dotenv(envfile)

    if envs:
        response = input(
            f"🚨 CAUTION: You are about to run tests using environment variables loaded from '{envfile}'.\n"
            "This may cause tests to interact with or modify real external systems (e.g., production or staging environments).\n"
            "Proceeding could result in data loss or unintended side effects.\n"
            "Are you sure you want to continue? [y/N]: "
        )
        if response.strip().lower() not in ("y", "yes"):
            pytest.exit("Aborted by user due to external envfile usage.")

    return envs


@pytest.fixture(scope="session")
def skip_if_no_external_envfile(external_envfile_dict: EnvVarsDict) -> None:
    if not external_envfile_dict:
        pytest.skip(reason="Skipping test since external-envfile is not set")


@pytest.fixture(scope="session")
def env_devel_dict(env_devel_file: Path) -> EnvVarsDict:
    assert env_devel_file.exists()
    assert env_devel_file.name == ".env-devel"
    return load_dotenv(env_devel_file, verbose=True, interpolate=True)


@pytest.fixture
def mock_env_devel_environment(
    env_devel_dict: EnvVarsDict, monkeypatch: pytest.MonkeyPatch
) -> EnvVarsDict:
    return setenvs_from_dict(monkeypatch, {**env_devel_dict})


#
# ENVIRONMENT IN A SERVICE
#


@pytest.fixture(scope="session")
def service_name(project_slug_dir: Path) -> str:
    """
    project_slug_dir MUST be defined on root's conftest.py
    """
    return project_slug_dir.name


@pytest.fixture(scope="session")
def docker_compose_services_dict(services_docker_compose_file: Path) -> EnvVarsDict:
    # NOTE: By keeping import here, this library is ONLY required when the fixture is used
    import yaml

    content = yaml.safe_load(services_docker_compose_file.read_text())
    assert "services" in content
    return content


@pytest.fixture
def docker_compose_service_hostname(
    faker: Faker, service_name: str, docker_compose_services_dict: dict[str, Any]
) -> str:
    """Evaluates `hostname` from docker-compose service"""
    hostname_template = docker_compose_services_dict["services"][service_name][
        "hostname"
    ]

    # Generate fake values to replace Docker Swarm template variables
    node_hostname = faker.hostname(levels=1)
    task_slot = faker.random_int(min=0, max=10)

    # Replace the Docker Swarm template variables with faker values
    return hostname_template.replace("{{.Node.Hostname}}", node_hostname).replace(
        "{{.Task.Slot}}", str(task_slot)
    )


@pytest.fixture
def docker_compose_service_environment_dict(
    docker_compose_services_dict: dict[str, Any],
    service_name: str,
    env_devel_dict: EnvVarsDict,
    env_devel_file: Path,
) -> EnvVarsDict:
    """Returns env vars dict from the docker-compose `environment` section

    - env_devel_dict in environment_configs plugin
    - service_name needs to be defined
    """
    service = docker_compose_services_dict["services"][service_name]

    def _substitute(key, value) -> tuple[str, str]:
        if m := re.match(r"\${([^{}:-]\w+)", f"{value}"):
            expected_env_var = m.group(1)
            try:
                # NOTE: if this raises, then the RHS env-vars in the docker-compose are
                # not defined in the env-devel
                if value := env_devel_dict[expected_env_var]:
                    return key, value
            except KeyError:
                pytest.fail(
                    f"{expected_env_var} is not defined in '{env_devel_file}' but it "
                    f"is used as a rhs variable in the docker-compose services[{service_name}].environment[{key}]"
                )
        return key, value

    envs: EnvVarsDict = {}
    for key, value in service.get("environment", {}).items():
        if found := _substitute(key, value):
            _, new_value = found
            envs[key] = new_value

    return envs
