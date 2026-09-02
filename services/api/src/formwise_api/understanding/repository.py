from typing import Any, Protocol

from formwise_api.understanding.models import StructuredDocument


class UnderstandingRepository(Protocol):
    def save(self, document: StructuredDocument) -> None: ...
    def get(self, document_id: str) -> StructuredDocument | None: ...


class FirestoreUnderstandingRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def save(self, document: StructuredDocument) -> None:
        self._client.collection("structured_documents").document(document.document_id).set(document.model_dump(by_alias=True, mode="python"))

    def get(self, document_id: str) -> StructuredDocument | None:
        snapshot = self._client.collection("structured_documents").document(document_id).get()
        if not snapshot.exists:
            return None
        return StructuredDocument.model_validate(snapshot.to_dict() or {})
