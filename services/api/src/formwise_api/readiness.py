"""PII-safe dependency readiness checks for the API process."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from formwise_api.ai_provider.factory import get_ai_provider
from formwise_api.authentication.firebase import get_firestore_client
from formwise_api.config import Settings

logger = structlog.get_logger()


async def readiness_report(settings: Settings) -> tuple[bool, dict[str, object]]:
    """Return an aggregate readiness result without exposing dependency diagnostics."""
    firestore_ready, client = _firestore_ready()
    checks: dict[str, bool | str] = {
        "firestore": firestore_ready,
        "storage": _storage_ready(settings),
        "provider": await _provider_ready(settings),
        "queues": _queues_ready(client) if firestore_ready else False,
    }
    checks["worker"] = _worker_ready(client, settings) if firestore_ready else False
    required = [
        value
        for name, value in checks.items()
        if name != "worker" or settings.readiness_require_worker_heartbeat
    ]
    ready = all(value is True for value in required)
    return ready, {"status": "ready" if ready else "not_ready", "dependencies": checks}


def _firestore_ready() -> tuple[bool, Any | None]:
    try:
        client = get_firestore_client()
        next(iter(client.collection("worker_health").limit(1).stream()), None)
        return True, client
    except Exception as error:
        logger.exception(
            "readiness_dependency_failed",
            dependency="firestore",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return False, None


def _storage_ready(settings: Settings) -> bool:
    return all(
        Path(path).is_dir()
        for path in (
            settings.local_storage_path,
            settings.quarantine_storage_path,
            settings.render_output_storage_path,
        )
    )


async def _provider_ready(settings: Settings) -> bool:
    try:
        return await get_ai_provider(settings).health_check()
    except Exception as error:
        logger.exception(
            "readiness_dependency_failed",
            dependency="ai_provider",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return False


def _queues_ready(client: Any) -> bool:
    try:
        for collection in ("ocr_jobs", "render_jobs", "retention_jobs"):
            next(iter(client.collection(collection).limit(1).stream()), None)
        return True
    except Exception as error:
        logger.exception(
            "readiness_dependency_failed",
            dependency="firestore_queue",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return False


def _worker_ready(client: Any, settings: Settings) -> bool:
    if not settings.readiness_require_worker_heartbeat:
        return True
    try:
        snapshot = next(
            iter(
                client.collection("worker_health")
                .order_by("updatedAt", direction="DESCENDING")
                .limit(1)
                .stream()
            ),
            None,
        )
        if snapshot is None:
            return False
        updated_at = (snapshot.to_dict() or {}).get("updatedAt")
        if not isinstance(updated_at, datetime):
            return False
        age = (datetime.now(UTC) - updated_at).total_seconds()
        return 0 <= age <= settings.readiness_worker_heartbeat_max_age_seconds
    except Exception as error:
        logger.exception(
            "readiness_dependency_failed",
            dependency="firestore_worker_heartbeat",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return False
