import contextlib
import datetime
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TypeAlias

import sqlalchemy as sa
from models_library.basic_types import SHA256Str
from models_library.projects import ProjectID
from models_library.projects_nodes_io import NodeID, SimcoreS3FileID
from models_library.users import UserID
from models_library.utils.fastapi_encoders import jsonable_encoder
from pydantic import BaseModel
from simcore_postgres_database.storage_models import file_meta_data
from simcore_postgres_database.utils_repos import (
    pass_or_acquire_connection,
    transaction_context,
)
from sqlalchemy import and_, literal_column
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncConnection

from ...exceptions.errors import FileMetaDataNotFoundError
from ...models import (
    FileMetaData,
    FileMetaDataAtDB,
    GenericCursor,
    PathMetaData,
    UserOrProjectFilter,
)
from ._base import BaseRepository

TotalChildren: TypeAlias = int


class _PathsCursorParameters(BaseModel):
    offset: int
    file_prefix: Path | None
    project_ids: list[ProjectID] | None
    partial: bool


def _init_pagination(
    cursor: GenericCursor | None,
    *,
    filter_by_project_ids: list[ProjectID] | None,
    filter_by_file_prefix: Path | None,
    is_partial_prefix: bool,
) -> _PathsCursorParameters:
    if cursor:
        return _PathsCursorParameters.model_validate_json(cursor)
    return _PathsCursorParameters(
        offset=0,
        file_prefix=filter_by_file_prefix,
        project_ids=filter_by_project_ids,
        partial=is_partial_prefix,
    )


def _create_next_cursor(
    total_count: TotalChildren, limit: int, cursor_params: _PathsCursorParameters
) -> GenericCursor | None:
    if cursor_params.offset + limit < total_count:
        return cursor_params.model_copy(
            update={"offset": cursor_params.offset + limit}
        ).model_dump_json()
    return None


def _list_filter_with_partial_file_id_stmt(
    *,
    user_or_project_filter: UserOrProjectFilter,
    file_id_prefix: str | None,
    partial_file_id: str | None,
    sha256_checksum: SHA256Str | None,
    is_directory: bool | None,
    limit: int | None = None,
    offset: int | None = None,
):
    conditions: list = []

    # Checks access rights (project can be owned or shared)
    user_id = user_or_project_filter.user_id
    if user_id is not None:
        project_ids = user_or_project_filter.project_ids
        conditions.append(
            sa.or_(
                file_meta_data.c.user_id == f"{user_id}",
                (
                    file_meta_data.c.project_id.in_(f"{_}" for _ in project_ids)
                    if project_ids
                    else False
                ),
            )
        )

    # Optional filters
    if file_id_prefix:
        conditions.append(file_meta_data.c.file_id.startswith(file_id_prefix))
    if partial_file_id:
        conditions.append(file_meta_data.c.file_id.ilike(f"%{partial_file_id}%"))
    if is_directory is not None:
        conditions.append(file_meta_data.c.is_directory.is_(is_directory))
    if sha256_checksum:
        conditions.append(file_meta_data.c.sha256_checksum == sha256_checksum)

    return (
        sa.select(file_meta_data)
        .where(sa.and_(*conditions))
        .order_by(file_meta_data.c.created_at.asc())  # sorted as oldest first
        .offset(offset)
        .limit(limit)
    )


class FileMetaDataRepository(BaseRepository):
    async def exists(
        self, *, connection: AsyncConnection | None = None, file_id: SimcoreS3FileID
    ) -> bool:
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            return bool(
                await conn.scalar(
                    sa.select(sa.func.count())
                    .select_from(file_meta_data)
                    .where(file_meta_data.c.file_id == file_id)
                )
                == 1
            )

    async def upsert(
        self,
        *,
        connection: AsyncConnection | None = None,
        fmd: FileMetaData | FileMetaDataAtDB,
    ) -> FileMetaDataAtDB:
        # NOTE: upsert file_meta_data, if the file already exists, we update the whole row
        # so we get the correct time stamps
        fmd_db = (
            FileMetaDataAtDB.model_validate(fmd)
            if isinstance(fmd, FileMetaData)
            else fmd
        )
        insert_statement = pg_insert(file_meta_data).values(**fmd_db.model_dump())
        on_update_statement = insert_statement.on_conflict_do_update(
            index_elements=[file_meta_data.c.file_id], set_=fmd_db.model_dump()
        ).returning(literal_column("*"))
        async with transaction_context(self.db_engine, connection) as conn:
            result = await conn.execute(on_update_statement)
            row = result.one()
        return FileMetaDataAtDB.model_validate(row)

    async def insert(
        self, *, connection: AsyncConnection | None = None, fmd: FileMetaData
    ) -> FileMetaDataAtDB:
        fmd_db = FileMetaDataAtDB.model_validate(fmd)
        async with transaction_context(self.db_engine, connection) as conn:
            result = await conn.execute(
                file_meta_data.insert()
                .values(jsonable_encoder(fmd_db))
                .returning(literal_column("*"))
            )
            row = result.one()
        return FileMetaDataAtDB.model_validate(row)

    async def get(
        self, *, connection: AsyncConnection | None = None, file_id: SimcoreS3FileID
    ) -> FileMetaDataAtDB:
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            result = await conn.execute(
                sa.select(file_meta_data).where(file_meta_data.c.file_id == file_id)
            )
        if row := result.one_or_none():
            return FileMetaDataAtDB.model_validate(row)
        raise FileMetaDataNotFoundError(file_id=file_id)

    async def list_filter_with_partial_file_id(
        self,
        *,
        connection: AsyncConnection | None = None,
        user_or_project_filter: UserOrProjectFilter,
        file_id_prefix: str | None,
        partial_file_id: str | None,
        sha256_checksum: SHA256Str | None,
        is_directory: bool | None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[FileMetaDataAtDB]:
        stmt = _list_filter_with_partial_file_id_stmt(
            user_or_project_filter=user_or_project_filter,
            file_id_prefix=file_id_prefix,
            partial_file_id=partial_file_id,
            sha256_checksum=sha256_checksum,
            is_directory=is_directory,
            limit=limit,
            offset=offset,
        )
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            return [
                FileMetaDataAtDB.model_validate(row)
                async for row in await conn.stream(stmt)
            ]

    async def try_get_directory(
        self, *, connection: AsyncConnection | None = None, file_filter: Path
    ) -> FileMetaData | None:
        """Check if the given file filter is a directory or is inside a directory."""
        # we might be exactly on a directory or inside it
        potential_directories = (file_filter, *file_filter.parents)
        with contextlib.suppress(MultipleResultsFound):
            async with pass_or_acquire_connection(self.db_engine, connection) as conn:
                for file_id in potential_directories:
                    # there should be only 1 entry if this is a directory
                    result = await conn.execute(
                        sa.select(file_meta_data).where(
                            file_meta_data.c.file_id == f"{file_id}"
                        )
                    )
                    if row := result.one_or_none():
                        fmd = FileMetaDataAtDB.model_validate(row)
                        if fmd.is_directory:
                            return FileMetaData.from_db_model(fmd)
                        return None
        return None

    async def list_child_paths(
        self,
        *,
        connection: AsyncConnection | None = None,
        filter_by_project_ids: list[ProjectID] | None,
        filter_by_file_prefix: Path | None,
        cursor: GenericCursor | None,
        limit: int,
        is_partial_prefix: bool,
    ) -> tuple[list[PathMetaData], GenericCursor | None, TotalChildren]:
        """returns a list of FileMetaDataAtDB that are one level deep.
        e.g. when no filter is used, these are top level objects
        """

        cursor_params = _init_pagination(
            cursor,
            filter_by_project_ids=filter_by_project_ids,
            filter_by_file_prefix=filter_by_file_prefix,
            is_partial_prefix=is_partial_prefix,
        )

        if cursor_params.file_prefix:
            prefix_levels = len(cursor_params.file_prefix.parts) - 1
            search_prefix = (
                f"{cursor_params.file_prefix}%"
                if cursor_params.partial
                else f"{cursor_params.file_prefix / '%'}"
            )
            search_regex = rf"^[^/]+(?:/[^/]+){{{prefix_levels}}}{'' if cursor_params.partial else '/[^/]+'}"
            ranked_files = (
                sa.select(
                    file_meta_data.c.file_id,
                    sa.func.substring(file_meta_data.c.file_id, search_regex).label(
                        "path"
                    ),
                    sa.func.row_number()
                    .over(
                        partition_by=sa.func.substring(
                            file_meta_data.c.file_id, search_regex
                        ),
                        order_by=(file_meta_data.c.file_id.asc(),),
                    )
                    .label("row_num"),
                )
                .where(
                    and_(
                        file_meta_data.c.file_id.like(search_prefix),
                        (
                            file_meta_data.c.project_id.in_(
                                [f"{_}" for _ in cursor_params.project_ids]
                            )
                            if cursor_params.project_ids
                            else True
                        ),
                    )
                )
                .cte("ranked_files")
            )
        else:
            ranked_files = (
                sa.select(
                    file_meta_data.c.file_id,
                    sa.func.split_part(file_meta_data.c.file_id, "/", 1).label("path"),
                    sa.func.row_number()
                    .over(
                        partition_by=sa.func.split_part(
                            file_meta_data.c.file_id, "/", 1
                        ),
                        order_by=(file_meta_data.c.file_id.asc(),),
                    )
                    .label("row_num"),
                )
                .where(
                    file_meta_data.c.project_id.in_(
                        [f"{_}" for _ in cursor_params.project_ids]
                    )
                    if cursor_params.project_ids
                    else True
                )
                .cte("ranked_files")
            )

        files_query = (
            (
                sa.select(ranked_files, file_meta_data)
                .where(
                    and_(
                        ranked_files.c.row_num == 1,
                        ranked_files.c.file_id == file_meta_data.c.file_id,
                    )
                )
                .order_by(file_meta_data.c.file_id.asc())
            )
            .limit(limit)
            .offset(cursor_params.offset)
        )
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            total_count = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(ranked_files)
                .where(ranked_files.c.row_num == 1)
            )

            items = [
                PathMetaData(
                    path=row.path
                    or row.file_id,  # NOTE: if path_prefix is partial then path is None
                    display_path=row.path or row.file_id,
                    location_id=row.location_id,
                    location=row.location,
                    bucket_name=row.bucket_name,
                    project_id=row.project_id,
                    node_id=row.node_id,
                    user_id=row.user_id,
                    created_at=row.created_at,
                    last_modified=row.last_modified,
                    file_meta_data=(
                        FileMetaData.from_db_model(FileMetaDataAtDB.model_validate(row))
                        if row.file_id == row.path and not row.is_directory
                        else None
                    ),
                )
                async for row in await conn.stream(files_query)
            ]

        return (
            items,
            _create_next_cursor(total_count, limit, cursor_params),
            total_count,
        )

    async def list_fmds(
        self,
        *,
        connection: AsyncConnection | None = None,
        user_id: UserID | None = None,
        project_ids: list[ProjectID] | None = None,
        file_ids: list[SimcoreS3FileID] | None = None,
        expired_after: datetime.datetime | None = None,
    ) -> list[FileMetaDataAtDB]:
        stmt = sa.select(file_meta_data).where(
            and_(
                (file_meta_data.c.user_id == f"{user_id}") if user_id else True,
                (
                    (file_meta_data.c.project_id.in_([f"{p}" for p in project_ids]))
                    if project_ids
                    else True
                ),
                (file_meta_data.c.file_id.in_(file_ids)) if file_ids else True,
                (
                    (file_meta_data.c.upload_expires_at < expired_after)
                    if expired_after
                    else True
                ),
            )
        )
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            return [
                FileMetaDataAtDB.model_validate(row)
                async for row in await conn.stream(stmt)
            ]

    async def total(self, *, connection: AsyncConnection | None = None) -> int:
        """returns the number of uploaded file entries"""
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            return (
                await conn.scalar(
                    sa.select(sa.func.count()).select_from(file_meta_data)
                )
                or 0
            )

    async def list_valid_uploads(
        self,
        *,
        connection: AsyncConnection | None = None,
    ) -> AsyncGenerator[FileMetaDataAtDB, None]:
        """returns all the theoretically valid fmds (e.g. upload_expires_at column is null)"""
        async with pass_or_acquire_connection(self.db_engine, connection) as conn:
            async for row in await conn.stream(
                sa.select(file_meta_data).where(
                    file_meta_data.c.upload_expires_at.is_(
                        None
                    )  # lgtm [py/test-equals-none]
                )
            ):
                fmd_at_db = FileMetaDataAtDB.model_validate(row)
                yield fmd_at_db

    async def delete(
        self,
        *,
        connection: AsyncConnection | None = None,
        file_ids: list[SimcoreS3FileID],
    ) -> None:
        async with transaction_context(self.db_engine, connection) as conn:
            await conn.execute(
                file_meta_data.delete().where(file_meta_data.c.file_id.in_(file_ids))
            )

    async def delete_all_from_project(
        self, *, connection: AsyncConnection | None = None, project_id: ProjectID
    ) -> None:
        async with transaction_context(self.db_engine, connection) as conn:
            await conn.execute(
                file_meta_data.delete().where(
                    file_meta_data.c.project_id == f"{project_id}"
                )
            )

    async def delete_all_from_node(
        self, *, connection: AsyncConnection | None = None, node_id: NodeID
    ) -> None:
        async with transaction_context(self.db_engine, connection) as conn:
            await conn.execute(
                file_meta_data.delete().where(file_meta_data.c.node_id == f"{node_id}")
            )
