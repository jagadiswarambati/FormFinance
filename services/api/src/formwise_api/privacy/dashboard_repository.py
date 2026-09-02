"""Firestore persistence for response-safe privacy dashboard projections."""

from typing import Any, Protocol

from firebase_admin import firestore
from formwise_document_core.privacy_models import PrivacyAuditEvent, PrivacySummary


class PrivacySummaryRepository(Protocol):
    def save(self, conversation_id: str, summary: PrivacySummary) -> None: ...
    def get(self, conversation_id: str) -> PrivacySummary | None: ...
    def delete(self, conversation_id: str) -> None: ...


class PrivacyAuditEventRepository(Protocol):
    def append(self, event: PrivacyAuditEvent) -> None: ...
    def list_for_conversation(self, conversation_id: str) -> list[PrivacyAuditEvent]: ...
    def delete_for_conversation(self, conversation_id: str) -> None: ...


class FirestorePrivacySummaryRepository:
    """Stores the privacy-summary projection on its owning conversation."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def save(self, conversation_id: str, summary: PrivacySummary) -> None:
        self._client.collection("conversations").document(conversation_id).set(
            {"privacySummary": summary.model_dump(by_alias=True, mode="python")},
            merge=True,
        )

    def get(self, conversation_id: str) -> PrivacySummary | None:
        snapshot = self._client.collection("conversations").document(conversation_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        summary = data.get("privacySummary")
        return PrivacySummary.model_validate(summary) if isinstance(summary, dict) else None

    def delete(self, conversation_id: str) -> None:
        self._client.collection("conversations").document(conversation_id).update(
            {"privacySummary": firestore.DELETE_FIELD}
        )


class FirestorePrivacyAuditEventRepository:
    """Appends response-safe privacy traceability events."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def append(self, event: PrivacyAuditEvent) -> None:
        self._client.collection("auditEvents").document(event.event_id).create(
            event.model_dump(by_alias=True, mode="python")
        )

    def list_for_conversation(self, conversation_id: str) -> list[PrivacyAuditEvent]:
        query = (
            self._client.collection("auditEvents")
            .where("conversationId", "==", conversation_id)
            .order_by("timestamp")
        )
        return [
            PrivacyAuditEvent.model_validate(snapshot.to_dict() or {})
            for snapshot in query.stream()
        ]

    def delete_for_conversation(self, conversation_id: str) -> None:
        query = self._client.collection("auditEvents").where(
            "conversationId", "==", conversation_id
        )
        for snapshot in query.stream():
            snapshot.reference.delete()
