"""Synthetic test data generator for settlements."""

from datetime import date
from dataclasses import dataclass


@dataclass
class SyntheticSettlement:
    """Represents a complete synthetic settlement with ground truth."""
    settlement_id: str
    owner_uid: str
    source: str
    settlement_date: date
    gross_amount: float
    net_amount: float
    currency: str
    deductions: list[dict]
    expected_decision: str  # "approve", "flag", "escalate"
    category: str  # "clean", "chargeback", "refund", "fee_dispute", "hold", "undocumented", etc.
    description: str


def generate_synthetic_settlements() -> list[SyntheticSettlement]:
    """Generate 5 synthetic settlements covering different scenarios."""
    
    settlements = []
    test_user_id = "test_user_123"
    
    # Settlement 1: Clean settlement - all deductions verified
    settlements.append(SyntheticSettlement(
        settlement_id="synthetic_001",
        owner_uid=test_user_id,
        source="razorpay",
        settlement_date=date(2026, 8, 1),
        gross_amount=500000.0,
        net_amount=470000.0,
        currency="INR",
        deductions=[
            {
                "type": "chargeback",
                "description": "Customer dispute - Order #12345",
                "amount": 15000.0,
                "reference_id": "CB-001",
                "reference_date": "2026-07-28",
                "confidence": 0.98,
            },
            {
                "type": "fee",
                "description": "Processing fee 2%",
                "amount": 10000.0,
                "reference_id": "FEE-001",
                "reference_date": "2026-08-01",
                "confidence": 0.95,
            },
            {
                "type": "hold",
                "description": "Reserve for disputes",
                "amount": 5000.0,
                "reference_id": None,
                "reference_date": None,
                "confidence": 0.90,
            },
        ],
        expected_decision="approve",
        category="clean",
        description="All deductions have supporting evidence and consistent amounts",
    ))
    
    # Settlement 2: Clean chargeback - passes deterministic checks
    settlements.append(SyntheticSettlement(
        settlement_id="synthetic_002",
        owner_uid=test_user_id,
        source="razorpay",
        settlement_date=date(2026, 8, 2),
        gross_amount=300000.0,
        net_amount=285000.0,
        currency="INR",
        deductions=[
            {
                "type": "chargeback",
                "description": "Customer dispute - Order #12346",
                "amount": 15000.0,  # Arithmetic: 300K - 15K = 285K ✓
                "reference_id": "CB-002",
                "reference_date": "2026-07-29",
                "confidence": 0.92,
            },
        ],
        expected_decision="approve",
        category="chargeback",
        description="Chargeback passes all deterministic checks (arithmetic valid, amount positive, confidence >= 0.5)",
    ))
    
    # Settlement 3: Refund processing
    settlements.append(SyntheticSettlement(
        settlement_id="synthetic_003",
        owner_uid=test_user_id,
        source="stripe",
        settlement_date=date(2026, 8, 3),
        gross_amount=250000.0,
        net_amount=240000.0,
        currency="INR",
        deductions=[
            {
                "type": "refund",
                "description": "Customer refund - Order #12347",
                "amount": 10000.0,
                "reference_id": "RF-001",
                "reference_date": "2026-07-30",
                "confidence": 0.96,
            },
        ],
        expected_decision="approve",
        category="refund",
        description="Refund with supporting authorization present",
    ))
    
    # Settlement 4: Multiple deductions - all pass checks
    settlements.append(SyntheticSettlement(
        settlement_id="synthetic_004",
        owner_uid=test_user_id,
        source="razorpay",
        settlement_date=date(2026, 8, 4),
        gross_amount=400000.0,
        net_amount=368000.0,
        currency="INR",
        deductions=[
            {
                "type": "fee",
                "description": "Gateway fee 2.5%",
                "amount": 12000.0,
                "reference_id": "FEE-002",
                "reference_date": "2026-08-04",
                "confidence": 0.85,
            },
            {
                "type": "chargeback",
                "description": "Processing chargeback",
                "amount": 20000.0,
                "reference_id": "CB-003",
                "reference_date": "2026-08-01",
                "confidence": 0.88,
            },
        ],
        expected_decision="approve",
        category="fee_dispute",
        description="Two deductions with valid arithmetic (400K - 12K - 20K = 368K), both pass confidence checks",
    ))
    
    # Settlement 5: High unverifiable rate triggers escalation
    settlements.append(SyntheticSettlement(
        settlement_id="synthetic_005",
        owner_uid=test_user_id,
        source="razorpay",
        settlement_date=date(2026, 8, 5),
        gross_amount=350000.0,
        net_amount=335000.0,
        currency="INR",
        deductions=[
            {
                "type": "fee",
                "description": "Processing fee",
                "amount": 10000.0,
                "reference_id": "FEE-003",
                "reference_date": "2026-08-05",
                "confidence": 0.93,
            },
            {
                "type": "other",
                "description": "Undocumented deduction",
                "amount": 5000.0,
                "reference_id": None,
                "reference_date": None,
                "confidence": 0.35,  # Below 0.5 threshold (50% of deductions unverifiable)
            },
        ],
        expected_decision="escalate",
        category="undocumented",
        description="50% of deductions unverifiable (> 30% threshold), triggers escalation for human review",
    ))
    
    return settlements


def get_settlement_test_data(settlement_id: str) -> SyntheticSettlement | None:
    """Get a specific synthetic settlement by ID."""
    for settlement in generate_synthetic_settlements():
        if settlement.settlement_id == settlement_id:
            return settlement
    return None


def create_test_settlement_request(settlement: SyntheticSettlement) -> dict:
    """Convert synthetic settlement to API request format."""
    return {
        "source": settlement.source,
        "settlementDate": settlement.settlement_date.isoformat(),
        "grossAmount": settlement.gross_amount,
        "netAmount": settlement.net_amount,
        "currency": settlement.currency,
    }


def create_test_extraction_request(settlement: SyntheticSettlement) -> dict:
    """Convert synthetic settlement deductions to extraction API request."""
    return {
        "deductions": settlement.deductions,
    }
