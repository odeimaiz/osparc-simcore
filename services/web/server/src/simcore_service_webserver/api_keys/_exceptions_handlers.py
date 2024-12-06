from servicelib.aiohttp import status
from simcore_service_webserver.api_keys.errors import ApiKeyNotFoundError

from ..exception_handling import (
    ExceptionToHttpErrorMap,
    HttpErrorInfo,
    exception_handling_decorator,
    to_exceptions_handlers_map,
)

_TO_HTTP_ERROR_MAP: ExceptionToHttpErrorMap = {
    ApiKeyNotFoundError: HttpErrorInfo(
        status.HTTP_404_NOT_FOUND,
        "API key was not found",
    ),
}


handle_plugin_requests_exceptions = exception_handling_decorator(
    to_exceptions_handlers_map(_TO_HTTP_ERROR_MAP)
)
# this is one decorator with a single exception handler