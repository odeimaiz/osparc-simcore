# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=unused-argument
# pylint: disable=unused-variable

import pytest
from fastapi import FastAPI
from models_library.api_schemas_catalog.services import LatestServiceGet, ServiceGetV2
from models_library.products import ProductName
from models_library.services_history import ServiceRelease
from models_library.users import UserID
from pydantic import HttpUrl
from pytest_mock import MockerFixture, MockType
from simcore_service_api_server.models.schemas.solvers import Solver
from simcore_service_api_server.services_rpc.catalog import CatalogService


@pytest.fixture
def product_name() -> ProductName:
    return "osparc"


def to_solver(
    service: LatestServiceGet | ServiceGetV2, href_self: HttpUrl | None = None
) -> Solver:
    # NOTE: this is an adapter around models on CatalogService interface
    return Solver(
        id=service.key,
        version=service.version,
        title=service.name,
        maintainer=service.owner or service.contact or "UNKNOWN",
        url=href_self,
        description=service.description,
    )


async def test_catalog_service_read_solvers(
    app: FastAPI,
    product_name: ProductName,
    user_id: UserID,
    mocker: MockerFixture,
    mocked_rpc_catalog_service_api: dict[str, MockType],
):
    catalog_service = CatalogService(client=mocker.MagicMock())

    # Step 1: List latest releases in a page
    latest_releases, meta = await catalog_service.list_latest_releases(
        product_name=product_name, user_id=user_id
    )
    solver_releases_page = [to_solver(srv) for srv in latest_releases]

    assert solver_releases_page, "Releases page should not be empty"
    assert meta.offset == 0

    # Step 2: Select one release and list solver releases
    selected_solver = solver_releases_page[0]
    releases, meta = await catalog_service.list_release_history(
        product_name=product_name,
        user_id=user_id,
        service_key=selected_solver.id,
    )
    assert releases, "Solver releases should not be empty"
    assert meta.offset == 0

    # Step 3: Take the latest solver release and get solver details
    oldest_release: ServiceRelease = releases[-1]

    service: ServiceGetV2 = await catalog_service.get(
        product_name=product_name,
        user_id=user_id,
        name=selected_solver.id,
        version=oldest_release.version,
    )
    solver = to_solver(service)
    assert solver.id == selected_solver.id
    assert solver.version == oldest_release.version

    # checks calls to rpc
    mocked_rpc_catalog_service_api["list_services_paginated"].assert_called_once()
    mocked_rpc_catalog_service_api[
        "list_my_service_history_paginated"
    ].assert_called_once()
    mocked_rpc_catalog_service_api["get_service"].assert_called_once()
