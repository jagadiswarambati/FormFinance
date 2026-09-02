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

from formwise_api.settlements.models import Settlement, SettlementCreateRequest
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.service import SettlementService
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.verification.models import SettlementDecision
from formwise_api.settlements.repository import SettlementRepository


@dataclass
class BatchMetrics:
    """Metrics from batch processing run."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
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
    ):
        self._settlement_service = settlement_service
        self._document_extractor = document_extractor
        self._verification_service = verification_service
        self._settlement_repo = settlement_repo
    
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
        metrics = BatchMetrics()
        results = []
        
        for spec in settlement_specs:
            result = self._process_single_settlement(owner_uid, spec)
            results.append(result)
            
            # Update metrics
            metrics.total_settlements += 1
            metrics.total_deductions += result.deduction_count
            
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
                metrics.exceptions.append({
                    "settlement_id": result.settlement_id,
                    "status": result.status,
                    "reason": result.decision.reason if result.decision else result.error,
                    "gaps": result.decision.gaps_identified if result.decision else [],
                })
        
        # Calculate rates
        if metrics.total_settlements > 0:
            metrics.settlement_approval_rate = (
                metrics.approved_count / metrics.total_settlements
            )
        
        if metrics.total_deductions > 0:
            metrics.deduction_verification_rate = (
                metrics.verified_deductions / metrics.total_deductions
            )
        
        return metrics, results
    
    def _process_single_settlement(
        self,
        owner_uid: str,
        spec: dict,
    ) -> SettlementProcessResult:
        """Process a single settlement with OCR extraction."""
        
        try:
            # 1. Create settlement record
            from formwise_api.settlements.repository import FirestoreSettlementDeductionRepository
            
            create_req = SettlementCreateRequest(
                source=spec.get("source", "razorpay"),
                settlement_date=spec.get("settlement_date"),
                gross_amount=spec.get("gross_amount", 100000.0),
                net_amount=spec.get("net_amount", 95000.0),
                currency=spec.get("currency", "INR"),
            )
            settlement_id = self._settlement_service.create_settlement(
                Settlement(
                    owner_uid=owner_uid,
                    source=create_req.source,
                    settlement_date=create_req.settlement_date,
                    gross_amount=create_req.gross_amount,
                    net_amount=create_req.net_amount,
                    currency=create_req.currency,
                )
            )
            
            # 2. Extract deductions from OCR text
            ocr_text = spec.get("ocr_text", "")
            extraction_count = 0
            deduction_repo = None
            
            if ocr_text:
                try:
                    # Use document extractor to parse OCR text
                    deductions = self._document_extractor._extract_deductions(ocr_text)
                    extraction_count = len(deductions)
                    
                    # Get deduction repository from extraction service
                    if hasattr(self._document_extractor, '_deduction_repo'):
                        deduction_repo = self._document_extractor._deduction_repo
                    
                    # Add deductions to settlement
                    if deduction_repo and deductions:
                        for ded in deductions:
                            # Set settlement_id on deduction
                            ded.settlement_id = settlement_id
                            deduction_repo.create(ded)
                except Exception as e:
                    # If extraction fails, note it but continue
                    pass
            
            # 3. Run verification workflow
            decision = self._verification_service.verify_settlement(settlement_id)
            
            settlement = self._settlement_service.get_settlement(settlement_id)
            if not settlement:
                return SettlementProcessResult(
                    settlement_id=settlement_id,
                    owner_uid=owner_uid,
                    source=spec.get("source", "razorpay"),
                    status="error",
                    error="Settlement not found after creation",
                    extraction_succeeded=extraction_count > 0,
                    extraction_deduction_count=extraction_count,
                )
            
            # Load deductions to get counts - need to use the extraction service repo
            from formwise_api.authentication.firebase import get_firestore_client
            client = get_firestore_client()
            deduction_repo_instance = FirestoreSettlementDeductionRepository(client)
            deductions = deduction_repo_instance.list_for_settlement(settlement_id)
            deduction_count = len(deductions)
            
            # Extract verification stats from decision if available
            verified_count = 0
            disputed_count = 0
            unverifiable_count = 0
            
            if decision and decision.verification_summary:
                verified_count = decision.verification_summary.get("verified", 0)
                disputed_count = decision.verification_summary.get("disputed", 0)
                unverifiable_count = decision.verification_summary.get("unverifiable", 0)
            
            return SettlementProcessResult(
                settlement_id=settlement_id,
                owner_uid=owner_uid,
                source=settlement.source,
                status=settlement.status,
                deduction_count=deduction_count,
                verified_count=verified_count,
                disputed_count=disputed_count,
                unverifiable_count=unverifiable_count,
                decision=decision,
                extraction_succeeded=extraction_count > 0,
                verification_succeeded=decision is not None,
                extraction_deduction_count=extraction_count,
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return SettlementProcessResult(
                settlement_id="error",
                owner_uid=owner_uid,
                source=spec.get("source", "razorpay"),
                status="error",
                error=str(e),
            )
