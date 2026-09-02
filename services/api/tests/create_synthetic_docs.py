"""Create synthetic test settlement documents for end-to-end testing.

These are text-based "PDFs" that simulate real settlement documents.
In production, these would be actual PDF files processed by PaddleOCR.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta


def create_test_settlement_razorpay():
    """Create synthetic Razorpay settlement document."""
    return """
================================================================================
                    RAZORPAY SETTLEMENT REPORT
================================================================================

Settlement ID: RZP-2026-08-15-001
Settlement Date: 2026-08-15
Report Generated: 2026-08-15 18:30:00 UTC
Period: 2026-08-01 to 2026-08-15

================================================================================
MERCHANT ACCOUNT INFORMATION
================================================================================

Merchant ID: acc_razorpay_demo_001
Business Name: Example E-commerce Store
Email: merchant@example.com
Phone: +91-98765-43210
Account Status: Active (Approved)
Account Currency: INR

================================================================================
SETTLEMENT SUMMARY
================================================================================

Settlement Duration: 15 days
Total Transactions: 5,234 transactions
Total Volume: INR 1,250,000.00
Average Transaction Value: INR 238.82
Successful Transactions: 5,215 (99.64%)
Failed Transactions: 19 (0.36%)

================================================================================
FINANCIAL BREAKDOWN
================================================================================

Gross Settlement Amount: INR 1,200,000.00

DEDUCTIONS:
-----------
1. Processing Fees (2.0% of volume)
   Amount: INR 24,000.00
   Details: Standard payment gateway processing fee

2. Refunds Processed
   Count: 15 refunds
   Amount: INR 18,500.00
   Reason: Customer returns, cancellations

3. Chargebacks
   Count: 2 chargebacks
   Amount: INR 3,200.00
   Reference: CB-20260808-001, CB-20260809-001
   Details: Under investigation

4. Platform Hold / Reserve
   Amount: INR 5,000.00
   Reason: Monthly risk reserve hold
   Duration: 30 days

5. Adjustments / Reconciliation
   Amount: INR 1,300.00
   Details: Previous month rectifications, bonus adjustments

TOTAL DEDUCTIONS: INR 52,000.00

================================================================================
NET SETTLEMENT
================================================================================

Net Payout Amount: INR 1,148,000.00
Payout Status: APPROVED FOR SETTLEMENT
Expected Settlement Date: 2026-08-17
Settlement Method: NEFT Bank Transfer

Bank Account Details:
Account Holder: Example E-commerce Store
Bank Name: HDFC Bank Limited
Account Number: ****5678
IFSC Code: HDFC0000001
Account Type: Current Account

Previous Balance (from 2026-07-31): INR 125,000.00
Current Settlement: INR 1,148,000.00
Available Balance (after settlement): INR 1,273,000.00

================================================================================
DEDUCTION DETAILS
================================================================================

PROCESSING FEES
Fee Type: Transaction Processing Fee
Rate: 2.0% of gross volume
Calculation: 1,250,000 * 0.02 = 25,000
Adjustment: Promo credit applied: -1,000
Final Amount: INR 24,000.00
Status: APPROVED

REFUNDS
Total Refunds Processed: INR 18,500.00
Sample Refund Transactions:
  - Order #12345 (2026-08-10): INR 2,500.00
  - Order #12346 (2026-08-11): INR 3,250.00
  - Order #12347 (2026-08-12): INR 1,800.00
  [... 12 more refunds ...]
Refund Rate: 1.48% of gross volume
Status: NORMAL

CHARGEBACKS
Chargebacks Reported: 2
Chargeback Amount: INR 3,200.00
  - Chargeback ID: CB-20260808-001
    Amount: INR 2,000.00
    Transaction: TXN-20260805-00234
    Reason: Customer dispute
    Status: Under investigation
    
  - Chargeback ID: CB-20260809-001
    Amount: INR 1,200.00
    Transaction: TXN-20260806-00891
    Reason: Unauthorized transaction claim
    Status: Evidence submitted, awaiting decision

Chargeback Rate: 0.26% of gross volume
Total Loss: INR 3,200.00

================================================================================
COMPLIANCE & AUDIT
================================================================================

3DS Compliance: 98.2%
Settlement Verification: PASSED
Reconciliation Status: COMPLETE
Fraud Score: LOW (3/100)
Risk Assessment: NORMAL

Settlement Statement Validity:
Merchant Signature (Digital): Verified
Settlement Authority: Razorpay Payments Pvt. Ltd.
Certification: This settlement has been verified against transaction logs

================================================================================
SETTLEMENT CONFIRMATION
================================================================================

Settlement Approved By: System Administrator (auto-approved)
Approval Date: 2026-08-15 18:30:00 UTC
Approval Authority: Razorpay Settlements System

Next Settlement: 2026-08-22 (7 days)
Next Expected Amount: INR 950,000.00 (estimated)

For disputes or questions contact: settlements@razorpay.com
Settlement Reference: RZP-2026-08-15-001-APPROVED

================================================================================
END OF SETTLEMENT REPORT
================================================================================
"""


def create_test_settlement_stripe():
    """Create synthetic Stripe settlement document."""
    return """
================================================================================
                        STRIPE PAYOUT STATEMENT
================================================================================

Payout ID: po_1Mqr3JIeNXXXXXXXXXXXXXX
Payout Date: 2026-08-31
Statement Period: 2026-08-01 to 2026-08-31
Currency: USD

================================================================================
ACCOUNT DETAILS
================================================================================

Account ID: acct_stripe_demo_001
Account Holder: Example SaaS Company
Email: finance@example-saas.com
Timezone: America/New_York
Account Status: Live

================================================================================
PAYOUT SUMMARY
================================================================================

Opening Balance: USD 42,500.00
Transactions Processed: 3,847
Total Volume: USD 875,000.00

PAYOUT BREAKDOWN:
-----------------
Gross Volume: USD 875,000.00
Processing Fees (2.9%): USD 25,375.00
Refunds: USD 12,000.00
Disputes: USD 1,500.00

Net Payout: USD 836,125.00

================================================================================
PAYOUT DETAILS
================================================================================

STRIPE PROCESSING FEES
Base Rate: 2.9% + $0.30 per transaction
Calculated Fee: USD 25,375.00
Status: APPROVED

REFUNDS ISSUED
Total: USD 12,000.00
Count: 8 refunds
Average Refund: USD 1,500.00
Refund Rate: 1.37%
Status: NORMAL

DISPUTES
Active Disputes: 1
Dispute Amount: USD 1,500.00
Dispute ID: dp_1Mqr3JIEXXXXXXXXXX
Reason: Product not received
Status: Under review
Days Remaining: 19 days

================================================================================
PAYOUT APPROVAL
================================================================================

Payout Status: APPROVED
Estimated Transfer Date: 2026-09-02
Transfer Method: ACH Bank Transfer

Bank Information:
Account Holder: Example SaaS Company
Bank: Wells Fargo Bank
Account Type: Checking
Account Number: ****6789
Routing Number: ****1234

================================================================================
END OF PAYOUT STATEMENT
================================================================================
"""


def create_test_evidence_chargeback():
    """Create synthetic chargeback evidence document."""
    return """
================================================================================
                    CHARGEBACK EVIDENCE DOCUMENTATION
================================================================================

Chargeback ID: CB-20260808-001
Report Date: 2026-08-08
Document Type: Chargeback Defense Evidence

================================================================================
DISPUTE INFORMATION
================================================================================

Dispute Amount: INR 2,000.00
Dispute Type: Unauthorized Transaction
Dispute Code: 4855

Transaction Details:
  Transaction ID: TXN-20260805-00234
  Date: 2026-08-05
  Amount: INR 2,000.00
  Card Last 4: 4242
  Merchant: Example E-commerce Store

Customer Information:
  Email: customer@example.com
  Phone: XXXXX45670
  Previous Transactions: 5 successful transactions
  Account Age: 2 years

================================================================================
DEFENSE EVIDENCE
================================================================================

1. PAYMENT CONFIRMATION
   - Order confirmation sent to customer at 2026-08-05 16:30:00 UTC
   - Subject: "Order #12345 Confirmed - INR 2,000.00"
   - Email delivered successfully
   - Click-through tracking: Yes (customer opened email)

2. DELIVERY CONFIRMATION
   - Delivery Date: 2026-08-06
   - Tracking Number: TRACK20260806789
   - Delivery Status: Delivered to customer address
   - Signature: Electronic signature obtained
   - Photo Evidence: Yes (delivery photo available)

3. CUSTOMER COMMUNICATION
   - Customer service ticket: TKT-20260806-0234
   - Date: 2026-08-06
   - Status: Customer confirmed delivery
   - Communication: "Product received in excellent condition"

4. SERVICE USAGE
   - Account activation: 2026-08-05 17:00:00 UTC
   - Service usage logs: 145 API calls
   - Data downloaded: 512 MB
   - No service issues reported

================================================================================
SUPPORTING DOCUMENTS ATTACHED
================================================================================

1. order_confirmation_email.pdf (attached)
2. delivery_tracking_proof.pdf (attached)
3. delivery_photo_20260806.pdf (attached)
4. customer_service_ticket.pdf (attached)
5. system_logs_excerpt.pdf (attached)

================================================================================
CONCLUSION
================================================================================

This chargeback appears to be fraudulent or a dispute initiated in error.

Supporting Evidence Summary:
✓ Proof of delivery to customer address
✓ Customer confirmation of receipt
✓ Evidence of service usage
✓ Communication history

Recommendation: DEFEND CHARGEBACK

Status: Evidence submitted to acquirer
Expected Response: 2026-08-20

================================================================================
"""


def create_test_evidence_refund():
    """Create synthetic refund receipt document."""
    return """
================================================================================
                         REFUND RECEIPT & PROOF
================================================================================

Refund ID: REF-20260810-00234
Refund Date: 2026-08-10
Refund Amount: INR 2,500.00
Refund Status: COMPLETED

================================================================================
ORIGINAL TRANSACTION
================================================================================

Order ID: ORD-20260805-12345
Transaction ID: TXN-20260805-00234
Purchase Date: 2026-08-05
Purchase Amount: INR 2,500.00

Product Purchased: Product XYZ Pro License
Quantity: 1
Unit Price: INR 2,500.00

Customer:
  Name: John Doe
  Email: john@example.com
  Customer ID: CUST-00234

================================================================================
REFUND DETAILS
================================================================================

Refund Initiated: 2026-08-10 10:30:00 UTC
Refund Reason: Customer requested cancellation
Refund Amount: INR 2,500.00
Refund Method: Original payment method
Refund Status: COMPLETED
Refund Processed Date: 2026-08-11

Refund Transaction ID: TXN-20260811-REF-00234
Settlement Reference: RZP-2026-08-15-001

Refund Confirmation:
✓ Amount: INR 2,500.00
✓ Card: ****4242
✓ Processing Time: 2 days
✓ Status: Successfully credited to customer account

================================================================================
CUSTOMER COMMUNICATION
================================================================================

Refund notification sent to: john@example.com
Subject: "Your refund of INR 2,500.00 has been processed"
Date: 2026-08-11 08:00:00 UTC
Status: Email delivered and opened

Customer Confirmation: Yes
Customer Acknowledgment: "Thanks for the refund, received in my account"

================================================================================
END OF REFUND RECEIPT
================================================================================
"""


def create_all_test_documents():
    """Create all test documents."""
    docs_dir = Path('/tmp/test_settlement_docs')
    docs_dir.mkdir(exist_ok=True)

    # Settlement documents
    with open(docs_dir / 'razorpay_settlement_aug.txt', 'w') as f:
        f.write(create_test_settlement_razorpay())
    
    with open(docs_dir / 'stripe_settlement_aug.txt', 'w') as f:
        f.write(create_test_settlement_stripe())
    
    # Evidence documents
    with open(docs_dir / 'chargeback_evidence_cb001.txt', 'w') as f:
        f.write(create_test_evidence_chargeback())
    
    with open(docs_dir / 'refund_receipt_2026_08_10.txt', 'w') as f:
        f.write(create_test_evidence_refund())
    
    print(f"✅ Created test documents in {docs_dir}")
    print(f"   - razorpay_settlement_aug.txt")
    print(f"   - stripe_settlement_aug.txt")
    print(f"   - chargeback_evidence_cb001.txt")
    print(f"   - refund_receipt_2026_08_10.txt")
    
    return docs_dir


if __name__ == '__main__':
    docs_dir = create_all_test_documents()
    
    # Print sample OCR text
    print("\n" + "="*80)
    print("SAMPLE OCR TEXT FROM RAZORPAY SETTLEMENT")
    print("="*80)
    with open(docs_dir / 'razorpay_settlement_aug.txt', 'r') as f:
        content = f.read()
        print(content[:800] + "...\n[truncated]")
