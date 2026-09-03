"""Integrated settlement processing pipeline.

Complete workflow:
1. Load settlement document (FormWise)
2. Extract OCR text from document
3. Parse settlement structure
4. Find evidence documents
5. Run deterministic verification
6. AI investigation for unresolved
7. Generate decision
8. Log audit trail
"""

from datetime import UTC, datetime
from typing import Optional
from uuid import uuid4

from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.deterministic_verifier import DeterministicVerifier
from formwise_api.settlements.evidence_matcher import EvidenceMatcher, SettlementEvidenceStore
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.settlements.finance_agent import SettlementFinanceAgent
from formwise_api.settlements.repository import (
    SettlementRepository,
    SettlementDeductionRepository,
)
from formwise_api.verification.repository import (
    SettlementDecisionRepository,
    VerificationResultRepository,
)
from formwise_api.audit.repository import FinanceAuditEventRepository
from formwise_api.audit.finance_audit_events import FinanceAuditEvent
from formwise_api.documents.repository import DocumentRepository
from formwise_api.evidence.repository import EvidenceLinkRepository
from formwise_worker.ocr.store import LocalOcrResultStore


class SettlementProcessingPipeline:
    """Complete settlement processing pipeline."""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        settlement_repo: SettlementRepository,
        deduction_repo: SettlementDeductionRepository,
        verification_repo: VerificationResultRepository,
        decision_repo: SettlementDecisionRepository,
        evidence_repo: EvidenceLinkRepository,
        audit_repo: FinanceAuditEventRepository,
        evidence_store: Optional[SettlementEvidenceStore] = None,
    ):
        self._document_repo = document_repo
        self._settlement_repo = settlement_repo
        self._deduction_repo = deduction_repo
        self._verification_repo = verification_repo
        self._decision_repo = decision_repo
        self._evidence_repo = evidence_repo
        self._audit_repo = audit_repo
        
        # Initialize evidence store with document repo
        self._evidence_store = evidence_store or SettlementEvidenceStore(
            document_repo=document_repo
        )
        
        # Initialize services
        self._extractor = DocumentSettlementExtractor(
            document_repo=document_repo,
            audit_repo=audit_repo,
        )
        self._verifier = DeterministicVerifier()
        self._matcher = EvidenceMatcher(
            evidence_repo=evidence_repo,
            evidence_store=self._evidence_store,
        )
        self._verification_service = SettlementVerificationService(
            settlement_repo=settlement_repo,
            deduction_repo=deduction_repo,
            verification_repo=verification_repo,
            decision_repo=decision_repo,
            audit_repo=audit_repo,
            evidence_link_repo=evidence_repo,
        )
        # Agent is initialized within SettlementVerificationService if ai_provider is available
        self._agent = None  # Not directly needed here
    
    def process_settlement_document(
        self,
        document_id: str,
        owner_uid: str,
        ocr_text: Optional[str] = None,
        evidence_document_ids: Optional[list[str]] = None,
    ) -> dict:
        """
        Complete settlement processing workflow.
        
        Args:
            document_id: Settlement document ID
            owner_uid: Owner user ID
            ocr_text: Optional pre-extracted OCR text
            evidence_document_ids: Optional list of document IDs containing evidence
            
        Returns:
            {
                "settlement_id": str,
                "status": "approved|flagged|escalated",
                "deductions": [...],
                "decision": {...},
                "audit_trail": [...],
                "metrics": {...},
            }
        """
        now = datetime.now(UTC)
        
        # STAGE 1: Load document
        document = self._document_repo.get_for_owner(document_id, owner_uid)
        if not document:
            return {
                "error": "Document not found",
                "status": "failed",
            }
        
        # Log settlement uploaded event
        self._audit_repo.create(
            FinanceAuditEvent(
                settlement_id=document_id,
                action="settlement_uploaded",
                resource_type="settlement",
                resource_id=document_id,
                details={
                    "document_id": document_id,
                    "filename": document.original_filename,
                },
            )
        )
        
        # STAGE 2: Extract settlement from document
        if ocr_text is None and document.ocr_text_storage_key:
            if document.ocr_status != "completed":
                return {
                    "error": "Document OCR not completed",
                    "status": "pending_ocr",
                    "document_id": document_id,
                }
            try:
                ocr_text = LocalOcrResultStore("").read(document.ocr_text_storage_key)
            except (OSError, UnicodeError):
                return {
                    "error": "Document OCR result is unavailable",
                    "status": "ocr_unavailable",
                    "document_id": document_id,
                }
            if not ocr_text.strip():
                return {
                    "error": "Document OCR result is empty",
                    "status": "ocr_unavailable",
                    "document_id": document_id,
                }
        elif ocr_text is None:
            return {
                "error": "Document OCR has not produced a result",
                "status": "pending_ocr",
                "document_id": document_id,
            }
        
        extraction_result = self._extractor.extract_from_document(
            document_id=document_id,
            owner_uid=owner_uid,
            ocr_text=ocr_text,
        )
        
        if not extraction_result:
            self._audit_repo.create(
                FinanceAuditEvent(
                    settlement_id=document_id,
                    action="extraction_completed",  # Log that extraction was attempted
                    resource_type="settlement",
                    resource_id=document_id,
                    details={
                        "reason": "Could not extract settlement from document",
                        "status": "failed",
                    },
                )
            )
            return {
                "error": "Could not extract settlement from document",
                "status": "extraction_failed",
                "document_id": document_id,
            }
        
        settlement, deductions = extraction_result
        
        # Save settlement
        self._settlement_repo.create(settlement)
        for deduction in deductions:
            self._deduction_repo.create(deduction)
        self._settlement_repo.update(
            settlement.id,
            {
                "status": "processing",
                "deductionIds": [deduction.id for deduction in deductions],
            },
        )
        
        # STAGE 3: Link evidence documents
        if evidence_document_ids:
            for evidence_doc_id in evidence_document_ids:
                evidence_doc = self._document_repo.get_for_owner(
                    evidence_doc_id, owner_uid
                )
                if evidence_doc:
                    # Link evidence to settlement deductions
                    # TODO: Smarter matching based on content
                    for deduction in deductions:
                        self._evidence_store.link_evidence_document(
                            deduction_id=deduction.id,
                            document_id=evidence_doc_id,
                            match_type="manual_linked",
                        )
        
        # STAGE 4-7: Run complete verification workflow
        decision = self._verification_service.verify_settlement(
            settlement_id=settlement.id,
        )
        
        # STAGE 8: Prepare response
        if decision:
            verification_results = self._safe_list(
                self._verification_repo, "list_for_settlement", settlement.id
            )
            evidence_links = [
                link.model_dump(by_alias=True, mode="json")
                for deduction in deductions
                for link in self._safe_list(
                    self._evidence_repo, "list_for_deduction", deduction.id
                )
            ]
            evidence_matches = [
                self._evidence_match_payload(item)
                for item in verification_results
                if item.evidence_match
            ]
            audit_events = [
                event.model_dump(by_alias=True, mode="json")
                for event in self._safe_list(
                    self._audit_repo, "list_for_settlement", settlement.id
                )
            ]
            result = {
                "settlement_id": settlement.id,
                "status": decision.final_decision,
                "reference": next((d.reference_id for d in deductions if d.reference_id), None),
                "currency": settlement.currency,
                "gross_amount": settlement.gross_amount,
                "total_deductions": sum(d.amount for d in deductions),
                "net_amount": settlement.net_amount,
                "deductions": [
                    {
                        "id": d.id,
                        "type": d.type,
                        "description": d.description,
                        "amount": d.amount,
                        "referenceId": d.reference_id,
                        "referenceDate": d.reference_date.isoformat() if d.reference_date else None,
                    }
                    for d in deductions
                ],
                "verification": [
                    item.model_dump(by_alias=True, mode="json")
                    for item in verification_results
                ],
                "evidence": evidence_matches + evidence_links,
                "decision": {
                    "status": decision.final_decision,
                    "confidence": decision.confidence,
                    "explanation": decision.reason,
                    "timestamp": decision.created_at.isoformat() if decision.created_at else None,
                },
                "audit_events": audit_events,
                "document_id": document_id,
                "processed_at": now.isoformat(),
            }
        else:
            # Fallback if verification service couldn't process
            # Use deterministic verification instead
            result = {
                "settlement_id": settlement.id,
                "status": "pending_review",  # Default status
                "reference": next((d.reference_id for d in deductions if d.reference_id), None),
                "currency": settlement.currency,
                "gross_amount": settlement.gross_amount,
                "total_deductions": sum(d.amount for d in deductions),
                "net_amount": settlement.net_amount,
                "deductions": [
                    {
                        "id": d.id,
                        "type": d.type,
                        "description": d.description,
                        "amount": d.amount,
                    }
                    for d in deductions
                ],
                "verification": [],
                "evidence": [],
                "decision": {
                    "status": "pending_review",
                    "confidence": 0.0,
                    "explanation": "Settlement awaiting verification",
                    "timestamp": now.isoformat(),
                },
                "audit_events": [],
                "document_id": document_id,
                "processed_at": now.isoformat(),
            }
        
        # Log decision made event
        if decision:
            self._audit_repo.create(
                FinanceAuditEvent(
                    settlement_id=settlement.id,
                    action="decision_made",
                    resource_type="settlement",
                    resource_id=settlement.id,
                    details={
                        "decision": decision.final_decision,
                        "confidence": decision.confidence,
                        "deduction_count": len(deductions),
                    },
                )
            )
            result["audit_events"] = [
                event.model_dump(by_alias=True, mode="json")
                for event in self._safe_list(
                    self._audit_repo, "list_for_settlement", settlement.id
                )
            ]
        
        return result

    @staticmethod
    def _safe_list(repository: object, method_name: str, value: str) -> list:
        method = getattr(repository, method_name, None)
        if not callable(method):
            return []
        try:
            records = method(value)
        except (AttributeError, TypeError):
            return []
        return records if isinstance(records, list) else []

    @staticmethod
    def _evidence_match_payload(result) -> dict:
        match = result.evidence_match or {}
        return {
            "evidenceFound": match.get("evidence_found"),
            "amountMatch": match.get("amount_match"),
            "dateMatch": match.get("date_match"),
            "referenceMatch": match.get("reference_match"),
            "confidence": match.get("confidence"),
            "reasons": [result.reason] if result.reason else [],
        }
    
    def get_settlement_details(
        self,
        settlement_id: str,
        owner_uid: str,
    ) -> Optional[dict]:
        """Get complete settlement details with verification results."""
        settlement = self._settlement_repo.get(settlement_id)
        if not settlement or settlement.owner_uid != owner_uid:
            return None
        
        deductions = self._deduction_repo.list_by_settlement(settlement_id)
        decision = self._decision_repo.get_by_settlement(settlement_id)
        
        if not decision:
            return None
        
        return {
            "settlement": {
                "id": settlement.id,
                "source": settlement.source,
                "settlement_date": settlement.settlement_date.isoformat(),
                "gross_amount": settlement.gross_amount,
                "net_amount": settlement.net_amount,
                "currency": settlement.currency,
            },
            "deductions": [
                {
                    "id": d.id,
                    "type": d.type,
                    "description": d.description,
                    "amount": d.amount,
                    "reference_id": d.reference_id,
                }
                for d in deductions
            ],
            "decision": {
                "status": decision.final_decision,
                "confidence": decision.confidence,
                "explanation": decision.reason,
                "timestamp": decision.created_at.isoformat() if decision.created_at else None,
            },
        }
