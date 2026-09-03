"""Batch settlement processor for demo workflow.

Processes multiple settlements end-to-end:
1. Load settlement documents (OCR text)
2. Extract deductions using document extraction
3. Run verification workflow
4. Aggregate results with metrics
"""

from typing import Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4

from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.service import SettlementService
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.verification.models import SettlementDecision
from formwise_api.settlements.repository import SettlementRepository
from formwise_api.settlements.extraction_service import SettlementExtractionService


@dataclass
class BatchMetrics:
    """Metrics from batch processing run."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_records: int = 0
    processed: int = 0
    successfully_extracted: int = 0
    total_settlements: int = 0
    total_deductions: int = 0
    
    # Settlement outcomes
    approved_count: int = 0
    flagged_count: int = 0
    escalated_count: int = 0
    processing_failed_count: int = 0
    
    # Deduction verification stats
    verified_deductions: int = 0
    disputed_deductions: int = 0
    unverifiable_deductions: int = 0
    
    # Rates
    settlement_approval_rate: float = 0.0
    deduction_verification_rate: float = 0.0
    evidence_checked: int = 0
    evidence_matched: int = 0
    evidence_match_rate: float = 0.0
    exception_count: int = 0
    exception_rate: float = 0.0
    extraction_success_rate: float = 0.0
    
    # AI agent usage
    agent_investigations: int = 0
    agent_successes: int = 0
    agent_failures: int = 0
    
    # Results
    exceptions: list[dict] = field(default_factory=list)
    settlement_results: list[dict] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SettlementProcessResult:
    """Result of processing a single settlement."""
    settlement_id: str
    owner_uid: str
    source: str
    status: str  # approved, flagged, escalated, error
    
    # Counts
    deduction_count: int = 0
    verified_count: int = 0
    disputed_count: int = 0
    unverifiable_count: int = 0
    
    # Decision details
    decision: Optional[SettlementDecision] = None
    error: Optional[str] = None
    
    # Workflow stages
    extraction_succeeded: bool = False
    verification_succeeded: bool = False
    extraction_deduction_count: int = 0
    evidence_checked: bool = False
    evidence_matched: bool = False
    
    def to_dict(self):
        """Convert to dictionary, handling decision object."""
        d = asdict(self)
        if self.decision:
            d['decision'] = {
                'id': self.decision.id,
                'status': self.decision.final_decision,
                'confidence': self.decision.confidence,
                'reason': self.decision.reason,
                'verification_summary': self.decision.verification_summary,
                'gaps_identified': self.decision.gaps_identified or [],
            }
        return d


class BatchSettlementProcessor:
    """Process multiple settlements end-to-end."""
    
    def __init__(
        self,
        settlement_service: SettlementService,
        document_extractor: DocumentSettlementExtractor,
        verification_service: SettlementVerificationService,
        settlement_repo: SettlementRepository,
        extraction_service: SettlementExtractionService | None = None,
    ):
        self._settlement_service = settlement_service
        self._document_extractor = document_extractor
        self._verification_service = verification_service
        self._settlement_repo = settlement_repo
        self._extraction_service = extraction_service
    
    def process_settlements(
        self,
        owner_uid: str,
        settlement_specs: list[dict],
    ) -> tuple[BatchMetrics, list[SettlementProcessResult]]:
        """
        Process a batch of settlements end-to-end.
        
        Args:
            owner_uid: User ID
            settlement_specs: List of settlement spec dicts with:
                - source, settlement_date, gross_amount, net_amount, currency
                - ocr_text (for document extraction)
        
        Returns:
            (BatchMetrics, list of SettlementProcessResult)
        """
        metrics = BatchMetrics(
            total_records=len(settlement_specs),
            total_settlements=len(settlement_specs),
        )
        results = []
        
        for spec in settlement_specs:
            result = self._process_single_settlement(owner_uid, spec)
            results.append(result)
            
            metrics.processed += result.status != "error"
            metrics.successfully_extracted += result.extraction_succeeded
            metrics.total_deductions += result.deduction_count
            metrics.evidence_checked += result.evidence_checked
            metrics.evidence_matched += result.evidence_matched
            
            if result.status == "approved":
                metrics.approved_count += 1
            elif result.status == "flagged":
                metrics.flagged_count += 1
            elif result.status == "escalated":
                metrics.escalated_count += 1
            else:
                metrics.processing_failed_count += 1
            
            if result.verified_count:
                metrics.verified_deductions += result.verified_count
            if result.disputed_count:
                metrics.disputed_deductions += result.disputed_count
            if result.unverifiable_count:
                metrics.unverifiable_deductions += result.unverifiable_count
            
            # Add to results
            metrics.settlement_results.append(result.to_dict())
            
            # Track exceptions
            if result.status in ("flagged", "escalated"):
                metrics.exception_count += 1
                metrics.exceptions.append({
                    "settlement_id": result.settlement_id,
                    "status": result.status,
                    "reason": result.decision.reason if result.decision else result.error,
                    "gaps": result.decision.gaps_identified if result.decision else [],
                })
        
        # Calculate rates
        if metrics.total_records > 0:
            metrics.settlement_approval_rate = metrics.approved_count / metrics.total_records
            metrics.exception_rate = metrics.exception_count / metrics.total_records
            metrics.extraction_success_rate = metrics.successfully_extracted / metrics.total_records
        
        if metrics.total_deductions > 0:
            metrics.deduction_verification_rate = (
                metrics.verified_deductions / metrics.total_deductions
            )
        if metrics.evidence_checked > 0:
            metrics.evidence_match_rate = metrics.evidence_matched / metrics.evidence_checked

        return metrics, results

    def _persist_deductions(self, settlement_id: str, deduction_data: list[dict]) -> list[SettlementDeduction]:
        if self._extraction_service:
            deductions = self._extraction_service.extract_from_structured_data(settlement_id, deduction_data)
            self._extraction_service.complete_extraction(settlement_id)
            return deductions

        deductions = []
        for data in deduction_data:
            deduction = SettlementDeduction(
                settlement_id=settlement_id,
                type=data["type"],
                description=data["description"],
                amount=float(data["amount"]),
                reference_id=data.get("reference_id"),
                reference_date=data.get("reference_date"),
                extracted_with_confidence=float(data.get("confidence", 0.95)),
            )
            deduction.id = self._settlement_service.create_deduction(deduction)
            deductions.append(deduction)
        self._settlement_service.update_settlement(
            settlement_id,
            {"status": "processing", "deductionIds": [deduction.id for deduction in deductions]},
        )
        return deductions
    
    def _process_single_settlement(
        self,
        owner_uid: str,
        spec: dict,
    ) -> SettlementProcessResult:
        """Process a single settlement with OCR extraction."""

        settlement_id = spec.get("settlement_id") or spec.get("id")
        try:
            settlement = Settlement(
                id=settlement_id or uuid4().hex,
                owner_uid=owner_uid,
                source=spec.get("source", "razorpay"),
                settlement_date=spec["settlement_date"],
                gross_amount=spec.get("gross_amount", 100000.0),
                net_amount=spec.get("net_amount", 95000.0),
                currency=spec.get("currency", "INR"),
            )
            settlement_id = self._settlement_service.create_settlement(settlement)

            deduction_data = spec.get("deductions")
            if deduction_data is None:
                deduction_data = self._document_extractor.extract_deductions(spec.get("ocr_text", ""))
            if not spec.get("ocr_text") and spec.get("deductions") is None:
                return SettlementProcessResult(
                    settlement_id=settlement_id,
                    owner_uid=owner_uid,
                    source=settlement.source,
                    status="error",
                    error="No settlement extraction input provided",
                )
            deductions = self._persist_deductions(settlement_id, deduction_data)
            extraction_succeeded = bool(spec.get("ocr_text") or spec.get("deductions") is not None)

            decision = self._verification_service.verify_settlement(settlement_id)
            stored_settlement = self._settlement_service.get_settlement(settlement_id)
            if not stored_settlement or not decision:
                return SettlementProcessResult(
                    settlement_id=settlement_id,
                    owner_uid=owner_uid,
                    source=settlement.source,
                    status="error",
                    error="Settlement verification did not produce a decision",
                    deduction_count=len(deductions),
                    extraction_succeeded=extraction_succeeded,
                    extraction_deduction_count=len(deductions),
                )

            summary = decision.verification_summary or {}
            return SettlementProcessResult(
                settlement_id=settlement_id,
                owner_uid=owner_uid,
                source=stored_settlement.source,
                status={"approve": "approved", "flag": "flagged", "escalate": "escalated"}.get(decision.final_decision, "error"),
                deduction_count=len(deductions),
                verified_count=summary.get("verified", 0),
                disputed_count=summary.get("disputed", 0),
                unverifiable_count=summary.get("unverifiable", 0),
                decision=decision,
                extraction_succeeded=extraction_succeeded,
                verification_succeeded=True,
                extraction_deduction_count=len(deductions),
                evidence_checked=bool(spec.get("evidence_checked", False)),
                evidence_matched=bool(spec.get("evidence_matched", False)),
            )

        except Exception as error:
            return SettlementProcessResult(
                settlement_id=settlement_id or "error",
                owner_uid=owner_uid,
                source=spec.get("source", "razorpay"),
                status="error",
                error=str(error),
            )

    def _persist_deductions(self, settlement_id: str, deduction_data: list[dict]) -> list[SettlementDeduction]:
        if self._extraction_service:
            deductions = self._extraction_service.extract_from_structured_data(settlement_id, deduction_data)
            self._extraction_service.complete_extraction(settlement_id)
            return deductions

        deductions = []
        for data in deduction_data:
            deduction = SettlementDeduction(
                settlement_id=settlement_id,
                type=data["type"],
                description=data["description"],
                amount=float(data["amount"]),
                reference_id=data.get("reference_id"),
                reference_date=data.get("reference_date"),
                extracted_with_confidence=float(data.get("confidence", 0.95)),
            )
            deduction.id = self._settlement_service.create_deduction(deduction)
            deductions.append(deduction)
        self._settlement_service.update_settlement(
            settlement_id,
            {"status": "processing", "deductionIds": [deduction.id for deduction in deductions]},
        )
        return deductions
