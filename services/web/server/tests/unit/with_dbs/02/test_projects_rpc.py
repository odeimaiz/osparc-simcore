# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
# pylint: disable=too-many-arguments


from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID

import pytest
from aiohttp.test_utils import TestClient
from common_library.users_enums import UserRole
from models_library.products import ProductName
from models_library.projects import ProjectID
from models_library.rpc.webserver.projects import (
    ListProjectsMarkedAsJobRpcFilters,
    MetadataFilterItem,
    PageRpcProjectJobRpcGet,
    ProjectJobRpcGet,
)
from pydantic import ValidationError
from pytest_simcore.helpers.monkeypatch_envs import setenvs_from_dict
from pytest_simcore.helpers.typing_env import EnvVarsDict
from pytest_simcore.helpers.webserver_users import NewUser, UserInfoDict
from servicelib.rabbitmq import RabbitMQRPCClient
from servicelib.rabbitmq.rpc_interfaces.webserver import projects as projects_rpc
from servicelib.rabbitmq.rpc_interfaces.webserver.errors import (
    ProjectForbiddenRpcError,
    ProjectNotFoundRpcError,
)
from settings_library.rabbit import RabbitSettings
from simcore_service_webserver.application_settings import ApplicationSettings
from simcore_service_webserver.projects.models import ProjectDict

pytest_simcore_core_services_selection = [
    "rabbit",
]


@pytest.fixture
def user_role() -> UserRole:
    # for logged_user
    return UserRole.USER


@pytest.fixture
def app_environment(
    rabbit_service: RabbitSettings,
    app_environment: EnvVarsDict,
    monkeypatch: pytest.MonkeyPatch,
):
    new_envs = setenvs_from_dict(
        monkeypatch,
        {
            **app_environment,
            "RABBIT_HOST": rabbit_service.RABBIT_HOST,
            "RABBIT_PORT": f"{rabbit_service.RABBIT_PORT}",
            "RABBIT_USER": rabbit_service.RABBIT_USER,
            "RABBIT_SECURE": f"{rabbit_service.RABBIT_SECURE}",
            "RABBIT_PASSWORD": rabbit_service.RABBIT_PASSWORD.get_secret_value(),
        },
    )

    settings = ApplicationSettings.create_from_envs()
    assert settings.WEBSERVER_RABBITMQ

    return new_envs


@pytest.fixture
async def rpc_client(
    rabbitmq_rpc_client: Callable[[str], Awaitable[RabbitMQRPCClient]],
) -> RabbitMQRPCClient:
    return await rabbitmq_rpc_client("client")


async def test_rpc_client_mark_project_as_job(
    rpc_client: RabbitMQRPCClient,
    product_name: ProductName,
    logged_user: UserInfoDict,
    user_project: ProjectDict,
):
    # `logged_user` OWNS the `user_project` but not `other_user`
    project_uuid: ProjectID = UUID(user_project["uuid"])
    user_id = logged_user["id"]

    await projects_rpc.mark_project_as_job(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        project_uuid=project_uuid,
        job_parent_resource_name="solvers/solver123/version/1.2.3",
    )


async def test_rpc_client_list_my_projects_marked_as_jobs(
    rpc_client: RabbitMQRPCClient,
    product_name: ProductName,
    logged_user: UserInfoDict,
    user_project: ProjectDict,
):
    project_uuid = ProjectID(user_project["uuid"])
    user_id = logged_user["id"]

    # Mark the project as a job first
    await projects_rpc.mark_project_as_job(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        project_uuid=project_uuid,
        job_parent_resource_name="solvers/solver123/version/1.2.3",
    )

    # List projects marked as jobs
    page: PageRpcProjectJobRpcGet = await projects_rpc.list_projects_marked_as_jobs(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        filters=ListProjectsMarkedAsJobRpcFilters(
            job_parent_resource_name_prefix="solvers/solver123"
        ),
    )

    assert page.meta.total == 1
    assert page.meta.offset == 0
    assert isinstance(page.data[0], ProjectJobRpcGet)

    project_job = page.data[0]
    assert project_job.uuid == project_uuid
    assert project_job.name == user_project["name"]
    assert project_job.description == user_project["description"]

    assert set(project_job.workbench.keys()) == set(user_project["workbench"].keys())


@pytest.fixture
async def other_user(
    client: TestClient,
    logged_user: UserInfoDict,
) -> AsyncIterator[UserInfoDict]:

    async with NewUser(
        user_data={
            "name": "other-user",
            "email": "other-user" + logged_user["email"],
        },
        app=client.app,
    ) as other_user_info:

        assert other_user_info["name"] != logged_user["name"]
        yield other_user_info


async def test_errors_on_rpc_client_mark_project_as_job(
    rpc_client: RabbitMQRPCClient,
    product_name: ProductName,
    logged_user: UserInfoDict,
    other_user: UserInfoDict,
    user_project: ProjectDict,
):
    # `logged_user` OWNS the `user_project` but not `other_user`
    project_uuid: ProjectID = UUID(user_project["uuid"])
    user_id = logged_user["id"]
    other_user_id = other_user["id"]

    with pytest.raises(ProjectForbiddenRpcError) as exc_info:
        await projects_rpc.mark_project_as_job(
            rpc_client=rpc_client,
            product_name=product_name,
            user_id=other_user_id,  # <-- no access
            project_uuid=project_uuid,
            job_parent_resource_name="solvers/solver123/version/1.2.3",
        )

    assert exc_info.value.error_context()["project_uuid"] == project_uuid

    with pytest.raises(ProjectNotFoundRpcError, match="not found"):
        await projects_rpc.mark_project_as_job(
            rpc_client=rpc_client,
            product_name=product_name,
            user_id=logged_user["id"],
            project_uuid=UUID("00000000-0000-0000-0000-000000000000"),  # <-- wont find
            job_parent_resource_name="solvers/solver123/version/1.2.3",
        )

    with pytest.raises(ValidationError, match="job_parent_resource_name") as exc_info:
        await projects_rpc.mark_project_as_job(
            rpc_client=rpc_client,
            product_name=product_name,
            user_id=user_id,
            project_uuid=project_uuid,
            job_parent_resource_name="This is not a resource",  # <-- wrong format
        )

    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors()[0]["loc"] == ("job_parent_resource_name",)
    assert exc_info.value.errors()[0]["type"] == "value_error"


async def test_rpc_client_list_projects_marked_as_jobs_with_metadata_filter(
    rpc_client: RabbitMQRPCClient,
    product_name: ProductName,
    logged_user: UserInfoDict,
    user_project: ProjectDict,
    client: TestClient,
):
    from simcore_service_webserver.projects import _metadata_service

    project_uuid = ProjectID(user_project["uuid"])
    user_id = logged_user["id"]

    # Mark the project as a job
    await projects_rpc.mark_project_as_job(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        project_uuid=project_uuid,
        job_parent_resource_name="solvers/solver123/version/1.2.3",
    )

    # Set custom metadata on the project
    custom_metadata = {
        "solver_type": "FEM",
        "mesh_cells": "10000",
        "domain": "biomedical",
    }

    await _metadata_service.set_project_custom_metadata(
        app=client.app,
        user_id=user_id,
        project_uuid=project_uuid,
        value=custom_metadata,
    )

    # Test with exact match on metadata field
    page: PageRpcProjectJobRpcGet = await projects_rpc.list_projects_marked_as_jobs(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        filters=ListProjectsMarkedAsJobRpcFilters(
            job_parent_resource_name_prefix="solvers/solver123",
            any_custom_metadata=[MetadataFilterItem(name="solver_type", pattern="FEM")],
        ),
    )

    assert page.meta.total == 1
    assert len(page.data) == 1
    assert page.data[0].uuid == project_uuid

    # Test with pattern match on metadata field
    page = await projects_rpc.list_projects_marked_as_jobs(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        filters=ListProjectsMarkedAsJobRpcFilters(
            any_custom_metadata=[MetadataFilterItem(name="mesh_cells", pattern="1*")],
        ),
    )

    assert page.meta.total == 1
    assert len(page.data) == 1
    assert page.data[0].uuid == project_uuid

    # Test with multiple metadata fields (any match should return the project)
    page = await projects_rpc.list_projects_marked_as_jobs(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        filters=ListProjectsMarkedAsJobRpcFilters(
            any_custom_metadata=[
                MetadataFilterItem(name="solver_type", pattern="FEM"),
                MetadataFilterItem(name="non_existent", pattern="value"),
            ],
        ),
    )

    assert page.meta.total == 1
    assert len(page.data) == 1

    # Test with no matches
    page = await projects_rpc.list_projects_marked_as_jobs(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        filters=ListProjectsMarkedAsJobRpcFilters(
            any_custom_metadata=[
                MetadataFilterItem(name="solver_type", pattern="CFD"),  # No match
            ],
        ),
    )

    assert page.meta.total == 0
    assert len(page.data) == 0

    # Test with combination of resource prefix and metadata
    page = await projects_rpc.list_projects_marked_as_jobs(
        rpc_client=rpc_client,
        product_name=product_name,
        user_id=user_id,
        filters=ListProjectsMarkedAsJobRpcFilters(
            job_parent_resource_name_prefix="wrong/prefix",
            any_custom_metadata=[
                MetadataFilterItem(name="solver_type", pattern="FEM"),
            ],
        ),
    )

    assert page.meta.total == 0
    assert len(page.data) == 0
