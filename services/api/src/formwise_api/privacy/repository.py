from typing import Any, Protocol


class PrivacyReportRepository(Protocol):
    def save(self, document_id: str, report: dict[str, Any]) -> None: ...
    def get(self, document_id: str) -> dict[str, Any] | None: ...


class FirestorePrivacyReportRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def save(self, document_id: str, report: dict[str, Any]) -> None:
        self._client.collection("privacy_reports").document(document_id).set(report)

    def get(self, document_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection("privacy_reports").document(document_id).get()
        return (snapshot.to_dict() or {}) if snapshot.exists else None
