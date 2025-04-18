import logging
from collections.abc import Callable
from operator import attrgetter
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError
from pydantic import ValidationError

from ..._service_solvers import SolverService
from ...exceptions.service_errors_utils import DEFAULT_BACKEND_SERVICE_STATUS_CODES
from ...models.basic_types import VersionStr
from ...models.pagination import OnePage, Page, PaginationParams
from ...models.schemas.errors import ErrorGet
from ...models.schemas.model_adapter import ServicePricingPlanGetLegacy
from ...models.schemas.solvers import Solver, SolverKeyId, SolverPort
from ...services_http.catalog import CatalogApi
from ..dependencies.application import get_reverse_url_mapper
from ..dependencies.authentication import get_current_user_id, get_product_name
from ..dependencies.services import get_api_client
from ..dependencies.webserver_http import AuthSession, get_webserver_session
from ._common import API_SERVER_DEV_FEATURES_ENABLED
from ._constants import (
    FMSG_CHANGELOG_NEW_IN_VERSION,
    FMSG_CHANGELOG_REMOVED_IN_VERSION_FORMAT,
    create_route_description,
)

_logger = logging.getLogger(__name__)

_SOLVER_STATUS_CODES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Not found",
        "model": ErrorGet,
    },
    **DEFAULT_BACKEND_SERVICE_STATUS_CODES,
}

router = APIRouter()

## SOLVERS -----------------------------------------------------------------------------------------
#
# - TODO: pagination, result ordering, filter field and results fields?? SEE https://cloud.google.com/apis/design/standard_methods#list
# - TODO: :search? SEE https://cloud.google.com/apis/design/custom_methods#common_custom_methods
# - TODO: move more of this logic to catalog service
# - TODO: error handling!!!
# - TODO: allow release_tags instead of versions in the next iteration.
#    Would be nice to have /solvers/foo/releases/latest or solvers/foo/releases/3 , similar to docker tagging


@router.get(
    "",
    response_model=list[Solver],
    responses=_SOLVER_STATUS_CODES,
    description=create_route_description(
        base="Lists all available solvers (latest version)",
        deprecated=True,
        alternative="GET /v0/solvers/page",
        changelog=[
            FMSG_CHANGELOG_NEW_IN_VERSION.format("0.5.0", ""),
            FMSG_CHANGELOG_REMOVED_IN_VERSION_FORMAT.format(
                "0.7",
                "This endpoint is deprecated and will be removed in a future version",
            ),
        ],
    ),
)
async def list_solvers(
    user_id: Annotated[int, Depends(get_current_user_id)],
    catalog_client: Annotated[CatalogApi, Depends(get_api_client(CatalogApi))],
    url_for: Annotated[Callable, Depends(get_reverse_url_mapper)],
    product_name: Annotated[str, Depends(get_product_name)],
):
    """Lists all available solvers (latest version)"""
    solvers: list[Solver] = await catalog_client.list_latest_releases(
        user_id=user_id, product_name=product_name
    )

    for solver in solvers:
        solver.url = url_for(
            "get_solver_release", solver_key=solver.id, version=solver.version
        )

    return sorted(solvers, key=attrgetter("id"))


@router.get(
    "/page",
    response_model=Page[Solver],
    include_in_schema=API_SERVER_DEV_FEATURES_ENABLED,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def get_solvers_page(
    page_params: Annotated[PaginationParams, Depends()],
):
    msg = f"list solvers with pagination={page_params!r}"
    raise NotImplementedError(msg)


@router.get(
    "/releases",
    response_model=list[Solver],
    summary="Lists All Releases",
    responses=_SOLVER_STATUS_CODES,
)
async def list_solvers_releases(
    user_id: Annotated[int, Depends(get_current_user_id)],
    catalog_client: Annotated[CatalogApi, Depends(get_api_client(CatalogApi))],
    url_for: Annotated[Callable, Depends(get_reverse_url_mapper)],
    product_name: Annotated[str, Depends(get_product_name)],
):
    """Lists all released solvers i.e. all released versions

    SEE get_solvers_releases_page for a paginated version of this function
    """
    assert await catalog_client.is_responsive()  # nosec

    services = await catalog_client.list_services(
        user_id=user_id,
        product_name=product_name,
        predicate=None,
        type_filter="COMPUTATIONAL",
    )
    solvers = [service.to_solver() for service in services]

    for solver in solvers:
        solver.url = url_for(
            "get_solver_release", solver_key=solver.id, version=solver.version
        )

    return sorted(solvers, key=attrgetter("id", "pep404_version"))


@router.get(
    "/releases/page",
    response_model=Page[Solver],
    include_in_schema=API_SERVER_DEV_FEATURES_ENABLED,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def get_solvers_releases_page(
    page_params: Annotated[PaginationParams, Depends()],
):
    msg = f"list solvers releases with pagination={page_params!r}"
    raise NotImplementedError(msg)


@router.get(
    "/{solver_key:path}/latest",
    response_model=Solver,
    summary="Get Latest Release of a Solver",
    responses=_SOLVER_STATUS_CODES,
)
async def get_solver(
    solver_key: SolverKeyId,
    user_id: Annotated[int, Depends(get_current_user_id)],
    solver_service: Annotated[SolverService, Depends(SolverService)],
    url_for: Annotated[Callable, Depends(get_reverse_url_mapper)],
    product_name: Annotated[str, Depends(get_product_name)],
) -> Solver:
    """Gets latest release of a solver"""
    # IMPORTANT: by adding /latest, we avoid changing the order of this entry in the router list
    # otherwise, {solver_key:path} will override and consume any of the paths that follow.
    try:
        solver = await solver_service.get_latest_release(
            user_id=user_id,
            solver_key=solver_key,
            product_name=product_name,
        )
        solver.url = url_for(
            "get_solver_release", solver_key=solver.id, version=solver.version
        )
        assert solver.id == solver_key  # nosec
        return solver

    except (KeyError, HTTPStatusError, IndexError) as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solver with id={solver_key} not found",
        ) from err


@router.get(
    "/{solver_key:path}/releases",
    response_model=list[Solver],
    responses=_SOLVER_STATUS_CODES,
)
async def list_solver_releases(
    solver_key: SolverKeyId,
    user_id: Annotated[int, Depends(get_current_user_id)],
    catalog_client: Annotated[CatalogApi, Depends(get_api_client(CatalogApi))],
    url_for: Annotated[Callable, Depends(get_reverse_url_mapper)],
    product_name: Annotated[str, Depends(get_product_name)],
):
    """Lists all releases of a given (one) solver

    SEE get_solver_releases_page for a paginated version of this function
    """
    releases: list[Solver] = await catalog_client.list_service_releases(
        user_id=user_id,
        solver_key=solver_key,
        product_name=product_name,
    )

    for solver in releases:
        solver.url = url_for(
            "get_solver_release", solver_key=solver.id, version=solver.version
        )

    return sorted(releases, key=attrgetter("pep404_version"))


@router.get(
    "/{solver_key:path}/releases/page",
    response_model=Page[Solver],
    include_in_schema=API_SERVER_DEV_FEATURES_ENABLED,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def get_solver_releases_page(
    solver_key: SolverKeyId,
    page_params: Annotated[PaginationParams, Depends()],
):
    msg = f"list solver {solver_key=} (one) releases with pagination={page_params!r}"
    raise NotImplementedError(msg)


@router.get(
    "/{solver_key:path}/releases/{version}",
    response_model=Solver,
    responses=_SOLVER_STATUS_CODES,
)
async def get_solver_release(
    solver_key: SolverKeyId,
    version: VersionStr,
    user_id: Annotated[int, Depends(get_current_user_id)],
    solver_service: Annotated[SolverService, Depends(SolverService)],
    url_for: Annotated[Callable, Depends(get_reverse_url_mapper)],
    product_name: Annotated[str, Depends(get_product_name)],
) -> Solver:
    """Gets a specific release of a solver"""
    try:
        solver: Solver = await solver_service.get_solver(
            user_id=user_id,
            name=solver_key,
            version=version,
            product_name=product_name,
        )

        solver.url = url_for(
            "get_solver_release", solver_key=solver.id, version=solver.version
        )
        return solver

    except (
        ValueError,
        IndexError,
        ValidationError,
        HTTPStatusError,
    ) as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solver {solver_key}:{version} not found",
        ) from err


@router.get(
    "/{solver_key:path}/releases/{version}/ports",
    response_model=OnePage[SolverPort],
    responses=_SOLVER_STATUS_CODES,
    description="Lists inputs and outputs of a given solver\n\n"
    + FMSG_CHANGELOG_NEW_IN_VERSION.format("0.5.0"),
)
async def list_solver_ports(
    solver_key: SolverKeyId,
    version: VersionStr,
    user_id: Annotated[int, Depends(get_current_user_id)],
    catalog_client: Annotated[CatalogApi, Depends(get_api_client(CatalogApi))],
    product_name: Annotated[str, Depends(get_product_name)],
):
    ports = await catalog_client.get_service_ports(
        user_id=user_id,
        name=solver_key,
        version=version,
        product_name=product_name,
    )

    return OnePage[SolverPort].model_validate(dict(items=ports))


@router.get(
    "/{solver_key:path}/releases/{version}/pricing_plan",
    response_model=ServicePricingPlanGetLegacy,
    description="Gets solver pricing plan\n\n"
    + FMSG_CHANGELOG_NEW_IN_VERSION.format("0.7"),
    responses=_SOLVER_STATUS_CODES,
)
async def get_solver_pricing_plan(
    solver_key: SolverKeyId,
    version: VersionStr,
    user_id: Annotated[int, Depends(get_current_user_id)],
    webserver_api: Annotated[AuthSession, Depends(get_webserver_session)],
    product_name: Annotated[str, Depends(get_product_name)],
):
    assert user_id
    assert product_name
    pricing_plan_or_none = await webserver_api.get_service_pricing_plan(
        solver_key=solver_key, version=version
    )
    # NOTE: pricing_plan_or_none https://github.com/ITISFoundation/osparc-simcore/issues/6901
    assert pricing_plan_or_none  # nosec
    return pricing_plan_or_none
