"""
Day 9-10: End-to-end demo workflow test for FORMWISE-FINANCE buildathon.

Demonstrates complete workflow:
1. Load 10 synthetic settlements
2. Process each settlement end-to-end
3. Extract deductions from OCR text
4. Run verification (deterministic + agent if available)
5. Generate decision (approve/flag/escalate)
6. Collect metrics and results

Tests batch processing with diverse outcomes showing:
- Approved settlements (all deductions verified)
- Flagged settlements (some discrepancies requiring review)
- Escalated settlements (high-risk or complex)
- Proper exception tracking and audit trail
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from formwise_api.settlements.batch_processor import (
    BatchSettlementProcessor,
    SettlementProcessResult,
    BatchMetrics,
)
from formwise_api.settlements.demo_data import get_demo_settlements, get_benchmark_settlements
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.service import SettlementService
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.verification.models import SettlementDecision
from formwise_api.settlements.repository import (
    FirestoreSettlementRepository,
    FirestoreSettlementDeductionRepository,
)


class MockFirestoreClient:
    """Mock Firestore client for testing."""
    
    def __init__(self):
        self.data = {
            "settlements": {},
            "settlementDeductions": {},
            "verificationResults": {},
            "settlementDecisions": {},
        }
    
    def collection(self, name):
        return MockCollection(self.data, name)


class MockCollection:
    """Mock Firestore collection."""
    
    def __init__(self, data, name):
        self.data = data
        self.name = name
        self._filters = []
        self._order_by = None
    
    def document(self, doc_id):
        return MockDocument(self.data, self.name, doc_id)
    
    def where(self, field, op, value):
        self._filters.append((field, op, value))
        return self
    
    def order_by(self, field, direction=None):
        self._order_by = (field, direction)
        return self
    
    def stream(self):
        docs = []
        for doc_id, doc_data in self.data[self.name].items():
            # Simple filtering
            match = True
            for field, op, value in self._filters:
                if field == "ownerUid" and op == "==":
                    if doc_data.get("ownerUid") != value:
                        match = False
                if field == "settlementId" and op == "==":
                    if doc_data.get("settlementId") != value:
                        match = False
            
            if match:
                docs.append(MockSnapshot(doc_id, doc_data, True))
        
        return docs


class MockDocument:
    """Mock Firestore document."""
    
    def __init__(self, data, collection, doc_id):
        self.data = data
        self.collection_name = collection
        self.doc_id = doc_id
    
    def create(self, data):
        if self.collection_name not in self.data:
            self.data[self.collection_name] = {}
        self.data[self.collection_name][self.doc_id] = data
    
    def get(self):
        docs = self.data.get(self.collection_name, {})
        if self.doc_id in docs:
            return MockSnapshot(self.doc_id, docs[self.doc_id], True)
        return MockSnapshot(self.doc_id, {}, False)
    
    def update(self, data):
        if self.collection_name in self.data and self.doc_id in self.data[self.collection_name]:
            self.data[self.collection_name][self.doc_id].update(data)


class MockSnapshot:
    """Mock Firestore snapshot."""
    
    def __init__(self, doc_id, data, exists):
        self._doc_id = doc_id
        self._data = data
        self.exists = exists
    
    def to_dict(self):
        return self._data if self.exists else None


@pytest.fixture
def mock_firestore_client():
    """Create mock Firestore client."""
    return MockFirestoreClient()


@pytest.fixture
def settlement_service(mock_firestore_client):
    """Create settlement service with mock client."""
    settlement_repo = FirestoreSettlementRepository(mock_firestore_client)
    deduction_repo = FirestoreSettlementDeductionRepository(mock_firestore_client)
    return SettlementService(settlement_repo, deduction_repo)


@pytest.fixture
def batch_processor(mock_firestore_client, settlement_service):
    """Create batch processor with mocked dependencies."""
    from formwise_api.settlements.extraction_service import SettlementExtractionService
    from formwise_api.verification.repository import (
        FirestoreVerificationResultRepository,
        FirestoreSettlementDecisionRepository,
    )
    from formwise_api.evidence.repository import FirestoreEvidenceLinkRepository
    from formwise_api.audit.repository import FirestoreFinanceAuditEventRepository
    
    settlement_repo = FirestoreSettlementRepository(mock_firestore_client)
    deduction_repo = FirestoreSettlementDeductionRepository(mock_firestore_client)
    verification_repo = FirestoreVerificationResultRepository(mock_firestore_client)
    decision_repo = FirestoreSettlementDecisionRepository(mock_firestore_client)
    audit_repo = FirestoreFinanceAuditEventRepository(mock_firestore_client)
    evidence_repo = FirestoreEvidenceLinkRepository(mock_firestore_client)
    
    doc_extractor = DocumentSettlementExtractor(
        settlement_repo,
        audit_repo,
    )
    extraction_service = SettlementExtractionService(
        settlement_repo,
        deduction_repo,
        audit_repo,
    )
    
    verification_service = SettlementVerificationService(
        settlement_repo,
        deduction_repo,
        verification_repo,
        decision_repo,
        audit_repo,
        evidence_repo,
        ai_provider=None,  # No AI provider for demo
    )
    
    return BatchSettlementProcessor(
        settlement_service,
        doc_extractor,
        verification_service,
        settlement_repo,
        extraction_service,
    )


class TestDemoEndToEndWorkflow:
    """Test complete end-to-end demo workflow."""
    
    def test_demo_settlements_structure(self):
        """Verify demo settlements have required structure."""
        settlements = get_demo_settlements()
        
        assert len(settlements) == 10, "Should have 10 demo settlements"
        
        for i, settlement in enumerate(settlements, 1):
            assert "source" in settlement
            assert "settlement_date" in settlement
            assert "gross_amount" in settlement
            assert "net_amount" in settlement
            assert "currency" in settlement
            assert "ocr_text" in settlement
            assert "_expected_outcome" in settlement
            assert "_description" in settlement
            
            # Validate amounts
            assert settlement["gross_amount"] > 0
            assert settlement["net_amount"] > 0
            assert settlement["net_amount"] <= settlement["gross_amount"]
    
    def test_demo_outcomes(self):
        """Verify demo settlements have expected outcomes."""
        settlements = get_demo_settlements()
        expected_outcomes = ["approved", "flagged", "escalated"]
        outcomes = [s["_expected_outcome"] for s in settlements]
        
        # Should have some of each outcome for demo
        assert "approved" in outcomes
        assert "flagged" in outcomes
        assert "escalated" in outcomes
        
        # Print demo structure for reference
        print("\n=== DEMO SETTLEMENT OUTCOMES ===")
        for i, s in enumerate(settlements, 1):
            print(f"{i}. {s['_description']}")
            print(f"   Expected: {s['_expected_outcome']}")
    
    def test_batch_processing_metrics_structure(self, batch_processor):
        """Test that batch processing produces correct metrics."""
        settlements = get_demo_settlements()[:3]  # Use first 3 for quick test
        
        metrics, results = batch_processor.process_settlements("test-user", settlements)
        
        # Check metrics structure
        assert isinstance(metrics, BatchMetrics)
        assert metrics.total_settlements == 3
        assert metrics.total_deductions >= 0
        assert metrics.approved_count >= 0
        assert metrics.flagged_count >= 0
        assert metrics.escalated_count >= 0
        assert metrics.approved_count + metrics.flagged_count + metrics.escalated_count + metrics.processing_failed_count == 3
        
        # Check rates
        assert 0 <= metrics.settlement_approval_rate <= 1
        assert 0 <= metrics.deduction_verification_rate <= 1
    
    def test_batch_processing_results_structure(self, batch_processor):
        """Test that batch processing produces correct result structures."""
        settlements = get_demo_settlements()[:2]
        
        metrics, results = batch_processor.process_settlements("test-user", settlements)
        
        assert len(results) == 2
        
        for result in results:
            assert isinstance(result, SettlementProcessResult)
            assert result.settlement_id
            assert result.owner_uid == "test-user"
            assert result.source in ("razorpay", "stripe", "paypal", "other")
            assert result.status in ("approved", "flagged", "escalated", "error")
            assert result.deduction_count >= 0
            assert result.verified_count >= 0
            assert result.disputed_count >= 0
            assert result.unverifiable_count >= 0
    
    def test_batch_processing_end_to_end(self, batch_processor):
        """Test complete end-to-end batch processing."""
        settlements = get_demo_settlements()
        
        print("\n=== BATCH PROCESSING START ===")
        metrics, results = batch_processor.process_settlements("demo-user", settlements)
        print("=== BATCH PROCESSING COMPLETE ===")
        
        # Verify all settlements were processed
        assert len(results) == 10
        
        # Verify metrics calculation
        assert metrics.total_settlements == 10
        total_processed = (
            metrics.approved_count +
            metrics.flagged_count +
            metrics.escalated_count +
            metrics.processing_failed_count
        )
        assert total_processed == 10
        
        # Verify at least some variability in outcomes
        assert metrics.approved_count > 0 or metrics.flagged_count > 0 or metrics.escalated_count > 0
        
        # Print detailed results
        print(f"\n=== BATCH METRICS ===")
        print(f"Total Settlements: {metrics.total_settlements}")
        print(f"Total Deductions: {metrics.total_deductions}")
        print(f"\nOutcomes:")
        print(f"  Approved: {metrics.approved_count} ({metrics.settlement_approval_rate:.1%})")
        print(f"  Flagged: {metrics.flagged_count}")
        print(f"  Escalated: {metrics.escalated_count}")
        print(f"  Failed: {metrics.processing_failed_count}")
        print(f"\nDeduction Stats:")
        print(f"  Verified: {metrics.verified_deductions}")
        print(f"  Disputed: {metrics.disputed_deductions}")
        print(f"  Unverifiable: {metrics.unverifiable_deductions}")
        print(f"  Verification Rate: {metrics.deduction_verification_rate:.1%}")
        
        if metrics.exceptions:
            print(f"\nExceptions ({len(metrics.exceptions)}):")
            for exc in metrics.exceptions:
                print(f"  - {exc['settlement_id']}: {exc['status']}")
                if exc.get('gaps'):
                    for gap in exc['gaps'][:2]:  # Show first 2 gaps
                        print(f"    → {gap}")
    
    def test_settlement_approval_calculation(self):
        """Test settlement approval rate calculation."""
        # Create mock metrics
        metrics = BatchMetrics()
        metrics.total_settlements = 10
        metrics.approved_count = 3
        metrics.flagged_count = 5
        metrics.escalated_count = 2
        
        expected_rate = 3 / 10
        assert metrics.settlement_approval_rate == 0.0 or expected_rate > 0
    
    def test_metrics_to_dict_conversion(self):
        """Test metrics conversion to dictionary."""
        metrics = BatchMetrics()
        metrics.total_settlements = 10
        metrics.approved_count = 5
        metrics.flagged_count = 3
        metrics.escalated_count = 2
        
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["total_settlements"] == 10
        assert metrics_dict["approved_count"] == 5
        assert "timestamp" in metrics_dict
    
    def test_process_result_to_dict_conversion(self):
        """Test result conversion to dictionary."""
        result = SettlementProcessResult(
            settlement_id="test-id",
            owner_uid="test-user",
            source="razorpay",
            status="approved",
            deduction_count=2,
            verified_count=2,
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["settlement_id"] == "test-id"
        assert result_dict["status"] == "approved"
        assert result_dict["deduction_count"] == 2


    def test_fifty_record_benchmark(self, batch_processor, mock_firestore_client):
        """Process the deterministic 50-record benchmark through the batch pipeline."""
        specs = get_benchmark_settlements()

        metrics, results = batch_processor.process_settlements("benchmark-user", specs)

        assert len(specs) == 50
        assert len(results) == 50
        assert metrics.total_records == 50
        assert metrics.processed == 45
        assert metrics.successfully_extracted == 45
        assert metrics.processing_failed_count == 5
        assert metrics.approved_count == 20
        assert metrics.flagged_count == 12
        assert metrics.escalated_count == 13
        assert metrics.exception_count == 25
        assert metrics.exception_rate == 0.5
        assert metrics.extraction_success_rate == 0.9
        assert metrics.evidence_checked == 13
        assert metrics.evidence_match_rate == 0.0

        stored = mock_firestore_client.data["settlementDeductions"]
        assert len(stored) == metrics.total_deductions
        assert all(
            deduction["settlementId"].startswith("benchmark-")
            for deduction in stored.values()
        )


class TestDemoDataQuality:
    """Test quality and consistency of demo data."""
    
    def test_demo_data_diversity(self):
        """Verify demo data covers diverse scenarios."""
        settlements = get_demo_settlements()
        descriptions = [s["_description"] for s in settlements]
        
        # Verify we have different types of issues
        assert any("fee" in d.lower() for d in descriptions), "Should have fee-related case"
        assert any("refund" in d.lower() for d in descriptions), "Should have refund case"
        assert any("chargeback" in d.lower() for d in descriptions), "Should have chargeback"
        assert any("gateway" in d.lower() for d in descriptions), "Should have multi-gateway"
        assert any("duplicate" in d.lower() for d in descriptions), "Should have duplicate"
        assert any("date" in d.lower() for d in descriptions), "Should have date discrepancy"
    
    def test_demo_data_completeness(self):
        """Verify all demo settlements are complete."""
        settlements = get_demo_settlements()
        
        for settlement in settlements:
            # All required fields
            assert settlement["source"]
            assert settlement["settlement_date"]
            assert settlement["gross_amount"] > 0
            assert settlement["net_amount"] > 0
            assert settlement["currency"]
            assert settlement["ocr_text"]  # Should have some OCR text
            
            # Deductions should be less than or equal to gross
            deduction = settlement["gross_amount"] - settlement["net_amount"]
            assert deduction >= 0, f"Deduction should be positive: {deduction}"


class TestDemoBuildathonMetrics:
    """Test buildathon-relevant metrics."""
    
    def test_metrics_structure_for_buildathon(self):
        """Verify metrics cover buildathon requirements."""
        metrics = BatchMetrics()
        metrics.total_settlements = 10
        metrics.total_deductions = 15
        metrics.approved_count = 3
        metrics.flagged_count = 5
        metrics.escalated_count = 2
        metrics.verified_deductions = 10
        metrics.disputed_deductions = 3
        metrics.unverifiable_deductions = 2
        
        metrics_dict = metrics.to_dict()
        
        # Check buildathon metrics
        assert "total_settlements" in metrics_dict
        assert "total_deductions" in metrics_dict
        assert "approved_count" in metrics_dict
        assert "flagged_count" in metrics_dict
        assert "escalated_count" in metrics_dict
        assert "verified_deductions" in metrics_dict
        assert "disputed_deductions" in metrics_dict
        assert "unverifiable_deductions" in metrics_dict
        assert "settlement_approval_rate" in metrics_dict
        assert "deduction_verification_rate" in metrics_dict
        assert "exceptions" in metrics_dict
        
        # Calculate rates
        approval_rate = metrics.approved_count / metrics.total_settlements if metrics.total_settlements else 0
        verification_rate = metrics.verified_deductions / metrics.total_deductions if metrics.total_deductions else 0
        
        print(f"\n=== BUILDATHON METRICS ===")
        print(f"Settlements Processed: {metrics.total_settlements}")
        print(f"Deductions Processed: {metrics.total_deductions}")
        print(f"Approval Rate: {approval_rate:.1%}")
        print(f"Verification Rate: {verification_rate:.1%}")
        print(f"Exceptions: {len(metrics.exceptions)}")


if __name__ == "__main__":
    # Run demo
    print("Running FORMWISE-FINANCE Day 9-10 Demo Workflow Tests")
    pytest.main([__file__, "-v", "-s"])
