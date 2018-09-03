import logging

from .celery import app


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG) # FIXME: set level via config

@app.task(name='comp.task', bind=True)
def pipeline(self, pipeline_id, node_id=None):
    from .core import SIDECAR

    _LOGGER.debug("ENTERING run")
    next_task_nodes = []
    try:
        next_task_nodes = SIDECAR.inspect(self, pipeline_id, node_id)
    #pylint:disable=broad-except
    except Exception:
        _LOGGER.exception("Uncaught exception")

    for _node_id in next_task_nodes:
        _task = app.send_task('comp.task', args=(pipeline_id, _node_id), kwargs={})
