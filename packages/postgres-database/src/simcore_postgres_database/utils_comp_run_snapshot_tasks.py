from typing import Any

import sqlalchemy as sa
from pydantic import PositiveInt
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from .models.comp_run_snapshot_tasks import comp_run_snapshot_tasks
from .utils_repos import pass_or_acquire_connection

COMP_RUN_SNAPSHOT_TASKS_DB_COLS = (
    comp_run_snapshot_tasks.c.snapshot_task_id,
    comp_run_snapshot_tasks.c.run_id,
    comp_run_snapshot_tasks.c.project_id,
    comp_run_snapshot_tasks.c.node_id,
    comp_run_snapshot_tasks.c.node_class,
    comp_run_snapshot_tasks.c.job_id,
    comp_run_snapshot_tasks.c.internal_id,
    comp_run_snapshot_tasks.c.schema,
    comp_run_snapshot_tasks.c.inputs,
    comp_run_snapshot_tasks.c.outputs,
    comp_run_snapshot_tasks.c.run_hash,
    comp_run_snapshot_tasks.c.image,
    comp_run_snapshot_tasks.c.state,
    comp_run_snapshot_tasks.c.errors,
    comp_run_snapshot_tasks.c.progress,
    comp_run_snapshot_tasks.c.start,
    comp_run_snapshot_tasks.c.end,
    comp_run_snapshot_tasks.c.last_heartbeat,
    comp_run_snapshot_tasks.c.created,
    comp_run_snapshot_tasks.c.modified,
    comp_run_snapshot_tasks.c.pricing_info,
    comp_run_snapshot_tasks.c.hardware_info,
)


async def update_for_run_id_and_node_id(
    engine: AsyncEngine,
    conn: AsyncConnection | None = None,
    *,
    run_id: PositiveInt,
    node_id: str,
    data: dict[str, Any],
) -> Row:
    async with pass_or_acquire_connection(engine, connection=conn) as _conn:
        result = await _conn.execute(
            comp_run_snapshot_tasks.update()
            .values(
                **data,
                modified=sa.func.now(),
            )
            .where(
                (comp_run_snapshot_tasks.c.run_id == run_id)
                & (comp_run_snapshot_tasks.c.node_id == node_id)
            )
            .returning(*COMP_RUN_SNAPSHOT_TASKS_DB_COLS)
        )
        row = result.one_or_none()
        if row is None:
            msg = f"update for run_id={run_id} and node_id={node_id} did not return any row"
            raise ValueError(msg)
        return row
