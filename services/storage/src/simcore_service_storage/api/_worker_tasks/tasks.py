import logging

from celery import Celery  # type: ignore[import-untyped]
from servicelib.logging_utils import log_context

from ...modules.celery._celery_types import register_celery_types
from ...modules.celery._task import define_task
from ...modules.celery.tasks import export_data
from ._files import complete_upload_file
from ._paths import compute_path_size, delete_paths
from ._simcore_s3 import deep_copy_files_from_project

_logger = logging.getLogger(__name__)


def setup_worker_tasks(app: Celery) -> None:
    register_celery_types()
    with log_context(
        _logger,
        logging.INFO,
        msg="Storage setup Worker Tasks",
    ):
        define_task(app, export_data)
        define_task(app, compute_path_size)
        define_task(app, delete_paths)
        define_task(app, complete_upload_file)
        define_task(app, deep_copy_files_from_project)
