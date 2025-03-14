from fastapi import APIRouter, FastAPI

from . import _datasets, _files, _health, _locations, _paths, _simcore_s3

v0_router = APIRouter()

health_router = _health.router
v0_router.include_router(_health.router)
v0_router.include_router(_locations.router)
v0_router.include_router(_datasets.router)
v0_router.include_router(_files.router)
v0_router.include_router(_paths.router)
v0_router.include_router(_simcore_s3.router)


def setup_rest_api_routes(app: FastAPI, vtag: str):
    # healthcheck at / and at /v0/
    app.include_router(health_router, prefix=f"/{vtag}")
    # api under /v*
    app.include_router(v0_router, prefix=f"/{vtag}")
