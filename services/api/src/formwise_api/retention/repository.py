"""Firestore persistence for retention lifecycle metadata and purge jobs."""

from collections.abc import Mapping
from typing import Any, Protocol

from firebase_admin import firestore
from formwise_document_core.retention_models import (
    PurgeJobStatus,
    RetentionJob,
    RetentionState,
)


class RetentionStateRepository(Protocol):
    def save(self, state: RetentionState) -> None: ...
    def get(self, conversation_id: str) -> RetentionState | None: ...
    def update(
        self,
        conversation_id: str,
        updates: Mapping[str, Any],
    ) -> RetentionState | None: ...
    def delete(self, conversation_id: str) -> None: ...


class RetentionJobRepository(Protocol):
    def enqueue(self, job: RetentionJob) -> None: ...
    def get(self, job_id: str) -> RetentionJob | None: ...
    def list_pending(self) -> list[RetentionJob]: ...
    def mark_processing(self, job_id: str, retry_count: int) -> RetentionJob | None: ...
    def mark_completed(self, job_id: str, retry_count: int) -> RetentionJob | None: ...
    def mark_failed(self, job_id: str, retry_count: int) -> RetentionJob | None: ...
    def delete(self, job_id: str) -> None: ...


class RetainedConversationSelector(Protocol):
    def retained_count(self, user_id: str) -> int: ...
    def oldest_retained_conversation_id(self, user_id: str) -> str | None: ...


class FirestoreRetentionStateRepository:
    """Stores retention state alongside its owning conversation."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def save(self, state: RetentionState) -> None:
        self._client.collection("conversations").document(state.conversation_id).set(
            {"retentionState": state.model_dump(by_alias=True, mode="python")},
            merge=True,
        )

    def get(self, conversation_id: str) -> RetentionState | None:
        snapshot = self._client.collection("conversations").document(conversation_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        state = data.get("retentionState")
        return RetentionState.model_validate(state) if isinstance(state, dict) else None

    def update(
        self,
        conversation_id: str,
        updates: Mapping[str, Any],
    ) -> RetentionState | None:
        current = self.get(conversation_id)
        if current is None:
            return None
        data = current.model_dump(by_alias=True, mode="python")
        data.update(
            {
                key: value
                for key, value in updates.items()
                if key
                in {
                    "state",
                    "revokedAt",
                    "queuedAt",
                    "startedAt",
                    "completedAt",
                    "failureCount",
                    "lastFailureAt",
                }
            }
        )
        data["conversationId"] = conversation_id
        state = RetentionState.model_validate(data)
        self.save(state)
        return state

    def delete(self, conversation_id: str) -> None:
        self._client.collection("conversations").document(conversation_id).update(
            {"retentionState": firestore.DELETE_FIELD}
        )


class FirestoreRetentionJobRepository:
    """Persists identifier-only retention jobs for worker execution."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def enqueue(self, job: RetentionJob) -> None:
        self._client.collection("retention_jobs").document(job.job_id).create(
            job.model_dump(by_alias=True, mode="python")
        )

    def get(self, job_id: str) -> RetentionJob | None:
        snapshot = self._client.collection("retention_jobs").document(job_id).get()
        return RetentionJob.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def list_pending(self) -> list[RetentionJob]:
        query = (
            self._client.collection("retention_jobs")
            .where("status", "==", "queued")
            .order_by("createdAt")
        )
        return [RetentionJob.model_validate(snapshot.to_dict() or {}) for snapshot in query.stream()]

    def mark_processing(self, job_id: str, retry_count: int) -> RetentionJob | None:
        return self._mark(job_id, "processing", retry_count)

    def mark_completed(self, job_id: str, retry_count: int) -> RetentionJob | None:
        return self._mark(job_id, "completed", retry_count)

    def mark_failed(self, job_id: str, retry_count: int) -> RetentionJob | None:
        return self._mark(job_id, "failed", retry_count)

    def delete(self, job_id: str) -> None:
        self._client.collection("retention_jobs").document(job_id).delete()

    def _mark(
        self,
        job_id: str,
        status: PurgeJobStatus,
        retry_count: int,
    ) -> RetentionJob | None:
        current = self.get(job_id)
        if current is None:
            return None
        data = current.model_dump(by_alias=True, mode="python")
        data.update({"status": status, "retryCount": retry_count})
        job = RetentionJob.model_validate(data)
        self._client.collection("retention_jobs").document(job_id).set(
            job.model_dump(by_alias=True, mode="python")
        )
        return job


class FirestoreRetainedConversationSelector:
    """Finds, but never changes, the oldest currently retained conversation."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def retained_count(self, user_id: str) -> int:
        return sum(1 for _ in self._retained_query(user_id).stream())

    def _retained_query(self, user_id: str) -> Any:
        return (
            self._client.collection("conversations")
            .where("userId", "==", user_id)
            .where("status", "in", ["ready", "in_progress", "ready_to_render"])
        )

    def oldest_retained_conversation_id(self, user_id: str) -> str | None:
        query = (
            self._retained_query(user_id)
            .order_by("createdAt")
            .order_by("__name__")
            .limit(1)
        )
        snapshot = next(iter(query.stream()), None)
        if snapshot is None:
            return None
        data = snapshot.to_dict() or {}
        conversation_id = data.get("id")
        return conversation_id if isinstance(conversation_id, str) else snapshot.id
