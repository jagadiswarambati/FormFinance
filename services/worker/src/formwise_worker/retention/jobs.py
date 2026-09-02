"""Worker-side Firestore adapter for identifier-only retention jobs."""

from datetime import UTC, datetime
from typing import Any

from firebase_admin import firestore
from formwise_document_core.retention_models import RetentionJob
from google.cloud.firestore_v1.base_query import FieldFilter


@firestore.transactional  # type: ignore[untyped-decorator]
def _claim_queued_job(
    transaction: Any,
    reference: Any,
    now: datetime,
) -> dict[str, Any] | None:
    snapshot = reference.get(transaction=transaction)
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    if data.get("status") != "queued":
        return None
    next_attempt_at = data.get("nextAttemptAt")
    if next_attempt_at is not None and next_attempt_at > now:
        return None
    data["status"] = "processing"
    transaction.set(reference, data)
    return data


class FirestoreRetentionJobRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def next_queued(self) -> RetentionJob | None:
        query = (
            self._client.collection("retention_jobs")
            .where(filter=FieldFilter("status", "==", "queued"))
            .order_by("createdAt")
            .limit(1)
        )
        now = datetime.now(UTC)
        for snapshot in query.stream():
            job = RetentionJob.model_validate(snapshot.to_dict() or {})
            if job.next_attempt_at is None or job.next_attempt_at <= now:
                return job
        return None

    def mark_processing(self, job: RetentionJob) -> RetentionJob | None:
        reference = self._client.collection("retention_jobs").document(job.job_id)
        data = _claim_queued_job(
            self._client.transaction(), reference, datetime.now(UTC)
        )
        if data is None:
            return None
        updated = RetentionJob.model_validate(data)
        conversation = self._client.collection("conversations").document(job.conversation_id)
        if conversation.get().exists:
            conversation.update(
                {
                    "retentionState.state": "processing",
                    "retentionState.startedAt": datetime.now(UTC),
                }
            )
        return updated

    def mark_completed(self, job: RetentionJob) -> RetentionJob | None:
        return self._update_job(job, "completed", job.retry_count, "completed")

    def requeue_after_failure(
        self,
        job: RetentionJob,
        retry_count: int,
        next_attempt_at: datetime,
    ) -> RetentionJob | None:
        return self._update_job(
            job,
            "queued",
            retry_count,
            "queued",
            failed=True,
            next_attempt_at=next_attempt_at,
        )

    def mark_failed(self, job: RetentionJob, retry_count: int) -> RetentionJob | None:
        return self._update_job(job, "failed", retry_count, "failed", failed=True)

    def _update_job(
        self,
        job: RetentionJob,
        status: str,
        retry_count: int,
        retention_state: str,
        *,
        failed: bool = False,
        next_attempt_at: datetime | None = None,
    ) -> RetentionJob | None:
        reference = self._client.collection("retention_jobs").document(job.job_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data.update(
            {
                "status": status,
                "retryCount": retry_count,
                "nextAttemptAt": next_attempt_at,
            }
        )
        updated = RetentionJob.model_validate(data)
        reference.set(updated.model_dump(by_alias=True, mode="python"))

        conversation = self._client.collection("conversations").document(job.conversation_id)
        conversation_snapshot = conversation.get()
        if conversation_snapshot.exists:
            now = datetime.now(UTC)
            state_updates: dict[str, Any] = {"retentionState.state": retention_state}
            if retention_state == "processing":
                state_updates["retentionState.startedAt"] = now
            elif retention_state == "completed":
                state_updates["retentionState.completedAt"] = now
            if failed:
                state_updates["retentionState.failureCount"] = retry_count
                state_updates["retentionState.lastFailureAt"] = now
            conversation.update(state_updates)
        return updated
