from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.documents.models import DocumentResponse


class DocumentRepository(Protocol):
    def create_pending(self, document: DocumentResponse) -> None: ...
    def get_for_owner(self, document_id: str, owner_uid: str) -> DocumentResponse | None: ...
    def mark_quarantined(self, document_id: str) -> DocumentResponse: ...
    def list_for_owner(self, owner_uid: str, limit: int) -> list[DocumentResponse]: ...
    def start_ocr(self, document_id: str, owner_uid: str, provider: str) -> DocumentResponse | None: ...
    def update_privacy(self, document_id: str, owner_uid: str, updates: dict[str, Any]) -> DocumentResponse | None: ...


class FirestoreDocumentRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create_pending(self, document: DocumentResponse) -> None:
        self._client.collection("documents").document(document.document_id).create({"documentId": document.document_id, "ownerUid": document.owner_uid, "originalFilename": document.original_filename, "storedFilename": document.stored_filename, "contentType": document.content_type, "fileSize": document.file_size, "uploadedAt": document.uploaded_at, "status": document.status, "quarantineStatus": "not_quarantined", "scanStatus": "not_requested", "scanStartedAt": None, "scanCompletedAt": None, "scanProvider": None, "scanReason": None, "ocrStatus": "not_started", "ocrStartedAt": None, "ocrCompletedAt": None, "ocrProvider": None, "ocrConfidence": None, "textLength": None, "ocrTextStorageKey": None, "ocrLayoutStorageKey": None, "protectedLayoutStorageKey": None, "privacyStatus": "not_started", "privacyCompletedAt": None, "privacyPolicyVersion": None, "piiCategories": [], "redactedTextStorageKey": None, "consentDecision": None})

    def get_for_owner(self, document_id: str, owner_uid: str) -> DocumentResponse | None:
        snapshot = self._client.collection("documents").document(document_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        if data.get("ownerUid") != owner_uid:
            return None
        return self._to_model(data)

    def mark_quarantined(self, document_id: str) -> DocumentResponse:
        reference = self._client.collection("documents").document(document_id)
        reference.update(
            {
                "status": "quarantined",
                "quarantineStatus": "pending",
                "scanStatus": "pending",
                "scanStartedAt": None,
                "scanCompletedAt": None,
                "scanProvider": None,
                "scanReason": None,
            }
        )
        data = reference.get().to_dict() or {}
        return self._to_model(data)

    def list_for_owner(self, owner_uid: str, limit: int) -> list[DocumentResponse]:
        query = self._client.collection("documents").where("ownerUid", "==", owner_uid).order_by("uploadedAt", direction="DESCENDING").limit(limit)
        return [self._to_model(snapshot.to_dict() or {}) for snapshot in query.stream()]

    def start_ocr(self, document_id: str, owner_uid: str, provider: str) -> DocumentResponse | None:
        reference = self._client.collection("documents").document(document_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        if data.get("ownerUid") != owner_uid or data.get("status") != "quarantined":
            return None
        if data.get("scanStatus") not in {"pending", "failed"}:
            return None
        reference.update({"scanStatus": "queued", "scanReason": None})
        data.update({"scanStatus": "queued", "scanReason": None})
        return self._to_model(data)

    def update_privacy(self, document_id: str, owner_uid: str, updates: dict[str, Any]) -> DocumentResponse | None:
        reference = self._client.collection("documents").document(document_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        if data.get("ownerUid") != owner_uid:
            return None
        reference.update(updates)
        data.update(updates)
        return self._to_model(data)

    def _to_model(self, data: dict[str, Any]) -> DocumentResponse:
        uploaded_at = data.get("uploadedAt")
        if not isinstance(uploaded_at, datetime):
            uploaded_at = datetime.now(UTC)
        return DocumentResponse(document_id=str(data["documentId"]), owner_uid=str(data["ownerUid"]), original_filename=str(data["originalFilename"]), stored_filename=str(data["storedFilename"]), content_type=str(data["contentType"]), file_size=int(data["fileSize"]), uploaded_at=uploaded_at, status=str(data["status"]), quarantine_status=str(data.get("quarantineStatus", "not_quarantined")), scan_status=str(data.get("scanStatus", "not_requested")), scan_started_at=data.get("scanStartedAt") if isinstance(data.get("scanStartedAt"), datetime) else None, scan_completed_at=data.get("scanCompletedAt") if isinstance(data.get("scanCompletedAt"), datetime) else None, scan_provider=data.get("scanProvider") if isinstance(data.get("scanProvider"), str) else None, scan_reason=data.get("scanReason") if isinstance(data.get("scanReason"), str) else None, ocr_status=str(data.get("ocrStatus", "not_started")), ocr_started_at=data.get("ocrStartedAt") if isinstance(data.get("ocrStartedAt"), datetime) else None, ocr_completed_at=data.get("ocrCompletedAt") if isinstance(data.get("ocrCompletedAt"), datetime) else None, ocr_provider=data.get("ocrProvider") if isinstance(data.get("ocrProvider"), str) else None, ocr_confidence=float(data["ocrConfidence"]) if isinstance(data.get("ocrConfidence"), (float, int)) else None, text_length=int(data["textLength"]) if isinstance(data.get("textLength"), int) else None, ocr_text_storage_key=data.get("ocrTextStorageKey") if isinstance(data.get("ocrTextStorageKey"), str) else None, ocr_layout_storage_key=data.get("ocrLayoutStorageKey") if isinstance(data.get("ocrLayoutStorageKey"), str) else None, protected_layout_storage_key=data.get("protectedLayoutStorageKey") if isinstance(data.get("protectedLayoutStorageKey"), str) else None, privacy_status=str(data.get("privacyStatus", "not_started")), privacy_completed_at=data.get("privacyCompletedAt") if isinstance(data.get("privacyCompletedAt"), datetime) else None, privacy_policy_version=data.get("privacyPolicyVersion") if isinstance(data.get("privacyPolicyVersion"), str) else None, pii_categories=[str(item) for item in data.get("piiCategories", []) if isinstance(item, str)], redacted_text_storage_key=data.get("redactedTextStorageKey") if isinstance(data.get("redactedTextStorageKey"), str) else None, consent_decision=data.get("consentDecision") if isinstance(data.get("consentDecision"), str) else None)
