"""Settlement extraction from FormWise documents."""

import re
from datetime import date
from typing import Optional
from formwise_api.documents.repository import DocumentRepository
from formwise_api.documents.models import DocumentResponse
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.audit.finance_audit_events import FinanceAuditEvent
from formwise_api.audit.repository import FinanceAuditEventRepository


class DocumentSettlementExtractor:
    """Extracts settlement information from FormWise documents.
    
    Workflow:
    1. Load document from DocumentRepository
    2. Retrieve OCR-extracted text
    3. Parse settlement structure (amounts, deductions, dates)
    4. Create Settlement and SettlementDeduction records
    5. Log extraction events
    """
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        audit_repo: FinanceAuditEventRepository,
    ):
        self._document_repo = document_repo
        self._audit_repo = audit_repo
    
    def extract_from_document(
        self,
        document_id: str,
        owner_uid: str,
        ocr_text: Optional[str] = None,
    ) -> Optional[tuple[Settlement, list[SettlementDeduction]]]:
        """
        Extract settlement from FormWise document.
        
        Args:
            document_id: Document ID in FormWise
            owner_uid: Owner user ID
            ocr_text: OCR text (if already extracted; otherwise will use document's OCR)
            
        Returns:
            (Settlement, [SettlementDeduction]) or None if extraction fails
        """
        # Load document from FormWise
        document = self._document_repo.get_for_owner(document_id, owner_uid)
        if not document:
            return None
        
        # Get OCR text
        if ocr_text is None:
            # TODO (production): Load from ocr_text_storage_key
            # For now, return None if no text provided
            return None
        
        # Parse settlement from OCR text
        settlement_data = self._parse_settlement_data(ocr_text)
        if not settlement_data:
            return None
        
        # Create Settlement
        settlement = Settlement(
            id=document_id,  # Use document ID as settlement ID
            owner_uid=owner_uid,
            source=settlement_data.get("source", "unknown"),
            settlement_date=settlement_data.get("settlement_date", date.today()),
            gross_amount=settlement_data.get("gross_amount", 0.0),
            net_amount=settlement_data.get("net_amount", 0.0),
            currency=settlement_data.get("currency", "INR"),
        )
        
        # Create deductions
        deductions = []
        for deduction_data in settlement_data.get("deductions", []):
            deduction = SettlementDeduction(
                settlement_id=settlement.id,
                type=deduction_data.get("type", "other"),
                description=deduction_data.get("description", ""),
                amount=deduction_data.get("amount", 0.0),
                reference_id=deduction_data.get("reference_id"),
                reference_date=deduction_data.get("reference_date"),
                extracted_with_confidence=deduction_data.get("confidence", 0.85),
            )
            deductions.append(deduction)
        
        # Log extraction event
        self._audit_repo.create(
            FinanceAuditEvent(
                settlement_id=settlement.id,
                action="settlement_uploaded",
                resource_type="settlement",
                resource_id=settlement.id,
                details={
                    "document_id": document_id,
                    "source": settlement.source,
                    "deduction_count": len(deductions),
                    "gross_amount": settlement.gross_amount,
                },
            )
        )
        
        return settlement, deductions

    def extract_deductions(self, ocr_text: str) -> list[dict]:
        """Extract normalized deduction data from OCR text for a caller to persist."""
        return self._extract_deductions(ocr_text)
    
    def _parse_settlement_data(self, ocr_text: str) -> Optional[dict]:
        """
        Parse settlement structure from OCR text.
        
        Looks for common patterns in Razorpay/Stripe/PayPal statements.
        """
        if not ocr_text or len(ocr_text) < 50:
            return None
        
        data = {
            "source": "other",
            "settlement_date": date.today(),
            "gross_amount": 0.0,
            "net_amount": 0.0,
            "currency": "INR",
            "deductions": [],
        }
        
        # Determine source from text
        text_lower = ocr_text.lower()
        if "razorpay" in text_lower:
            data["source"] = "razorpay"
        elif "stripe" in text_lower:
            data["source"] = "stripe"
        elif "paypal" in text_lower:
            data["source"] = "paypal"
        
        # Extract amounts - try multiple patterns
        amount_patterns = [
            r"gross[:\s]+(?:INR|₹|Rs\.?|\$|USD)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
            r"total\s+revenue\s*:\s*(?:INR|₹|Rs\.?|\$|USD|EUR)?\s*(\d+(?:,\d+)*(?:\.\d{2})?)",
            r"gross\s*amount[:\s]*(?:INR|₹|Rs\.?|\$|USD)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
            r"total\s*amount[:\s]*(?:INR|₹|Rs\.?|\$|USD)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, ocr_text, re.IGNORECASE)
            if matches:
                # Clean the number (remove commas, convert)
                amount_str = matches[0].replace(",", "")
                try:
                    data["gross_amount"] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract net amount
        net_patterns = [
            r"net\s*(?:amount|payout)[:\s]*(?:INR|₹|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
            r"settlement\s*amount[:\s]*(?:INR|₹|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
            r"total\s*payout[:\s]*(?:INR|₹|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
            r"net[:\s]*(?:INR|₹|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)",
        ]
        
        for pattern in net_patterns:
            matches = re.findall(pattern, ocr_text, re.IGNORECASE)
            if matches:
                amount_str = matches[0].replace(",", "")
                try:
                    data["net_amount"] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract currency
        if "USD" in ocr_text or "$" in ocr_text:
            data["currency"] = "USD"
        elif "EUR" in ocr_text or "€" in ocr_text:
            data["currency"] = "EUR"
        
        # Extract deductions
        data["deductions"] = self._extract_deductions(ocr_text)
        
        return data if data["gross_amount"] > 0 else None
    
    def _extract_deductions(self, ocr_text: str) -> list[dict]:
        """Extract individual deductions from OCR text."""
        deductions = []
        
        # Patterns for common deduction types
        deduction_patterns = [
            (r"chargeback[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "chargeback"),
            (r"(?:refund|refunds)[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "refund"),
            (r"(?:fee|fees)[s]?[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "fee"),
            (r"hold[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "hold"),
            (r"reserve[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "hold"),
            (r"dispute[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "chargeback"),
            (r"adjustment[:\s]*(?:₹|INR|Rs\.?|\$)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)", "other"),
        ]
        
        for pattern, dtype in deduction_patterns:
            matches = re.finditer(pattern, ocr_text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    if amount > 0:
                        deductions.append({
                            "type": dtype,
                            "description": f"{dtype.capitalize()} deduction",
                            "amount": amount,
                            "reference_id": None,
                            "reference_date": None,
                            "confidence": 0.80,  # Pattern-matched confidence
                        })
                except ValueError:
                    continue
        
        return deductions
