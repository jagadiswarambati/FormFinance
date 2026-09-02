"""Provider-neutral worker reliability and PII-safe operational primitives."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar
from uuid import uuid4

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

T = TypeVar("T")


class WorkerOperationTimeout(TimeoutError):
    """Raised when a bounded worker operation does not finish in time."""


def run_with_timeout(operation: Callable[[], T], timeout_seconds: float) -> T:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(operation)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as error:
        future.cancel()
        raise WorkerOperationTimeout("WORKER_OPERATION_TIMEOUT") from error
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def retry_at(attempt: int, base_seconds: float, maximum_seconds: float) -> datetime:
    delay = min(base_seconds * (2 ** max(attempt - 1, 0)), maximum_seconds)
    return datetime.now(UTC) + timedelta(seconds=delay)


@firestore.transactional  # type: ignore[untyped-decorator]
def _claim_job(
    transaction: Any,
    reference: Any,
    now: datetime,
) -> dict[str, Any] | None:
    snapshot = reference.get(transaction=transaction)
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    next_attempt_at = data.get("nextAttemptAt")
    if data.get("status") != "queued" or (
        isinstance(next_attempt_at, datetime) and next_attempt_at > now
    ):
        return None
    data.update(
        {
            "status": "processing",
            "attempt": int(data.get("attempt", 0)) + 1,
            "startedAt": now,
        }
    )
    transaction.set(reference, data)
    return data


def claim_next_queued_job(client: Any, collection: str) -> tuple[str, dict[str, Any]] | None:
    now = datetime.now(UTC)
    candidates = (
        client.collection(collection)
        .where(filter=FieldFilter("status", "==", "queued"))
        .order_by("createdAt")
        .limit(20)
        .stream()
    )
    for snapshot in candidates:
        data = _claim_job(client.transaction(), snapshot.reference, now)
        if data is not None:
            return snapshot.id, data
    return None


class FirestoreOperationalReporter:
    """Stores only non-content worker health, queue depth, and terminal failures."""

    def __init__(self, client: Any, worker_id: str) -> None:
        self._client = client
        self._worker_id = worker_id

    def queue_depths(self) -> dict[str, int]:
        return {
            "ocr": self._queue_depth("ocr_jobs"),
            "render": self._queue_depth("render_jobs"),
            "retention": self._queue_depth("retention_jobs"),
        }

    def heartbeat(self, *, active_jobs: int, last_error_code: str | None = None) -> None:
        self._client.collection("worker_health").document(self._worker_id).set(
            {
                "workerId": self._worker_id,
                "status": "healthy",
                "updatedAt": datetime.now(UTC),
                "activeJobs": active_jobs,
                "queueDepths": self.queue_depths(),
                "lastErrorCode": last_error_code,
            }
        )

    def dead_letter(
        self,
        *,
        queue: str,
        job_id: str,
        attempt: int,
        error_code: str,
        request_id: str | None,
    ) -> None:
        self._client.collection("dead_letter_jobs").document(uuid4().hex).create(
            {
                "queue": queue,
                "jobId": job_id,
                "attempt": attempt,
                "errorCode": error_code,
                "requestId": request_id,
                "createdAt": datetime.now(UTC),
            }
        )

    def _queue_depth(self, collection: str) -> int:
        return sum(
            1
            for _ in self._client.collection(collection)
            .where(filter=FieldFilter("status", "==", "queued"))
            .stream()
        )
