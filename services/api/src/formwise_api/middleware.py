"""Request-context and response-security middleware for the API boundary."""

from uuid import UUID, uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from formwise_api.config import Settings


def _request_id(candidate: str | None) -> str:
    if candidate is not None:
        try:
            return str(UUID(candidate))
        except ValueError:
            pass
    return str(uuid4())


class ApiSecurityMiddleware(BaseHTTPMiddleware):
    """Adds a trusted request ID and security headers without inspecting content."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = _request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if request.url.path not in {"/docs", "/redoc", "/openapi.json"}:
            response.headers["Content-Security-Policy"] = self._settings.security_content_security_policy
        if self._settings.security_hsts_max_age_seconds > 0:
            hsts = f"max-age={self._settings.security_hsts_max_age_seconds}"
            if self._settings.security_hsts_include_subdomains:
                hsts += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts
        return response
