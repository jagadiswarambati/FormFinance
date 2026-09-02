"""Demo data for FORMWISE-FINANCE buildathon demonstration.

Provides 10 synthetic settlements with diverse outcomes:
1. Clean/approved
2. Fee mismatch/flagged
3. Refund mismatch/flagged
4. Chargeback/approved
5. Missing evidence/escalated
6. Amount discrepancy/flagged
7. Date discrepancy/flagged
8. Duplicate entry/flagged
9. Low confidence OCR/escalated
10. Multi-gateway/escalated
"""

def get_demo_settlements() -> list[dict]:
    """
    Get 10 synthetic settlement specs for demo workflow.
    
    Returns list of dicts with:
    - source: razorpay, stripe, paypal, other
    - settlement_date: YYYY-MM-DD
    - gross_amount: total before deductions
    - net_amount: total after deductions
    - currency: INR, USD, EUR
    - ocr_text: OCR-extracted text with deductions
    
    Each settlement demonstrates different verification outcomes:
    - 1: Approved (all verified)
    - 2: Flagged (fee mismatch)
    - 3: Flagged (refund mismatch)
    - 4: Approved (chargeback)
    - 5: Escalated (missing evidence)
    - 6: Flagged (amount discrepancy)
    - 7: Flagged (date discrepancy)
    - 8: Flagged (duplicate)
    - 9: Escalated (low confidence)
    - 10: Escalated (multi-gateway)
    """
    
    settlements = [
        # 1. CLEAN/APPROVED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-20",
            "gross_amount": 250000.0,
            "net_amount": 242500.0,
            "currency": "INR",
            "ocr_text": """
RAZORPAY SETTLEMENT REPORT
Date: August 20, 2026
Gross Revenue: INR 250,000.00
Platform Fee: INR 5,000.00
Payment Processing Fee: INR 2,500.00
Total Deductions: INR 7,500.00
Net Payout: INR 242,500.00
Status: COMPLETED
            """,
            "_expected_outcome": "approved",
            "_description": "Clean settlement, all fees match"
        },
        
        # 2. FEE MISMATCH/FLAGGED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-21",
            "gross_amount": 250000.0,
            "net_amount": 240500.0,
            "currency": "INR",
            "ocr_text": """
RAZORPAY SETTLEMENT REPORT
Date: August 21, 2026
Gross Revenue: INR 250,000.00
Platform Fee: INR 5,000.00
Payment Processing Fee: INR 2,500.00
Miscellaneous Fees: INR 2,000.00
Total Deductions: INR 9,500.00
Net Payout: INR 240,500.00
            """,
            "_expected_outcome": "flagged",
            "_description": "Fee amount higher than expected (9,500 vs 7,500)"
        },
        
        # 3. REFUND MISMATCH/FLAGGED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-22",
            "gross_amount": 200000.0,
            "net_amount": 148000.0,
            "currency": "INR",
            "ocr_text": """
RAZORPAY SETTLEMENT REPORT
Date: August 22, 2026
Gross Revenue: INR 200,000.00
Refunds: INR 48,000.00
Platform Fee: INR 2,000.00
Payment Processing Fee: INR 2,000.00
Total Deductions: INR 52,000.00
Net Payout: INR 148,000.00
Refund Rate: 24%
            """,
            "_expected_outcome": "flagged",
            "_description": "High refund rate (24%) requires review"
        },
        
        # 4. CHARGEBACK/APPROVED
        {
            "source": "stripe",
            "settlement_date": "2026-08-23",
            "gross_amount": 300000.0,
            "net_amount": 299000.0,
            "currency": "USD",
            "ocr_text": """
STRIPE PAYOUT REPORT
Period: August 23, 2026
Gross Volume: USD 300,000.00
Chargebacks: 1 case, USD 1,000.00
Stripe Processing Fee: USD 0.00
Net Payout: USD 299,000.00
Chargeback Status: Documented
            """,
            "_expected_outcome": "approved",
            "_description": "Single documented chargeback"
        },
        
        # 5. MISSING EVIDENCE/ESCALATED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-24",
            "gross_amount": 180000.0,
            "net_amount": 165000.0,
            "currency": "INR",
            "ocr_text": """
RAZORPAY SETTLEMENT
Date: August 24, 2026
Gross: INR 180,000
Adjustments: INR 15,000
Net: INR 165,000
Note: Adjustments pending documentation
            """,
            "_expected_outcome": "escalated",
            "_description": "Undocumented adjustments, missing evidence"
        },
        
        # 6. AMOUNT DISCREPANCY/FLAGGED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-25",
            "gross_amount": 150000.0,
            "net_amount": 141000.0,
            "currency": "INR",
            "ocr_text": """
RAZORPAY SETTLEMENT REPORT
Date: August 25, 2026
Gross Revenue: INR 150,000.00
Reported Gross: INR 150,500.00
Fee: INR 9,000.00
Reported Fee: INR 8,500.00
Net Payout: INR 141,000.00
            """,
            "_expected_outcome": "flagged",
            "_description": "Amount discrepancy between gross and reported"
        },
        
        # 7. DATE DISCREPANCY/FLAGGED
        {
            "source": "paypal",
            "settlement_date": "2026-08-26",
            "gross_amount": 120000.0,
            "net_amount": 114000.0,
            "currency": "USD",
            "ocr_text": """
PAYPAL SETTLEMENT
Settlement Date: August 26, 2026
Transaction Date: August 24, 2026
Gross: USD 120,000.00
Fee: USD 6,000.00
Net: USD 114,000.00
Date Variance: 2 days
            """,
            "_expected_outcome": "flagged",
            "_description": "Date discrepancy (2 day variance)"
        },
        
        # 8. DUPLICATE/FLAGGED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-27",
            "gross_amount": 100000.0,
            "net_amount": 95000.0,
            "currency": "INR",
            "ocr_text": """
RAZORPAY SETTLEMENT REPORT
Date: August 27, 2026
Gross Revenue: INR 100,000.00
Chargeback ID: CB-2026-08-001 (Amount: INR 5,000)
Chargeback ID: CB-2026-08-001 (Amount: INR 5,000)
Fee: INR 0.00
Net Payout: INR 95,000.00
Note: Duplicate chargeback ID detected
            """,
            "_expected_outcome": "flagged",
            "_description": "Duplicate chargeback entry"
        },
        
        # 9. LOW CONFIDENCE OCR/ESCALATED
        {
            "source": "razorpay",
            "settlement_date": "2026-08-28",
            "gross_amount": 95000.0,
            "net_amount": 89500.0,
            "currency": "INR",
            "ocr_text": """
R@Z0RP@Y SETTL3M3NT R3P0RT
D@t3: @ugust 28, 2026
Gr0ss R3v3nu3: INR 95,0##.00
D3ductions: ?????
N3t P@y0ut: INR 89,500.00
[OCR QUALITY: LOW - MULTIPLE RECOGNITION ERRORS]
            """,
            "_expected_outcome": "escalated",
            "_description": "Low OCR quality, unclear deductions"
        },
        
        # 10. MULTI-GATEWAY/ESCALATED
        {
            "source": "other",
            "settlement_date": "2026-08-29",
            "gross_amount": 350000.0,
            "net_amount": 320000.0,
            "currency": "INR",
            "ocr_text": """
MULTI-GATEWAY SETTLEMENT REPORT
Date: August 29, 2026

Razorpay:
  Gross: INR 180,000
  Fee: INR 9,000
  Net: INR 171,000

Stripe:
  Gross: USD 5,000 (approx INR 100,000)
  Fee: USD 250
  Net: USD 4,750

PayPal:
  Gross: INR 70,000
  Fee: INR 2,000
  Net: INR 68,000

Total Gross: INR 350,000
Total Deductions: INR 30,000
Total Net: INR 320,000
Status: MULTI-GATEWAY - REQUIRES RECONCILIATION
            """,
            "_expected_outcome": "escalated",
            "_description": "Multi-gateway settlement, complex reconciliation"
        },
    ]
    
    return settlements


if __name__ == "__main__":
    # Quick test
    settlements = get_demo_settlements()
    print(f"✓ Loaded {len(settlements)} demo settlements")
    for i, s in enumerate(settlements, 1):
        print(f"  {i}. {s['_description']} → {s['_expected_outcome']}")
