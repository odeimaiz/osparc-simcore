# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
# pylint: disable=too-many-arguments


from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, status
from simcore_service_webserver._meta import API_VTAG
from simcore_service_webserver.folders._models import (
    FoldersPathParams,
    RemoveQueryParams,
)
from simcore_service_webserver.projects._trash_handlers import ProjectPathParams
from simcore_service_webserver.projects._trash_handlers import (
    RemoveQueryParams as RemoveQueryParams_duplicated,
)

router = APIRouter(
    prefix=f"/{API_VTAG}",
    tags=["trash"],
)


@router.delete(
    "/trash",
    status_code=status.HTTP_204_NO_CONTENT,
)
def empty_trash():
    ...


_extra_tags: list[str | Enum] = ["projects"]


@router.post(
    "/projects/{project_id}:trash",
    tags=_extra_tags,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not such a project"},
        status.HTTP_409_CONFLICT: {
            "description": "Project is in use and cannot be trashed"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Trash service error"},
    },
)
def trash_project(
    _p: Annotated[ProjectPathParams, Depends()],
    _q: Annotated[RemoveQueryParams, Depends()],
):
    ...


@router.post(
    "/projects/{project_id}:untrash",
    tags=_extra_tags,
    status_code=status.HTTP_204_NO_CONTENT,
)
def untrash_project(
    _p: Annotated[ProjectPathParams, Depends()],
):
    ...


_extra_tags = ["folders"]


@router.post(
    "/folders/{folder_id}:trash",
    tags=_extra_tags,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not such a folder"},
        status.HTTP_409_CONFLICT: {
            "description": "One or more projects is in use and cannot be trashed"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Trash service error"},
    },
)
def trash_folder(
    _p: Annotated[FoldersPathParams, Depends()],
    _q: Annotated[RemoveQueryParams_duplicated, Depends()],
):
    ...


@router.post(
    "/folders/{folder_id}:untrash",
    tags=_extra_tags,
    status_code=status.HTTP_204_NO_CONTENT,
)
def untrash_folder(
    _p: Annotated[FoldersPathParams, Depends()],
):
    ...
