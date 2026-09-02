from typing import Any, Protocol

from formwise_api.audit.finance_audit_events import FinanceAuditEvent


class FinanceAuditEventRepository(Protocol):
    def create(self, event: FinanceAuditEvent) -> str: ...
    def get(self, event_id: str) -> FinanceAuditEvent | None: ...
    def list_for_settlement(self, settlement_id: str) -> list[FinanceAuditEvent]: ...


class FirestoreFinanceAuditEventRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, event: FinanceAuditEvent) -> str:
        self._client.collection("financeAuditEvents").document(event.id).create(
            event.model_dump(by_alias=True, mode="python")
        )
        return event.id

    def get(self, event_id: str) -> FinanceAuditEvent | None:
        snapshot = self._client.collection("financeAuditEvents").document(event_id).get()
        return FinanceAuditEvent.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def list_for_settlement(self, settlement_id: str) -> list[FinanceAuditEvent]:
        return [
            FinanceAuditEvent.model_validate(snapshot.to_dict() or {})
            for snapshot in self._client.collection("financeAuditEvents")
            .where("settlementId", "==", settlement_id)
            .order_by("timestamp")
            .stream()
        ]
