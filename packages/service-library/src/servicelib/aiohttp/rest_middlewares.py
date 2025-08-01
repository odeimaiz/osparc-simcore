"""rest - middlewares for error, enveloping and validation

SEE  https://gist.github.com/amitripshtos/854da3f4217e3441e8fceea85b0cbd91
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import web
from aiohttp.web_exceptions import HTTPError
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse
from common_library.error_codes import ErrorCodeStr, create_error_code
from common_library.json_serialization import json_dumps, json_loads
from common_library.user_messages import user_message
from models_library.basic_types import IDStr
from models_library.rest_error import ErrorGet, ErrorItemType, LogMessageType
from servicelib.rest_constants import RESPONSE_MODEL_POLICY
from servicelib.status_codes_utils import is_5xx_server_error

from ..logging_errors import create_troubleshootting_log_kwargs
from ..mimetype_constants import MIMETYPE_APPLICATION_JSON
from ..rest_responses import is_enveloped_from_text
from ..status_codes_utils import get_code_description
from . import status
from .rest_responses import (
    create_data_response,
    create_http_error,
    safe_status_message,
    wrap_as_envelope,
)
from .typing_extension import Handler, Middleware
from .web_exceptions_extension import get_http_error_class_or_none

DEFAULT_API_VERSION = "v0"
_FMSG_INTERNAL_ERROR_USER_FRIENDLY = user_message(
    "We apologize for the inconvenience. "
    "The issue has been recorded, please report it if it persists.",
    _version=1,
)


_logger = logging.getLogger(__name__)


def is_api_request(request: web.Request, api_version: str) -> bool:
    base_path = "/" + api_version.lstrip("/")
    return bool(request.path.startswith(base_path))


def _create_error_context(
    request: web.BaseRequest, exception: Exception
) -> tuple[ErrorCodeStr, dict[str, Any]]:
    """Create error code and context for logging purposes.

    Returns:
        Tuple of (error_code, error_context)
    """
    error_code = create_error_code(exception)
    error_context: dict[str, Any] = {
        "request.remote": f"{request.remote}",
        "request.method": f"{request.method}",
        "request.path": f"{request.path}",
    }
    return error_code, error_context


def _log_5xx_server_error(
    request: web.BaseRequest, exception: Exception, user_error_msg: str
) -> ErrorCodeStr:
    """Log 5XX server errors with error code and context."""
    error_code, error_context = _create_error_context(request, exception)

    _logger.exception(
        **create_troubleshootting_log_kwargs(
            user_error_msg,
            error=exception,
            error_context=error_context,
            error_code=error_code,
        )
    )
    return error_code


def _handle_unexpected_exception_as_500(
    request: web.BaseRequest, exception: Exception
) -> web.HTTPInternalServerError:
    """Process unexpected exceptions and return them as HTTP errors with proper formatting.

    IMPORTANT: this function cannot throw exceptions, as it is called
    """
    error_code, error_context = _create_error_context(request, exception)
    user_error_msg = _FMSG_INTERNAL_ERROR_USER_FRIENDLY

    error_context["http_error"] = http_error = create_http_error(
        exception,
        user_error_msg,
        web.HTTPInternalServerError,
        error_code=error_code,
    )

    _log_5xx_server_error(request, exception, user_error_msg)

    return http_error


def handle_aiohttp_web_http_error(
    request: web.BaseRequest, exception: web.HTTPError
) -> web.HTTPError:
    """Handle standard HTTP errors by ensuring they're properly formatted.

    NOTE: this needs further refactoring to avoid code duplication
    """
    assert request  # nosec
    assert not exception.empty_body, "HTTPError should not have an empty body"  # nosec

    exception.content_type = MIMETYPE_APPLICATION_JSON
    if exception.reason:
        exception.set_status(
            exception.status, reason=safe_status_message(message=exception.reason)
        )

    if not exception.text or not is_enveloped_from_text(exception.text):
        # NOTE: aiohttp.HTTPException creates `text = f"{self.status}: {self.reason}"`
        user_error_msg = exception.text or "Unexpected error"

        error_code: IDStr | None = None
        if is_5xx_server_error(exception.status):
            error_code = IDStr(
                _log_5xx_server_error(request, exception, user_error_msg)
            )

        error_model = ErrorGet(
            errors=[
                ErrorItemType(
                    code=exception.__class__.__name__,
                    message=user_error_msg,
                    resource=None,
                    field=None,
                ),
            ],
            status=exception.status,
            logs=[
                LogMessageType(message=user_error_msg, level="ERROR"),
            ],
            message=user_error_msg,
            support_id=error_code,
        )
        exception.text = json_dumps(
            wrap_as_envelope(
                error=error_model.model_dump(mode="json", **RESPONSE_MODEL_POLICY)
            )
        )

    return exception


def _handle_aiohttp_web_http_successful(
    request: web.Request, exception: web.HTTPSuccessful
) -> web.HTTPSuccessful:
    """Handle successful HTTP responses, ensuring they're properly enveloped."""
    assert request  # nosec

    exception.content_type = MIMETYPE_APPLICATION_JSON
    if exception.reason:
        exception.set_status(
            exception.status, reason=safe_status_message(message=exception.reason)
        )

    if exception.text and not is_enveloped_from_text(exception.text):
        # Ensures that the response is enveloped
        data = json_loads(exception.text)
        exception.text = json_dumps({"data": data})

    return exception


def _handle_exception_as_http_error(
    request: web.Request,
    exception: NotImplementedError | TimeoutError,
    status_code: int,
) -> HTTPError:
    """
    Generic handler for exceptions that map to specific HTTP status codes.
    Converts the status code to the appropriate HTTP error class and creates a response.
    """
    assert request  # nosec

    http_error_cls = get_http_error_class_or_none(status_code)
    if http_error_cls is None:
        msg = (
            f"No HTTP error class found for status code {status_code}, falling back to 500",
        )
        raise ValueError(msg)

    user_error_msg = get_code_description(status_code)

    if is_5xx_server_error(status_code):
        _log_5xx_server_error(request, exception, user_error_msg)

    return create_http_error(exception, user_error_msg, http_error_cls)


def error_middleware_factory(api_version: str) -> Middleware:

    @web.middleware
    async def _middleware_handler(request: web.Request, handler: Handler):
        """
        Ensure all error raised are properly enveloped and json responses
        """
        if not is_api_request(request, api_version):
            return await handler(request)

        try:
            try:
                result = await handler(request)

            except web.HTTPError as exc:  # 4XX and 5XX raised as exceptions
                result = handle_aiohttp_web_http_error(request, exc)

            except web.HTTPSuccessful as exc:  # 2XX rased as exceptions
                result = _handle_aiohttp_web_http_successful(request, exc)

            except web.HTTPRedirection as exc:  # 3XX raised as exceptions
                result = exc

            except NotImplementedError as exc:
                result = _handle_exception_as_http_error(
                    request, exc, status.HTTP_501_NOT_IMPLEMENTED
                )

            except TimeoutError as exc:
                result = _handle_exception_as_http_error(
                    request, exc, status.HTTP_504_GATEWAY_TIMEOUT
                )

        except Exception as exc:  # pylint: disable=broad-except
            #
            # Last resort for unexpected exceptions (including those raise by the exception handlers!)
            #
            result = _handle_unexpected_exception_as_500(request, exc)

        return result

    # adds identifier (mostly for debugging)
    setattr(  # noqa: B010
        _middleware_handler, "__middleware_name__", f"{__name__}.error_{api_version}"
    )

    return _middleware_handler


_ResponseOrBodyData = StreamResponse | Any
HandlerFlexible = Callable[[Request], Awaitable[_ResponseOrBodyData]]
MiddlewareFlexible = Callable[[Request, HandlerFlexible], Awaitable[StreamResponse]]


def envelope_middleware_factory(
    api_version: str,
) -> Callable[..., Awaitable[StreamResponse]]:
    # FIXME: This data conversion is very error-prone. Use decorators instead!

    @web.middleware
    async def _middleware_handler(
        request: web.Request, handler: HandlerFlexible
    ) -> StreamResponse:
        """
        Ensures all responses are enveloped as {'data': .. , 'error', ...} in json
        ONLY for API-requests
        """
        if not is_api_request(request, api_version):
            resp = await handler(request)
            assert isinstance(resp, StreamResponse)  # nosec
            return resp

        # NOTE: the return values of this handler
        resp = await handler(request)

        if isinstance(resp, web.FileResponse):
            return resp

        if not isinstance(resp, StreamResponse):
            resp = create_data_response(data=resp)

        assert isinstance(resp, web.StreamResponse)  # nosec
        return resp

    # adds identifier (mostly for debugging)
    setattr(  # noqa: B010
        _middleware_handler, "__middleware_name__", f"{__name__}.envelope_{api_version}"
    )

    return _middleware_handler


def append_rest_middlewares(
    app: web.Application, api_version: str = DEFAULT_API_VERSION
):
    """Helper that appends rest-middlewares in the correct order"""
    app.middlewares.append(error_middleware_factory(api_version))
    app.middlewares.append(envelope_middleware_factory(api_version))
