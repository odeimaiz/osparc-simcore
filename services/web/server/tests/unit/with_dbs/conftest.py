""" Configuration for unit testing with a postgress fixture

    - Unit testing of webserver app with a postgress service as fixture
    - Starts test session by running a postgres container as a fixture (see postgress_service)

    IMPORTANT: remember that these are still unit-tests!
"""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable

import json
import os
import sys
import textwrap
from copy import deepcopy
from pathlib import Path
from typing import Callable, Dict, Iterator, List
from uuid import uuid4

import aioredis
import pytest
import redis
import simcore_postgres_database.cli as pg_cli
import simcore_service_webserver.db_models as orm
import simcore_service_webserver.utils
import sqlalchemy as sa
import trafaret_config
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from pydantic import BaseSettings
from pytest_simcore.helpers.utils_login import NewUser
from servicelib.aiopg_utils import DSN
from servicelib.application_keys import APP_CONFIG_KEY, APP_DB_ENGINE_KEY
from simcore_service_webserver.application import create_application
from simcore_service_webserver.application_config import app_schema as app_schema
from simcore_service_webserver.constants import APP_DB_ENGINE_KEY, INDEX_RESOURCE_NAME
from simcore_service_webserver.groups_api import (
    add_user_in_group,
    create_user_group,
    delete_user_group,
    list_user_groups,
)
from yarl import URL

# current directory
current_dir = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent


# DEPLOYED SERVICES FOR TESTSUITE SESSION -----------------------------------


@pytest.fixture(scope="session")
def default_app_cfg(osparc_simcore_root_dir):
    # NOTE: ONLY used at the session scopes
    cfg_path = current_dir / "config.yaml"
    assert cfg_path.exists()

    variables = dict(os.environ)
    variables.update(
        {
            "OSPARC_SIMCORE_REPO_ROOTDIR": str(osparc_simcore_root_dir),
        }
    )

    # validates and fills all defaults/optional entries that normal load would not do
    cfg_dict = trafaret_config.read_and_validate(cfg_path, app_schema, vars=variables)

    # WARNING: changes to this fixture during testing propagates to other tests. Use cfg = deepcopy(cfg_dict)
    # FIXME:  free cfg_dict but deepcopy shall be r/w
    return cfg_dict


@pytest.fixture(scope="session")
def docker_compose_file(default_app_cfg, monkeypatch_session):
    """Overrides pytest-docker fixture"""

    cfg = deepcopy(default_app_cfg["db"]["postgres"])

    # docker-compose reads these environs
    monkeypatch_session.setenv("TEST_POSTGRES_DB", cfg["database"])
    monkeypatch_session.setenv("TEST_POSTGRES_USER", cfg["user"])
    monkeypatch_session.setenv("TEST_POSTGRES_PASSWORD", cfg["password"])

    dc_path = current_dir / "docker-compose-devel.yml"

    assert dc_path.exists()
    yield str(dc_path)


# WEB SERVER/CLIENT FIXTURES ------------------------------------------------


@pytest.fixture(scope="function")
def app_cfg(default_app_cfg, aiohttp_unused_port) -> Dict:
    """Can be overriden in any test module to configure
    the app accordingly
    """
    cfg = deepcopy(default_app_cfg)

    # fills ports on the fly
    cfg["main"]["port"] = aiohttp_unused_port()
    cfg["storage"]["port"] = aiohttp_unused_port()

    # this fixture can be safely modified during test since it is renovated on every call
    return cfg


class _BaseSettingEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseSettings):
            return o.json()
        elif isinstance(o, Path):
            return str(o)

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


@pytest.fixture
def web_server(
    loop,
    app_cfg: Dict,
    monkeypatch,
    postgres_db,
    aiohttp_server,
    disable_static_webserver,
) -> TestServer:
    print(
        "Inits webserver with app_cfg",
        json.dumps(app_cfg, indent=2, cls=_BaseSettingEncoder),
    )

    # original APP
    app = create_application(app_cfg)

    assert app[APP_CONFIG_KEY] == app_cfg

    # with patched email
    _path_mail(monkeypatch)

    disable_static_webserver(app)

    server = loop.run_until_complete(aiohttp_server(app, port=app_cfg["main"]["port"]))

    assert isinstance(postgres_db, sa.engine.Engine)
    pg_settings = dict(e.split("=") for e in app[APP_DB_ENGINE_KEY].dsn.split())
    assert pg_settings["host"] == postgres_db.url.host
    assert int(pg_settings["port"]) == postgres_db.url.port
    assert pg_settings["user"] == postgres_db.url.username

    return server


@pytest.fixture
def client(
    loop, aiohttp_client, web_server: TestServer, mock_orphaned_services
) -> TestClient:
    cli = loop.run_until_complete(aiohttp_client(web_server))
    return cli


# SUBSYSTEM MOCKS FIXTURES ------------------------------------------------
#
# Mocks entirely or part of the calls to the web-server subsystems
#


@pytest.fixture
def disable_static_webserver(monkeypatch) -> Callable:
    """
    Disables the static-webserver module.
    Avoids fecthing and caching index.html pages
    Mocking a response for all the services which expect it.
    """

    async def _mocked_index_html(request: web.Request) -> web.Response:
        """
        Emulates the reply of the '/' path when the static-webserver is disabled
        """
        html = textwrap.dedent(
            """\
            <!DOCTYPE html>
            <html>
            <body>
                <h1>OSPARC-SIMCORE</h1>
                <p> This is a result of disable_static_webserver fixture for product OSPARC</p>
            </body>
            </html>
            """
        )
        return web.Response(text=html)

    # mount and serve some staic mocked content
    monkeypatch.setenv("WEBSERVER_STATIC_MODULE_ENABLED", "false")

    def add_index_route(app: web.Application) -> None:
        app.router.add_get("/", _mocked_index_html, name=INDEX_RESOURCE_NAME)

    return add_index_route


@pytest.fixture
def computational_system_mock(mocker):
    mock_fun = mocker.patch(
        "simcore_service_webserver.projects.projects_handlers.update_pipeline_db",
        return_value="",
    )
    return mock_fun


@pytest.fixture
async def storage_subsystem_mock(loop, mocker):
    """
    Patches client calls to storage service

    Patched functions are exposed within projects but call storage subsystem
    """
    # requests storage to copy data
    mock = mocker.patch(
        "simcore_service_webserver.projects.projects_handlers.copy_data_folders_from_project"
    )

    async def _mock_copy_data_from_project(*args):
        return args[2]

    mock.side_effect = _mock_copy_data_from_project

    # requests storage to delete data
    async_mock = mocker.AsyncMock(return_value="")
    mock1 = mocker.patch(
        "simcore_service_webserver.projects.projects_handlers.projects_api.delete_data_folders_of_project",
        side_effect=async_mock,
    )
    return mock, mock1


@pytest.fixture
def asyncpg_storage_system_mock(mocker):
    mocked_method = mocker.patch(
        "simcore_service_webserver.login.storage.AsyncpgStorage.delete_user",
        return_value="",
    )
    return mocked_method


@pytest.fixture
async def mocked_director_api(loop, mocker):
    # NOTE: patches are done at 'simcore_service_webserver.director.director_api'
    #
    #  Read carefully "where to patch" in https://docs.python.org/3/library/unittest.mock.html#id6
    #
    mocks = {}
    for func_name, fake_return in [
        ("get_running_interactive_services", []),
        ("start_service", []),
        ("stop_service", None),
    ]:
        mocks[func_name] = mocker.patch(
            f"simcore_service_webserver.director.director_api.{func_name}",
            return_value=fake_return,
            name=f"{__name__}.mocked_director_api::director_api.{func_name}",
        )

    return mocks


@pytest.fixture
async def mocked_dynamic_service(loop, client, mocked_director_api):
    services = []

    async def create(user_id, project_id) -> Dict:
        SERVICE_UUID = str(uuid4())
        SERVICE_KEY = "simcore/services/dynamic/3d-viewer"
        SERVICE_VERSION = "1.4.2"
        url = client.app.router["create_node"].url_for(project_id=project_id)
        create_node_data = {
            "service_key": SERVICE_KEY,
            "service_version": SERVICE_VERSION,
            "service_uuid": SERVICE_UUID,
        }

        running_service_dict = {
            "published_port": "23423",
            "service_uuid": SERVICE_UUID,
            "service_key": SERVICE_KEY,
            "service_version": SERVICE_VERSION,
            "service_host": "some_service_host",
            "service_port": "some_service_port",
            "service_state": "some_service_state",
        }

        services.append(running_service_dict)
        # reset the future or an invalidStateError will appear as set_result sets the future to done
        mocked_director_api["get_running_interactive_services"].return_value = services
        return running_service_dict

    return create


# POSTGRES CORE SERVICE ---------------------------------------------------


@pytest.fixture(scope="session")
def postgres_dsn(docker_services, docker_ip, default_app_cfg: Dict) -> Dict:
    cfg = deepcopy(default_app_cfg["db"]["postgres"])
    cfg["host"] = docker_ip
    cfg["port"] = docker_services.port_for("postgres", 5432)
    return cfg


@pytest.fixture(scope="session")
def postgres_service(docker_services, postgres_dsn):
    url = DSN.format(**postgres_dsn)

    # Wait until service is responsive.
    docker_services.wait_until_responsive(
        check=lambda: _is_postgres_responsive(url),
        timeout=30.0,
        pause=0.1,
    )

    return url


@pytest.fixture()
def postgres_db(
    postgres_dsn: Dict, postgres_service: str
) -> Iterator[sa.engine.Engine]:
    # Overrides packages/pytest-simcore/src/pytest_simcore/postgres_service.py::postgres_db to reduce scope
    url = postgres_service

    # Configures db and initializes tables
    kwargs = postgres_dsn.copy()
    pg_cli.discover.callback(**kwargs)
    pg_cli.upgrade.callback("head")
    # Uses syncrounous engine for that
    engine = sa.create_engine(url, isolation_level="AUTOCOMMIT")

    yield engine

    pg_cli.downgrade.callback("base")
    pg_cli.clean.callback()

    orm.metadata.drop_all(engine)
    engine.dispose()


# REDIS CORE SERVICE ------------------------------------------------------


@pytest.fixture(scope="session")
def redis_service(docker_services, docker_ip) -> URL:

    host = docker_ip
    port = docker_services.port_for("redis", 6379)
    url = URL(f"redis://{host}:{port}")

    docker_services.wait_until_responsive(
        check=lambda: _is_redis_responsive(host, port),
        timeout=30.0,
        pause=0.1,
    )
    return url


@pytest.fixture
async def redis_client(loop, redis_service):
    client = await aioredis.create_redis_pool(str(redis_service), encoding="utf-8")
    yield client

    await client.flushall()
    client.close()
    await client.wait_closed()


def _is_redis_responsive(host: str, port: int) -> bool:
    r = redis.Redis(host=host, port=port)
    return r.ping() == True


# SOCKETS FIXTURES  --------------------------------------------------------

# Moved to packages/pytest-simcore/src/pytest_simcore/websocket_client.py


# USER GROUP FIXTURES -------------------------------------------------------


@pytest.fixture
async def primary_group(client, logged_user) -> Dict[str, str]:
    primary_group, _, _ = await list_user_groups(client.app, logged_user["id"])
    return primary_group


@pytest.fixture
async def standard_groups(client, logged_user: Dict) -> List[Dict[str, str]]:
    # create a separate admin account to create some standard groups for the logged user
    sparc_group = {
        "gid": "5",  # this will be replaced
        "label": "SPARC",
        "description": "Stimulating Peripheral Activity to Relieve Conditions",
        "thumbnail": "https://commonfund.nih.gov/sites/default/files/sparc-image-homepage500px.png",
        "inclusionRules": {"email": r"@(sparc)+\.(io|com)$"},
    }
    team_black_group = {
        "gid": "5",  # this will be replaced
        "label": "team Black",
        "description": "THE incredible black team",
        "thumbnail": None,
        "inclusionRules": {"email": r"@(black)+\.(io|com)$"},
    }
    async with NewUser(
        {"name": f"{logged_user['name']}_admin", "role": "USER"}, client.app
    ) as admin_user:
        # creates two groups
        sparc_group = await create_user_group(client.app, admin_user["id"], sparc_group)
        team_black_group = await create_user_group(
            client.app, admin_user["id"], team_black_group
        )

        # adds logged_user  to sparc group
        await add_user_in_group(
            client.app,
            admin_user["id"],
            sparc_group["gid"],
            new_user_id=logged_user["id"],
        )

        # adds logged_user  to team-black group
        await add_user_in_group(
            client.app,
            admin_user["id"],
            team_black_group["gid"],
            new_user_email=logged_user["email"],
        )

        _, standard_groups, _ = await list_user_groups(client.app, logged_user["id"])
        yield standard_groups
        # clean groups
        await delete_user_group(client.app, admin_user["id"], sparc_group["gid"])
        await delete_user_group(client.app, admin_user["id"], team_black_group["gid"])


@pytest.fixture
async def all_group(client, logged_user) -> Dict[str, str]:
    _, _, all_group = await list_user_groups(client.app, logged_user["id"])
    return all_group


# GENERIC HELPER FUNCTIONS ----------------------------------------------------


def _path_mail(monkeypatch):
    async def send_mail(*args):
        print("=== EMAIL TO: {}\n=== SUBJECT: {}\n=== BODY:\n{}".format(*args))

    monkeypatch.setattr(
        simcore_service_webserver.login.utils, "compose_mail", send_mail
    )


def _is_postgres_responsive(url):
    """Check if something responds to ``url`` """
    try:
        engine = sa.create_engine(url)
        conn = engine.connect()
        conn.close()
    except sa.exc.OperationalError:
        return False
    return True
