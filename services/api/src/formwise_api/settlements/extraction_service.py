"""Settlement extraction service for parsing settlement statements.

Handles extraction of structured settlement data from documents and creating
Settlement + SettlementDeduction records.
"""

from datetime import date
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.repository import (
    SettlementRepository,
    SettlementDeductionRepository,
)
from formwise_api.audit.finance_audit_events import FinanceAuditEvent
from formwise_api.audit.repository import FinanceAuditEventRepository


class SettlementExtractionService:
    """Handles settlement document extraction and deduction parsing.
    
    CURRENT LIMITATION (Day 3-4):
    - Accepts structured deduction data (dicts) directly via API
    - Does NOT load documents from DocumentRepository or run OCR
    - Does NOT integrate with PaddleOCR infrastructure
    
    TODO (Day 5-6+):
    - Load settlement document from DocumentRepository by document_id
    - Run OCR/PaddleOCR extraction pipeline
    - Convert OCR output to structured deduction data
    - Use existing FormWise document/understanding models
    
    Currently designed for synthetic/test data and will be enhanced
    to work with actual settlement PDFs (Razorpay, Stripe, PayPal, etc.)
    """

    def __init__(
        self,
        settlement_repo: SettlementRepository,
        deduction_repo: SettlementDeductionRepository,
        audit_repo: FinanceAuditEventRepository,
    ):
        self._settlement_repo = settlement_repo
        self._deduction_repo = deduction_repo
        self._audit_repo = audit_repo

    def extract_from_structured_data(
        self,
        settlement_id: str,
        deduction_data: list[dict],
    ) -> list[SettlementDeduction]:
        """
        Extract deductions from structured data format.
        
        Args:
            settlement_id: ID of parent settlement
            deduction_data: List of deduction dicts with:
                - type: str (chargeback, fee, hold, refund, other)
                - description: str
                - amount: float
                - reference_id: str (optional)
                - reference_date: date or str (optional)
                - confidence: float (optional, defaults to 0.95)
                
        Returns:
            List of created SettlementDeduction objects
        """
        deductions = []
        
        for data in deduction_data:
            # Parse reference_date if provided as string
            ref_date = None
            if "reference_date" in data and data["reference_date"]:
                ref_date_val = data["reference_date"]
                if isinstance(ref_date_val, str):
                    ref_date = date.fromisoformat(ref_date_val)
                else:
                    ref_date = ref_date_val
            
            deduction = SettlementDeduction(
                settlement_id=settlement_id,
                type=data["type"],
                description=data["description"],
                amount=float(data["amount"]),
                reference_id=data.get("reference_id"),
                reference_date=ref_date,
                extracted_with_confidence=float(data.get("confidence", 0.95)),
            )
            
            # Persist to repository
            deduction_id = self._deduction_repo.create(deduction)
            deduction.id = deduction_id
            deductions.append(deduction)
            
            # Log extraction event
            self._audit_repo.create(
                FinanceAuditEvent(
                    settlement_id=settlement_id,
                    action="deduction_extracted",
                    resource_type="deduction",
                    resource_id=deduction_id,
                    details={
                        "type": deduction.type,
                        "amount": deduction.amount,
                        "confidence": deduction.extracted_with_confidence,
                    },
                    confidence=deduction.extracted_with_confidence,
                )
            )
        
        return deductions

    def complete_extraction(self, settlement_id: str) -> Settlement | None:
        """
        Mark settlement extraction as complete.
        
        Updates settlement status and logs completion event.
        """
        settlement = self._settlement_repo.get(settlement_id)
        if not settlement:
            return None
        
        # Get all deductions to update counts
        deductions = self._deduction_repo.list_for_settlement(settlement_id)
        
        # Update settlement status and deduction references
        updated_settlement = self._settlement_repo.update(
            settlement_id,
            {
                "status": "processing",
                "deductionIds": [d.id for d in deductions],
            },
        )
        
        # Log completion
        if updated_settlement:
            self._audit_repo.create(
                FinanceAuditEvent(
                    settlement_id=settlement_id,
                    action="extraction_completed",
                    resource_type="settlement",
                    resource_id=settlement_id,
                    details={
                        "deduction_count": len(deductions),
                    },
                )
            )
        
        return updated_settlement
