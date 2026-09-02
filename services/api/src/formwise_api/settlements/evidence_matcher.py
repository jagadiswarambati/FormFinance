"""Evidence matcher service for finding and matching supporting evidence."""

from datetime import date
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.deterministic_verifier import DeterministicVerifier
from formwise_api.verification.models import VerificationResult
from formwise_api.evidence.models import EvidenceLink, EvidenceLinkStatus
from formwise_api.evidence.repository import EvidenceLinkRepository


class SettlementEvidenceStore:
    """Evidence store - can use DocumentRepository or mock."""
    
    def __init__(self, document_repo=None):
        self.evidence_database = {}
        self._document_repo = document_repo
    
    def register_evidence(self, deduction_id: str, evidence_type: str, evidence_data: dict):
        """Register evidence for a deduction (for testing)."""
        if deduction_id not in self.evidence_database:
            self.evidence_database[deduction_id] = []
        self.evidence_database[deduction_id].append({
            "type": evidence_type,
            "data": evidence_data
        })
    
    def link_evidence_document(self, deduction_id: str, document_id: str, match_type: str):
        """Link a document as evidence for a deduction."""
        if deduction_id not in self.evidence_database:
            self.evidence_database[deduction_id] = []
        self.evidence_database[deduction_id].append({
            "type": "document",
            "data": {"document_id": document_id, "match_type": match_type}
        })
    
    def find_evidence_for_deduction(self, deduction: SettlementDeduction, owner_uid: str = None) -> list[dict]:
        """Find evidence documents matching deduction criteria."""
        # First check registered evidence (test data)
        evidence = self.evidence_database.get(deduction.id, [])
        
        # REAL: Query FormWise DocumentRepository for matching evidence
        if self._document_repo and owner_uid and not evidence:
            # Search FormWise documents for matching deduction evidence
            # This would look for:
            # - Chargeback documents (for chargeback deductions)
            # - Refund receipts (for refund deductions)
            # - Delivery proofs (for delivery-related deductions)
            evidence = self._query_formwise_documents(
                deduction, owner_uid
            )
        
        return evidence

    def _query_formwise_documents(self, deduction: SettlementDeduction, owner_uid: str) -> list[dict]:
        """Query FormWise DocumentRepository for matching evidence."""
        if not self._document_repo:
            return []
        
        evidence_results = []
        
        # Get all documents for this owner
        documents = self._document_repo.list_for_owner(owner_uid, limit=50)
        
        if not documents:
            return []
        
        # Match documents to deduction based on type and content hints
        for doc in documents:
            match_type = self._get_match_type(deduction, doc)
            if match_type:
                evidence_results.append({
                    "type": "document",
                    "data": {
                        "document_id": doc.document_id,
                        "filename": doc.original_filename,
                        "match_type": match_type,
                    }
                })
        
        return evidence_results

    def _get_match_type(self, deduction: SettlementDeduction, doc) -> str | None:
        """Determine if a document matches the deduction."""
        deduction_type = deduction.deduction_type.lower()
        filename = doc.original_filename.lower() if hasattr(doc, 'original_filename') else ""
        
        # Match based on filename hints
        if "chargeback" in deduction_type and "chargeback" in filename:
            return "chargeback_document"
        elif "refund" in deduction_type and ("refund" in filename or "receipt" in filename):
            return "refund_receipt"
        elif "delivery" in deduction_type and ("delivery" in filename or "proof" in filename):
            return "delivery_proof"
        elif deduction_type in filename:
            return "matching_evidence"
        
        return None


class EvidenceMatcher:
    """Matches deductions against available evidence."""
    
    def __init__(self, evidence_repo: EvidenceLinkRepository, evidence_store: SettlementEvidenceStore | None = None):
        self._evidence_repo = evidence_repo
        self._evidence_store = evidence_store or SettlementEvidenceStore()
        self._verifier = DeterministicVerifier()
    
    def match_deduction_to_evidence(
        self,
        deduction: SettlementDeduction,
        settlement: Settlement,
    ) -> tuple[VerificationResult, EvidenceLink | None]:
        """
        Match a deduction against available evidence.
        
        Returns:
            (VerificationResult, EvidenceLink if found)
        """
        # Find potential evidence
        evidence_items = self._evidence_store.find_evidence_for_deduction(deduction)
        
        if not evidence_items:
            # No evidence found
            return (
                VerificationResult(
                    deduction_id=deduction.id,
                    settlement_id=deduction.settlement_id,
                    status="unverifiable",
                    reason="No supporting evidence found",
                    evidence_match={"evidence_found": False},
                ),
                None,
            )
        
        # Try to match evidence
        best_match = None
        best_result = None
        
        for evidence_item in evidence_items:
            # Extract amount from evidence
            evidence_amount = evidence_item["data"].get("amount")
            evidence_date = evidence_item["data"].get("date")
            
            if evidence_amount is not None:
                result = self._verifier.verify_deduction_against_evidence(
                    deduction,
                    evidence_amount=evidence_amount,
                    evidence_date=evidence_date,
                )
                
                # Check if this is a good match
                if result.status == "verified":
                    best_match = evidence_item
                    best_result = result
                    break
                elif best_result is None or result.status == "disputed":
                    best_match = evidence_item
                    best_result = result
        
        if best_result is None:
            return (
                VerificationResult(
                    deduction_id=deduction.id,
                    settlement_id=deduction.settlement_id,
                    status="unverifiable",
                    reason="Evidence found but could not be matched",
                    evidence_match={"evidence_found": True, "match_failed": True},
                ),
                None,
            )
        
        # Create evidence link
        evidence_link = EvidenceLink(
            deduction_id=deduction.id,
            evidence_document_id=best_match.get("document_id", "generated"),
            link_confidence=0.85,
            extracted_from_evidence=str(best_match["data"].get("amount", "unknown")),
            status="found" if best_result.status == "verified" else "partial",
        )
        
        return best_result, evidence_link
    
    def match_settlement_evidence(
        self,
        settlement: Settlement,
        deductions: list[SettlementDeduction],
    ) -> dict[str, tuple[VerificationResult, EvidenceLink | None]]:
        """
        Match all deductions in a settlement to evidence.
        
        Returns:
            Dict of {deduction_id: (VerificationResult, EvidenceLink)}
        """
        results = {}
        
        for deduction in deductions:
            result, link = self.match_deduction_to_evidence(deduction, settlement)
            results[deduction.id] = (result, link)
            
            # Persist link if found
            if link:
                self._evidence_repo.create(link)
        
        return results
