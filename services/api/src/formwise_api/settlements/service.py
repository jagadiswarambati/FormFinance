from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.repository import (
    SettlementRepository,
    SettlementDeductionRepository,
)


class SettlementService:
    """Business logic for settlements"""

    def __init__(
        self,
        settlement_repo: SettlementRepository,
        deduction_repo: SettlementDeductionRepository,
    ):
        self._settlement_repo = settlement_repo
        self._deduction_repo = deduction_repo

    def create_settlement(self, settlement: Settlement) -> str:
        """Create settlement"""
        return self._settlement_repo.create(settlement)

    def get_settlement(self, settlement_id: str) -> Settlement | None:
        """Retrieve settlement"""
        return self._settlement_repo.get(settlement_id)

    def update_settlement(self, settlement_id: str, updates: dict) -> Settlement | None:
        """Update settlement"""
        return self._settlement_repo.update(settlement_id, updates)

    def list_user_settlements(self, user_id: str) -> list[Settlement]:
        """List user's settlements"""
        return self._settlement_repo.list_for_user(user_id)

    def create_deduction(self, deduction: SettlementDeduction) -> str:
        """Create deduction"""
        return self._deduction_repo.create(deduction)

    def get_deduction(self, deduction_id: str) -> SettlementDeduction | None:
        """Retrieve deduction"""
        return self._deduction_repo.get(deduction_id)

    def list_settlement_deductions(self, settlement_id: str) -> list[SettlementDeduction]:
        """List all deductions for a settlement"""
        return self._deduction_repo.list_for_settlement(settlement_id)
