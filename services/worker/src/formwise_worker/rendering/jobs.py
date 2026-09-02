from datetime import UTC, datetime
from typing import Any

from formwise_worker.operations import claim_next_queued_job


class FirestoreRenderJobRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def claim_next(self) -> dict[str, Any] | None:
        claimed = claim_next_queued_job(self._client, "render_jobs")
        if claimed is None:
            return None
        job_id, data = claimed
        data["id"] = job_id
        return data

    def update(self, job_id: str, status: str, **details: Any) -> None:
        self._client.collection("render_jobs").document(job_id).update(
            {"status": status, **details}
        )

    def enqueue(self, render_id: str, document_id: str, owner_uid: str) -> None:
        self._client.collection("render_jobs").document(render_id).create(
            {
                "renderId": render_id,
                "documentId": document_id,
                "ownerUid": owner_uid,
                "status": "queued",
                "attempt": 0,
                "createdAt": datetime.now(UTC),
                "startedAt": None,
                "completedAt": None,
                "errorCode": None,
                "nextAttemptAt": None,
            }
        )
