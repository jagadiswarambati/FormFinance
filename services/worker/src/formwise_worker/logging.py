"""PII-safe structured logging for worker operational events."""

import logging

import structlog
from structlog.types import EventDict, WrappedLogger

_ALLOWED_LOG_KEYS = {
    "event",
    "level",
    "timestamp",
    "request_id",
    "worker_id",
    "queue",
    "job_id",
    "render_id",
    "conversation_id",
    "document_id",
    "status",
    "error_code",
    "error_type",
    "retry_count",
    "active_jobs",
    "queue_depths",
    "duration_ms",
}


def _allowlisted_event(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    return {key: value for key, value in event_dict.items() if key in _ALLOWED_LOG_KEYS}


def configure_logging(log_level: str) -> None:
    """Configure JSON logs which retain only operational metadata."""
    logging.basicConfig(level=log_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _allowlisted_event,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
    )
