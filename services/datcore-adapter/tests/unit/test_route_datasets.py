# pylint:disable=unused-variable
# pylint:disable=unused-argument
# pylint:disable=redefined-outer-name


import httpx
import respx
from fastapi_pagination import LimitOffsetPage
from models_library.api_schemas_datcore_adapter.datasets import (
    DatasetMetaData,
    FileMetaData,
)
from pydantic import TypeAdapter
from starlette import status


async def test_get_dataset_entrypoint(
    async_client: httpx.AsyncClient,
    pennsieve_dataset_id: str,
    pennsieve_subsystem_mock: respx.MockRouter | None,
    pennsieve_api_headers: dict[str, str],
):
    response = await async_client.get(
        f"v0/datasets/{pennsieve_dataset_id}",
        headers=pennsieve_api_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data
    TypeAdapter(DatasetMetaData).validate_python(data)


async def test_list_datasets_entrypoint(
    async_client: httpx.AsyncClient,
    pennsieve_subsystem_mock: respx.MockRouter | None,
    pennsieve_api_headers: dict[str, str],
):
    response = await async_client.get(
        "v0/datasets",
        headers=pennsieve_api_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data
    TypeAdapter(LimitOffsetPage[DatasetMetaData]).validate_python(data)


async def test_list_dataset_files_legacy_entrypoint(
    async_client: httpx.AsyncClient,
    pennsieve_dataset_id: str,
    pennsieve_subsystem_mock,
    pennsieve_api_headers: dict[str, str],
):
    dataset_id = pennsieve_dataset_id

    response = await async_client.get(
        f"v0/datasets/{dataset_id}/files_legacy",
        headers=pennsieve_api_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data
    TypeAdapter(list[FileMetaData]).validate_python(data)


async def test_list_dataset_top_level_files_entrypoint(
    async_client: httpx.AsyncClient,
    pennsieve_dataset_id: str,
    pennsieve_subsystem_mock,
    pennsieve_api_headers: dict[str, str],
):
    dataset_id = pennsieve_dataset_id

    response = await async_client.get(
        f"v0/datasets/{dataset_id}/files",
        headers=pennsieve_api_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data
    TypeAdapter(LimitOffsetPage[FileMetaData]).validate_python(data)


async def test_list_dataset_collection_files_entrypoint(
    async_client: httpx.AsyncClient,
    pennsieve_dataset_id: str,
    pennsieve_collection_id: str,
    pennsieve_subsystem_mock,
    pennsieve_api_headers: dict[str, str],
):
    dataset_id = pennsieve_dataset_id
    collection_id = pennsieve_collection_id

    response = await async_client.get(
        f"v0/datasets/{dataset_id}/files/{collection_id}",
        headers=pennsieve_api_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data
    TypeAdapter(LimitOffsetPage[FileMetaData]).validate_python(data)
