"""Evidence matcher service for finding and matching supporting evidence."""

import re
from datetime import date, datetime
from typing import Any
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.deterministic_verifier import DeterministicVerifier
from formwise_api.verification.models import DeductionVerificationStatus, VerificationResult
from formwise_api.evidence.models import EvidenceLink
from formwise_api.evidence.repository import EvidenceLinkRepository
from formwise_api.privacy.storage import LocalPrivacyTextStore


class SettlementEvidenceStore:
    """Evidence store - can use DocumentRepository or mock."""
    
    def __init__(self, document_repo: Any = None) -> None:
        self.evidence_database: dict[str, list[dict[str, Any]]] = {}
        self._document_repo = document_repo
    
    def register_evidence(self, deduction_id: str, evidence_type: str, evidence_data: dict[str, Any]) -> None:
        """Register evidence for a deduction (for testing)."""
        if deduction_id not in self.evidence_database:
            self.evidence_database[deduction_id] = []
        self.evidence_database[deduction_id].append({
            "type": evidence_type,
            "data": evidence_data
        })
    
    def link_evidence_document(self, deduction_id: str, document_id: str, match_type: str) -> None:
        """Link a document as evidence for a deduction."""
        if deduction_id not in self.evidence_database:
            self.evidence_database[deduction_id] = []
        self.evidence_database[deduction_id].append({
            "type": "document",
            "data": {"document_id": document_id, "match_type": match_type}
        })
    
    def find_evidence_for_deduction(self, deduction: SettlementDeduction, owner_uid: str | None = None) -> list[dict[str, Any]]:
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

    def get_ocr_text(self, evidence_item: dict[str, Any]) -> str | None:
        """Load OCR text for a candidate evidence item from FormWise storage."""
        data = evidence_item.get("data", {})
        if isinstance(data, dict) and isinstance(data.get("ocr_text"), str):
            return data["ocr_text"]

        if not isinstance(data, dict):
            return None

        document_id = data.get("document_id")
        if not document_id or not self._document_repo:
            return None

        document = self._document_repo.get_for_owner(document_id, data.get("owner_uid"))
        if not document or getattr(document, "ocr_status", None) != "completed" or not getattr(document, "ocr_text_storage_key", None):
            return None

        try:
            return LocalPrivacyTextStore("").read_ocr(document.ocr_text_storage_key)
        except (OSError, UnicodeError):
            return None

    def _query_formwise_documents(self, deduction: SettlementDeduction, owner_uid: str) -> list[dict[str, Any]]:
        """Query FormWise DocumentRepository for matching evidence."""
        if not self._document_repo:
            return []
        
        evidence_results: list[dict[str, Any]] = []
        
        # Get all documents for this owner
        try:
            documents = self._document_repo.list_for_owner(owner_uid, limit=50)
        except Exception:
            return []

        if not documents:
            return []
        
        # Match documents to deduction based on type and content hints
        try:
            for doc in documents:
                match_type = self._get_match_type(deduction, doc)
                if match_type:
                    doc_id = getattr(doc, "document_id", None) or getattr(doc, "id", "doc_unknown")
                    filename = getattr(doc, "original_filename", "")
                    evidence_results.append({
                        "type": "document",
                        "data": {
                            "document_id": doc_id,
                            "filename": filename,
                            "match_type": match_type,
                            "owner_uid": owner_uid,
                        }
                    })
        except TypeError:
            return []
        
        return evidence_results

    def _get_match_type(self, deduction: SettlementDeduction, doc: Any) -> str | None:
        """Determine if a document matches the deduction."""
        deduction_type = deduction.type.lower()
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
    
    def __init__(self, evidence_repo: EvidenceLinkRepository, evidence_store: SettlementEvidenceStore | None = None) -> None:
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
        evidence_items = self._evidence_store.find_evidence_for_deduction(
            deduction, owner_uid=settlement.owner_uid
        )
        
        if not evidence_items:
            # No evidence found
            return (
                VerificationResult(
                    deductionId=deduction.id,
                    settlementId=deduction.settlement_id,
                    status="unverifiable",
                    reason="No supporting evidence found",
                    evidenceMatch={"evidence_found": False},
                ),
                None,
            )
        
        # Evaluate every candidate's financial fields; discovery metadata alone is not proof.
        best_match: dict[str, Any] | None = None
        best_result: VerificationResult | None = None
        best_score = -1
        
        for evidence_item in evidence_items:
            evidence_item.setdefault("data", {}).setdefault("owner_uid", settlement.owner_uid)
            evidence_data = self._evidence_fields(evidence_item)
            result = self._compare_evidence(deduction, evidence_data)
            score = sum(value is True for value in result.evidence_match.values())
            if best_result is None or score > best_score:
                best_match = evidence_item
                best_result = result
                best_score = score
        
        if best_result is None or best_match is None:
            return (
                VerificationResult(
                    deductionId=deduction.id,
                    settlementId=deduction.settlement_id,
                    status="unverifiable",
                    reason="Evidence found but could not be matched",
                    evidenceMatch={"evidence_found": True, "match_failed": True},
                ),
                None,
            )
        
        # Create evidence link
        doc_data = best_match.get("data", {}) if isinstance(best_match, dict) else {}
        evidence_doc_id = doc_data.get("document_id", "generated") if isinstance(doc_data, dict) else "generated"
        
        evidence_link = EvidenceLink(
            deductionId=deduction.id,
            evidenceDocumentId=evidence_doc_id,
            linkConfidence=float(best_result.evidence_match.get("confidence", 0.0)),
            extractedFromEvidence=str(best_result.evidence_match.get("evidence_amount", "unknown")),
            status="found" if best_result.status == "verified" else "partial",
        )
        
        return best_result, evidence_link

    def _evidence_fields(self, evidence_item: dict[str, Any]) -> dict[str, Any]:
        data = evidence_item.get("data", {}) if isinstance(evidence_item, dict) else {}
        if not isinstance(data, dict):
            data = {}
        ocr_text = self._evidence_store.get_ocr_text(evidence_item)
        if ocr_text is None:
            fields: dict[str, Any] = {key: data.get(key) for key in ("amount", "date", "reference")}
            if "ocr_available" in data:
                fields["ocr_available"] = bool(data["ocr_available"])
            else:
                fields["ocr_available"] = False
            return fields
        fields = self._extract_ocr_fields(ocr_text)
        fields["ocr_available"] = True
        return fields

    def _compare_evidence(self, deduction: SettlementDeduction, evidence: dict[str, Any]) -> VerificationResult:
        expected: dict[str, Any] = {
            "amount": deduction.amount,
            "date": deduction.reference_date,
            "reference": deduction.reference_id,
        }
        checks: dict[str, bool] = {}
        reasons: list[str] = []
        for field, expected_value in expected.items():
            if expected_value is None:
                continue
            actual_value = evidence.get(field)
            label = "reference" if field == "reference" else field
            if actual_value is None:
                checks[f"{field}_match"] = False
                reasons.append(f"Missing {label} in evidence OCR")
                continue
            if field == "amount":
                matches = self._amounts_equal(expected_value, actual_value)
            elif field == "date":
                matches = self._parse_date(actual_value) == self._parse_date(expected_value)
            else:
                matches = self._normalize_reference(expected_value) == self._normalize_reference(actual_value)
            checks[f"{field}_match"] = matches
            if not matches:
                reasons.append(
                    f"{label.capitalize()} mismatch: expected {self._display(expected_value)}, evidence contains {self._display(actual_value)}"
                )

        required = len(checks)
        matched = sum(checks.values())
        confidence = matched / required if required else 0.0
        ocr_avail = bool(evidence.get("ocr_available", True))
        evidence_match: dict[str, Any] = {
            "evidence_found": ocr_avail,
            "amount_match": checks.get("amount_match"),
            "date_match": checks.get("date_match"),
            "reference_match": checks.get("reference_match"),
            "confidence": confidence,
        }
        if "amount" in evidence and evidence["amount"] is not None:
            evidence_match["evidence_amount"] = evidence["amount"]
        if not ocr_avail and not any(value is not None for key, value in evidence.items() if key != "ocr_available"):
            reasons = ["Evidence OCR is unavailable"]
        has_mismatch = any(
            value is False and evidence.get(field.removesuffix("_match")) is not None
            for field, value in checks.items()
            if field.endswith("_match")
        )
        status: DeductionVerificationStatus = (
            "verified" if required and matched == required
            else "disputed" if has_mismatch
            else "unverifiable"
        )
        return VerificationResult(
            deductionId=deduction.id,
            settlementId=deduction.settlement_id,
            status=status,
            reason="All required evidence fields match" if status == "verified" else "; ".join(reasons),
            deterministicChecks=checks,
            evidenceMatch=evidence_match,
        )

    @staticmethod
    def _extract_ocr_fields(text: str) -> dict[str, Any]:
        amount_match = re.search(
            r"(?:amount|value|total|deduction|fee|refund|chargeback)\s*[:=-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
            text,
            re.IGNORECASE,
        )
        date_match = re.search(
            r"(?:transaction\s+date|reference\s+date|processed\s+date|date)\s*[:=-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            text,
            re.IGNORECASE,
        )
        reference_match = re.search(
            r"(?:reference|transaction|txn|payment)\s*(?:id|no\.?|number)?\s*[:#=-]?\s*([A-Za-z0-9][A-Za-z0-9._/-]{2,})",
            text,
            re.IGNORECASE,
        )
        return {
            "amount": float(amount_match.group(1).replace(",", "")) if amount_match else None,
            "date": EvidenceMatcher._parse_date(date_match.group(1)) if date_match else None,
            "reference": reference_match.group(1) if reference_match else None,
        }

    @staticmethod
    def _parse_date(value: object) -> date | None:
        if isinstance(value, date):
            return value
        if not isinstance(value, str):
            return None
        for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), pattern).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _normalize_reference(value: object) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value).lower())

    @staticmethod
    def _amounts_equal(first: object, second: object) -> bool:
        try:
            if isinstance(first, (int, float, str)) and isinstance(second, (int, float, str)):
                return abs(float(first) - float(second)) <= 0.01
            return False
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _display(value: object) -> str:
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        return str(value)
    
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
