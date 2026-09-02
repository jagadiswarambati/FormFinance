from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.settlements.models import Settlement, SettlementDeduction


class SettlementRepository(Protocol):
    def create(self, settlement: Settlement) -> str: ...
    def get(self, settlement_id: str) -> Settlement | None: ...
    def update(self, settlement_id: str, updates: dict[str, Any]) -> Settlement | None: ...
    def list_for_user(self, user_id: str) -> list[Settlement]: ...


class SettlementDeductionRepository(Protocol):
    def create(self, deduction: SettlementDeduction) -> str: ...
    def get(self, deduction_id: str) -> SettlementDeduction | None: ...
    def list_for_settlement(self, settlement_id: str) -> list[SettlementDeduction]: ...


class FirestoreSettlementRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, settlement: Settlement) -> str:
        self._client.collection("settlements").document(settlement.id).create(
            settlement.model_dump(by_alias=True, mode="python")
        )
        return settlement.id

    def get(self, settlement_id: str) -> Settlement | None:
        snapshot = self._client.collection("settlements").document(settlement_id).get()
        return Settlement.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def update(self, settlement_id: str, updates: dict[str, Any]) -> Settlement | None:
        reference = self._client.collection("settlements").document(settlement_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return None
        updates["updatedAt"] = datetime.now(UTC)
        reference.update(updates)
        data = snapshot.to_dict() or {}
        data.update(updates)
        return Settlement.model_validate(data)

    def list_for_user(self, user_id: str) -> list[Settlement]:
        return [
            Settlement.model_validate(snapshot.to_dict() or {})
            for snapshot in self._client.collection("settlements")
            .where("ownerUid", "==", user_id)
            .order_by("createdAt", direction=False)
            .stream()
        ]


class FirestoreSettlementDeductionRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, deduction: SettlementDeduction) -> str:
        self._client.collection("settlementDeductions").document(deduction.id).create(
            deduction.model_dump(by_alias=True, mode="python")
        )
        return deduction.id

    def get(self, deduction_id: str) -> SettlementDeduction | None:
        snapshot = self._client.collection("settlementDeductions").document(deduction_id).get()
        return SettlementDeduction.model_validate(snapshot.to_dict() or {}) if snapshot.exists else None

    def list_for_settlement(self, settlement_id: str) -> list[SettlementDeduction]:
        return [
            SettlementDeduction.model_validate(snapshot.to_dict() or {})
            for snapshot in self._client.collection("settlementDeductions")
            .where("settlementId", "==", settlement_id)
            .order_by("createdAt")
            .stream()
        ]
