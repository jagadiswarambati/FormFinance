from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.verification.models import VerificationResult, SettlementDecision


class VerificationResultRepository(Protocol):
    def create(self, result: VerificationResult) -> str: ...
    def get(self, result_id: str) -> VerificationResult | None: ...
    def update(self, result_id: str, updates: dict[str, Any]) -> VerificationResult | None: ...
    def list_for_settlement(self, settlement_id: str) -> list[VerificationResult]: ...


class SettlementDecisionRepository(Protocol):
    def create(self, decision: SettlementDecision) -> str: ...
    def get(self, decision_id: str) -> SettlementDecision | None: ...
    def get_by_settlement(self, settlement_id: str) -> SettlementDecision | None: ...


class FirestoreVerificationResultRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, result: VerificationResult) -> str:
        self._client.collection("verificationResults").document(result.id).create(
            result.model_dump(by_alias=True, mode="python")
        )
        return result.id

    def get(self, result_id: str) -> VerificationResult | None:
        snapshot = self._client.collection("verificationResults").document(result_id).get()
        return VerificationResult.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def update(self, result_id: str, updates: dict[str, Any]) -> VerificationResult | None:
        reference = self._client.collection("verificationResults").document(result_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        reference.update(updates)
        data = snapshot.to_dict() or {}
        data.update(updates)
        return VerificationResult.model_validate(data)

    def list_for_settlement(self, settlement_id: str) -> list[VerificationResult]:
        return [
            VerificationResult.model_validate(snapshot.to_dict() or {})
            for snapshot in self._client.collection("verificationResults")
            .where("settlementId", "==", settlement_id)
            .order_by("createdAt")
            .stream()
        ]


class FirestoreSettlementDecisionRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, decision: SettlementDecision) -> str:
        self._client.collection("settlementDecisions").document(decision.id).create(
            decision.model_dump(by_alias=True, mode="python")
        )
        return decision.id

    def get(self, decision_id: str) -> SettlementDecision | None:
        snapshot = self._client.collection("settlementDecisions").document(decision_id).get()
        return SettlementDecision.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def get_by_settlement(self, settlement_id: str) -> SettlementDecision | None:
        docs = self._client.collection("settlementDecisions").where("settlementId", "==", settlement_id).limit(1).stream()
        for doc in docs:
            return SettlementDecision.model_validate(doc.to_dict() or {})
        return None
