"""Production-safe, stable API error responses."""

import re
from typing import Final

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger()

_STATUS_CODES: Final[dict[int, str]] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "AUTHENTICATION_REQUIRED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "RESOURCE_NOT_FOUND",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "PAYLOAD_TOO_LARGE",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_FAILED",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
}
_MESSAGES: Final[dict[str, str]] = {
    "BAD_REQUEST": "The request could not be processed.",
    "AUTHENTICATION_REQUIRED": "Authentication is required.",
    "FORBIDDEN": "You are not permitted to perform this action.",
    "RESOURCE_NOT_FOUND": "The requested resource was not found.",
    "CONFLICT": "The request conflicts with the current resource state.",
    "PAYLOAD_TOO_LARGE": "The request payload exceeds the permitted size.",
    "VALIDATION_FAILED": "The request could not be validated.",
    "RATE_LIMITED": "Too many requests. Please try again later.",
    "SERVICE_UNAVAILABLE": "The service is temporarily unavailable.",
    "INTERNAL_ERROR": "An unexpected error occurred.",
    "POLICY_BLOCKED": "This action is blocked by the privacy policy.",
    "RENDER_NOT_COMPLETED": "The rendered document is not ready yet.",
    "RENDER_OUTPUT_UNAVAILABLE": "The rendered output is unavailable.",
    "RENDER_ARTIFACT_UNAVAILABLE": "The rendered artifact is unavailable.",
}
_EXPLICIT_CODE = re.compile(r"^([A-Z][A-Z0-9_]+)(?::|$)")


def _request_id(request: Request) -> str | None:
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) else None


def _code_for(status_code: int, detail: object) -> str:
    if isinstance(detail, str):
        match = _EXPLICIT_CODE.match(detail)
        if match is not None:
            return match.group(1)
    return _STATUS_CODES.get(status_code, "REQUEST_REJECTED")


def _response(status_code: int, code: str, request_id: str | None) -> JSONResponse:
    message = _MESSAGES.get(code, _MESSAGES.get(_STATUS_CODES.get(status_code, ""), _MESSAGES["BAD_REQUEST"]))
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message,
            "code": code,
            "requestId": request_id,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    async def handle_http_exception(
        request: Request,
        exception: Exception,
    ) -> JSONResponse:
        assert isinstance(exception, StarletteHTTPException)
        code = _code_for(exception.status_code, exception.detail)
        logger.info(
            "api_request_rejected",
            status_code=exception.status_code,
            error_code=code,
        )
        response = _response(exception.status_code, code, _request_id(request))
        if exception.headers:
            response.headers.update(exception.headers)
        return response

    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(HTTPException, handle_http_exception)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        _: RequestValidationError,
    ) -> JSONResponse:
        logger.info("api_request_validation_failed", status_code=422, error_code="VALIDATION_FAILED")
        return _response(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_FAILED", _request_id(request))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.error(
            "api_request_failed",
            status_code=500,
            error_code="INTERNAL_ERROR",
            error_type=type(exception).__name__,
        )
        return _response(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", _request_id(request))
