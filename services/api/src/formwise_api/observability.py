"""Small provider-neutral helpers for propagating request correlation metadata."""

import structlog


def current_request_id() -> str | None:
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    return request_id if isinstance(request_id, str) else None
