"""Synthetic settlement documents (OCR text) for testing document extraction."""

from datetime import date


class SyntheticDocument:
    """Represents a synthetic settlement document."""
    
    def __init__(
        self,
        doc_id: str,
        category: str,
        ocr_text: str,
        expected_deductions: int,
        expected_decision: str,
        description: str,
    ):
        self.doc_id = doc_id
        self.category = category
        self.ocr_text = ocr_text
        self.expected_deductions = expected_deductions
        self.expected_decision = expected_decision
        self.description = description


def get_synthetic_documents() -> list[SyntheticDocument]:
    """Return all 10 synthetic settlement documents."""
    
    docs = []
    
    # 1. Clean settlement - no issues
    docs.append(SyntheticDocument(
        doc_id="doc_001_clean",
        category="clean",
        ocr_text="""
        RAZORPAY SETTLEMENT STATEMENT
        Settlement Date: 2026-08-15
        
        SUMMARY
        Gross Amount: INR 100,000.00
        Net Amount: INR 100,000.00
        
        No deductions this period.
        """,
        expected_deductions=0,
        expected_decision="approve",
        description="Clean settlement with no deductions",
    ))
    
    # 2. Fee mismatch - extracted vs actual
    docs.append(SyntheticDocument(
        doc_id="doc_002_fee_mismatch",
        category="fee_mismatch",
        ocr_text="""
        RAZORPAY SETTLEMENT STATEMENT
        Settlement Date: 2026-08-14
        
        SUMMARY
        Gross Amount: INR 250,000.00
        Net Amount: INR 245,000.00
        
        DEDUCTIONS
        Processing Fee: INR 5,500.00
        (Standard rate 2.2%)
        """,
        expected_deductions=1,
        expected_decision="flag",
        description="Fee calculation mismatch (2.2% fee on 250K should be 5500)",
    ))
    
    # 3. Refund mismatch
    docs.append(SyntheticDocument(
        doc_id="doc_003_refund_mismatch",
        category="refund_mismatch",
        ocr_text="""
        STRIPE SETTLEMENT REPORT
        Settlement Date: 2026-08-13
        
        MONTHLY SUMMARY
        Total Revenue: USD 5,000.00
        Total Refunds: USD 1,200.00
        Net Amount: USD 3,800.00
        """,
        expected_deductions=1,
        expected_decision="flag",
        description="Refund amount seems high (24% refund rate)",
    ))
    
    # 4. Chargeback
    docs.append(SyntheticDocument(
        doc_id="doc_004_chargeback",
        category="chargeback",
        ocr_text="""
        PAYPAL TRANSACTION SUMMARY
        Period: 2026-08-12 to 2026-08-12
        
        ACCOUNT SUMMARY
        Gross Amount: INR 150,000.00
        Dispute/Chargeback: INR 7,500.00
        Net Payout: INR 142,500.00
        """,
        expected_deductions=1,
        expected_decision="approve",
        description="Legitimate chargeback with clear reference",
    ))
    
    # 5. Missing evidence - no documentation
    docs.append(SyntheticDocument(
        doc_id="doc_005_missing_evidence",
        category="missing_evidence",
        ocr_text="""
        RAZORPAY SETTLEMENT
        Settlement Date: 2026-08-11
        
        SUMMARY
        Gross Amount: INR 75,000.00
        Adjustment: INR 3,500.00
        Net Amount: INR 71,500.00
        
        NOTES
        Adjustment applied - details in separate report
        """,
        expected_deductions=1,
        expected_decision="escalate",
        description="Adjustment with no documentation or clear reason",
    ))
    
    # 6. Amount discrepancy
    docs.append(SyntheticDocument(
        doc_id="doc_006_amount_discrepancy",
        category="amount_discrepancy",
        ocr_text="""
        STRIPE MONTHLY STATEMENT
        Month: August 2026
        
        TOTALS
        Total Revenue: INR 500,000.00
        Processing Fees: INR 12,000.00
        Chargebacks: INR 2,500.00
        Net Settlement: INR 487,500.00
        
        Note: Amount differs from expected
        """,
        expected_deductions=2,
        expected_decision="flag",
        description="Settlement arithmetic mismatch (should be 485,500)",
    ))
    
    # 7. Date discrepancy
    docs.append(SyntheticDocument(
        doc_id="doc_007_date_discrepancy",
        category="date_discrepancy",
        ocr_text="""
        PAYPAL SETTLEMENT SLIP
        Statement Date: 2026-08-10
        Effective Date: 2026-09-01
        
        DEDUCTIONS
        Refund ID: REF-2026-0725 - INR 2,000.00
        (Refund dated July 25, 2026)
        
        Total Amount: INR 98,000.00
        Deduction: INR 2,000.00
        Net: INR 96,000.00
        """,
        expected_deductions=1,
        expected_decision="flag",
        description="Refund dated before settlement period",
    ))
    
    # 8. Duplicate entry
    docs.append(SyntheticDocument(
        doc_id="doc_008_duplicate",
        category="duplicate",
        ocr_text="""
        RAZORPAY SETTLEMENT
        Settlement Date: 2026-08-09
        
        SUMMARY
        Gross: INR 200,000.00
        
        DEDUCTIONS
        Chargeback CB-0089: INR 5,000.00
        Chargeback CB-0089: INR 5,000.00
        
        Net: INR 190,000.00
        """,
        expected_deductions=2,
        expected_decision="flag",
        description="Duplicate chargeback entry (same ID)",
    ))
    
    # 9. Low confidence extraction
    docs.append(SyntheticDocument(
        doc_id="doc_009_low_confidence",
        category="low_confidence",
        ocr_text="""
        SETTLEMENT DOCUMENT
        (Scanned document - poor quality)
        
        [ILLEGIBLE] Amount: INR 320,000
        [BLURRED] Deduction: INR 8,00?
        Settlement: INR 31[?],000
        
        Details unclear in scan
        """,
        expected_deductions=1,
        expected_decision="escalate",
        description="Low confidence OCR due to poor document quality",
    ))
    
    # 10. Mixed/ambiguous case
    docs.append(SyntheticDocument(
        doc_id="doc_010_mixed",
        category="mixed_ambiguous",
        ocr_text="""
        MULTI-GATEWAY SETTLEMENT
        Period: August 2026
        
        RAZORPAY
        Gross: INR 150,000
        Fees: INR 3,300
        Net: INR 146,700
        
        STRIPE
        Gross: USD 2,000
        Fees: USD 60
        Hold: USD 200
        Net: USD 1,740
        
        Note: Multiple gateways, mixed currencies, some holds applied
        """,
        expected_deductions=3,
        expected_decision="flag",
        description="Complex multi-gateway settlement with holds and mixed currencies",
    ))
    
    return docs


def get_document(doc_id: str) -> SyntheticDocument | None:
    """Get a specific document by ID."""
    docs = get_synthetic_documents()
    for doc in docs:
        if doc.doc_id == doc_id:
            return doc
    return None
