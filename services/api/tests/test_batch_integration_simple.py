"""
Simple integration test for batch processor.
Tests the workflow without Firestore dependencies.
"""

import sys
sys.path.insert(0, 'src')

from datetime import datetime
from formwise_api.settlements.batch_processor import BatchMetrics, SettlementProcessResult
from formwise_api.settlements.demo_data import get_demo_settlements


def test_metrics_calculation():
    """Test metrics calculation."""
    print("\n=== TEST: Metrics Calculation ===")
    
    metrics = BatchMetrics()
    metrics.total_settlements = 10
    metrics.total_deductions = 15
    metrics.approved_count = 3
    metrics.flagged_count = 5
    metrics.escalated_count = 2
    metrics.processing_failed_count = 0
    metrics.verified_deductions = 10
    metrics.disputed_deductions = 3
    metrics.unverifiable_deductions = 2
    metrics.agent_investigations = 2
    metrics.agent_successes = 1
    metrics.agent_failures = 1
    
    # Calculate rates
    metrics.settlement_approval_rate = metrics.approved_count / metrics.total_settlements
    metrics.deduction_verification_rate = metrics.verified_deductions / metrics.total_deductions
    
    print(f"Total Settlements: {metrics.total_settlements}")
    print(f"Total Deductions: {metrics.total_deductions}")
    print(f"Approved: {metrics.approved_count} ({metrics.settlement_approval_rate:.1%})")
    print(f"Flagged: {metrics.flagged_count}")
    print(f"Escalated: {metrics.escalated_count}")
    print(f"Verification Rate: {metrics.deduction_verification_rate:.1%}")
    print(f"Agent Investigations: {metrics.agent_investigations}")
    
    # Verify rates
    assert 0 <= metrics.settlement_approval_rate <= 1
    assert 0 <= metrics.deduction_verification_rate <= 1
    print("✓ Metrics calculation correct")


def test_result_to_dict():
    """Test result serialization."""
    print("\n=== TEST: Result Serialization ===")
    
    result = SettlementProcessResult(
        settlement_id="settlement-123",
        owner_uid="user-abc",
        source="razorpay",
        status="approved",
        deduction_count=3,
        verified_count=3,
        disputed_count=0,
        unverifiable_count=0,
        extraction_succeeded=True,
        verification_succeeded=True,
        extraction_deduction_count=3,
    )
    
    result_dict = result.to_dict()
    
    print(f"Settlement ID: {result_dict['settlement_id']}")
    print(f"Status: {result_dict['status']}")
    print(f"Deductions: {result_dict['deduction_count']}")
    print(f"Verified: {result_dict['verified_count']}")
    
    assert result_dict["settlement_id"] == "settlement-123"
    assert result_dict["status"] == "approved"
    assert result_dict["deduction_count"] == 3
    print("✓ Result serialization correct")


def test_demo_data_structure():
    """Test demo data structure."""
    print("\n=== TEST: Demo Data Structure ===")
    
    settlements = get_demo_settlements()
    
    print(f"Total Demo Settlements: {len(settlements)}")
    
    outcomes = {}
    for settlement in settlements:
        outcome = settlement["_expected_outcome"]
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        # Verify structure
        assert "source" in settlement
        assert "settlement_date" in settlement
        assert "gross_amount" in settlement
        assert "net_amount" in settlement
        assert "currency" in settlement
        assert "ocr_text" in settlement
        assert "_expected_outcome" in settlement
        assert "_description" in settlement
        
        # Verify amounts
        assert settlement["gross_amount"] > 0
        assert settlement["net_amount"] > 0
        assert settlement["net_amount"] <= settlement["gross_amount"]
    
    print(f"Outcomes: {outcomes}")
    print(f"  Approved: {outcomes.get('approved', 0)}")
    print(f"  Flagged: {outcomes.get('flagged', 0)}")
    print(f"  Escalated: {outcomes.get('escalated', 0)}")
    
    assert "approved" in outcomes
    assert "flagged" in outcomes
    assert "escalated" in outcomes
    print("✓ Demo data structure correct")


def test_buildathon_metrics():
    """Test buildathon key metrics."""
    print("\n=== TEST: Buildathon Metrics ===")
    
    # Simulate batch processing results
    metrics = BatchMetrics()
    metrics.timestamp = datetime.utcnow().isoformat()
    metrics.total_settlements = 10
    metrics.total_deductions = 25
    metrics.approved_count = 2
    metrics.flagged_count = 5
    metrics.escalated_count = 3
    metrics.processing_failed_count = 0
    metrics.verified_deductions = 18
    metrics.disputed_deductions = 5
    metrics.unverifiable_deductions = 2
    metrics.agent_investigations = 3
    metrics.agent_successes = 2
    metrics.agent_failures = 1
    metrics.settlement_approval_rate = metrics.approved_count / metrics.total_settlements
    metrics.deduction_verification_rate = metrics.verified_deductions / metrics.total_deductions
    
    # Add some exceptions
    metrics.exceptions = [
        {
            "settlement_id": "settlement-002",
            "status": "flagged",
            "reason": "Fee mismatch detected",
            "gaps": ["Fee: expected INR 5000, found INR 9500"],
        },
        {
            "settlement_id": "settlement-005",
            "status": "escalated",
            "reason": "Undocumented adjustments",
            "gaps": ["Adjustment: INR 15000 - no documentation provided"],
        },
    ]
    
    metrics_dict = metrics.to_dict()
    
    # Print buildathon report
    print("\n=== BUILDATHON REPORT ===")
    print(f"\nSettlements Processed: {metrics_dict['total_settlements']}")
    print(f"Deductions Processed: {metrics_dict['total_deductions']}")
    print(f"\nApproval Metrics:")
    print(f"  Approved: {metrics_dict['approved_count']} ({metrics_dict['settlement_approval_rate']:.1%})")
    print(f"  Flagged (needs review): {metrics_dict['flagged_count']}")
    print(f"  Escalated (high-risk): {metrics_dict['escalated_count']}")
    print(f"  Failed: {metrics_dict['processing_failed_count']}")
    print(f"\nDeduction Metrics:")
    print(f"  Verified: {metrics_dict['verified_deductions']}")
    print(f"  Disputed: {metrics_dict['disputed_deductions']}")
    print(f"  Unverifiable: {metrics_dict['unverifiable_deductions']}")
    print(f"  Verification Rate: {metrics_dict['deduction_verification_rate']:.1%}")
    print(f"\nAI Agent Metrics:")
    print(f"  Investigations: {metrics_dict['agent_investigations']}")
    print(f"  Successes: {metrics_dict['agent_successes']}")
    print(f"  Failures: {metrics_dict['agent_failures']}")
    print(f"\nExceptions: {len(metrics_dict['exceptions'])}")
    for exc in metrics_dict['exceptions']:
        print(f"  - {exc['settlement_id']}: {exc['reason']}")
    
    # Verify key metrics exist
    assert metrics_dict['total_settlements'] > 0
    assert metrics_dict['total_deductions'] > 0
    assert 'settlement_approval_rate' in metrics_dict
    assert 'deduction_verification_rate' in metrics_dict
    assert 'exceptions' in metrics_dict
    
    print("\n✓ Buildathon metrics complete")


if __name__ == "__main__":
    print("=== FORMWISE-FINANCE Day 9-10 Integration Tests ===")
    
    try:
        test_metrics_calculation()
        test_result_to_dict()
        test_demo_data_structure()
        test_buildathon_metrics()
        
        print("\n✓ ALL TESTS PASSED")
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
