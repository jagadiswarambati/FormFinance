"""Generate deterministic PDF fixtures for the FormWise settlement demo."""

from pathlib import Path

import fitz


FIXTURE_DIR = Path(__file__).parent

FIXTURES = {
    "valid_settlement.pdf": """RAZORPAY SETTLEMENT REPORT
Settlement ID: RZP-DEMO-001
Settlement Date: 2026-08-20
Currency: INR

FINANCIAL SUMMARY
Gross Amount: INR 100,000.00

DEDUCTIONS
Processing Fee: INR 2,000.00
Refund: INR 1,000.00
Chargeback: INR 500.00

Total Deductions: INR 3,500.00
Net Amount: INR 96,500.00
Status: COMPLETED
""",
    "deduction_mismatch_settlement.pdf": """RAZORPAY SETTLEMENT REPORT
Settlement ID: RZP-DEMO-002
Settlement Date: 2026-08-21
Currency: INR

Gross Amount: INR 100,000.00
Processing Fee: INR 2,000.00
Refund: INR 1,000.00
Chargeback: INR 700.00
Total Deductions: INR 3,700.00
Net Amount: INR 96,300.00
Exception: chargeback differs from ledger expectation
""",
    "missing_evidence_settlement.pdf": """RAZORPAY SETTLEMENT REPORT
Settlement ID: RZP-DEMO-003
Settlement Date: 2026-08-22
Currency: INR

Gross Amount: INR 80,000.00
Adjustment: INR 5,000.00
Net Amount: INR 75,000.00
Evidence Status: DOCUMENTATION NOT PROVIDED
""",
    "escalation_settlement.pdf": """STRIPE PAYOUT REPORT
Payout ID: po_DEMO_ESCALATE_004
Settlement Date: 2026-08-23
Currency: USD

Gross Amount: USD 50,000.00
Refund: $2,000.00
Chargeback: $1,500.00
Hold: $1,000.00
Net Payout: $45,500.00
Risk Status: MANUAL INVESTIGATION REQUIRED
""",
    "multiple_deductions_settlement.pdf": """RAZORPAY SETTLEMENT REPORT
Settlement ID: RZP-DEMO-005
Settlement Date: 2026-08-24
Currency: INR

Gross Amount: INR 250,000.00
Processing Fee: INR 5,000.00
Refund: INR 2,500.00
Chargeback: INR 1,200.00
Hold: INR 3,000.00
Adjustment: INR 800.00
Total Deductions: INR 12,500.00
Net Amount: INR 237,500.00
Status: COMPLETED
""",
    "chargeback_evidence_match.pdf": """CHARGEBACK EVIDENCE RECEIPT
Reference: TXN-DEMO-001
Transaction Date: 2026-08-20
Amount: INR 500.00
Chargeback Status: CONFIRMED
""",
    "chargeback_evidence_mismatch.pdf": """CHARGEBACK EVIDENCE RECEIPT
Reference: TXN-DEMO-001
Transaction Date: 2026-08-20
Amount: INR 700.00
Chargeback Status: CONFIRMED
""",
}


def write_fixture(filename: str, text: str) -> None:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_textbox(
        fitz.Rect(54, 54, 541, 788),
        text,
        fontsize=12,
        fontname="courier",
        lineheight=1.5,
    )
    document.save(FIXTURE_DIR / filename, garbage=4, deflate=True)
    document.close()


if __name__ == "__main__":
    for fixture_name, fixture_text in FIXTURES.items():
        write_fixture(fixture_name, fixture_text)
    print(f"Generated {len(FIXTURES)} settlement PDF fixtures in {FIXTURE_DIR}")