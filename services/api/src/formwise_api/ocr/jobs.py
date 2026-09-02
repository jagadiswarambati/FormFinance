from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.observability import current_request_id


class OcrJobRepository(Protocol):
    def enqueue(self, document_id: str, owner_uid: str, provider: str) -> None: ...


class FirestoreOcrJobRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def enqueue(self, document_id: str, owner_uid: str, provider: str) -> None:
        self._client.collection("ocr_jobs").document(document_id).set(
            {
                "documentId": document_id,
                "ownerUid": owner_uid,
                "provider": provider,
                "status": "queued",
                "attempt": 0,
                "nextAttemptAt": None,
                "requestId": current_request_id(),
                "createdAt": datetime.now(UTC),
                "startedAt": None,
                "completedAt": None,
            }
        )
