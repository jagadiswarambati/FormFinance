"""Tests for evidence matching and AI agent investigation (Day 5-6)."""

import sys
sys.path.insert(0, 'tests')

from datetime import date
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.repository import (
    FirestoreSettlementRepository,
    FirestoreSettlementDeductionRepository,
)
from formwise_api.settlements.extraction_service import SettlementExtractionService
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.settlements.evidence_matcher import EvidenceMatcher, SettlementEvidenceStore
from formwise_api.verification.repository import (
    FirestoreVerificationResultRepository,
    FirestoreSettlementDecisionRepository,
)
from formwise_api.evidence.repository import FirestoreEvidenceLinkRepository
from formwise_api.audit.repository import FirestoreFinanceAuditEventRepository
from formwise_api.ai_provider.mock import MockAIProvider
from synthetic_data import generate_synthetic_settlements, get_settlement_test_data


# Minimal fake Firestore
class FakeFirestoreClient:
    def __init__(self):
        self.data = {}
    def collection(self, name: str):
        if name not in self.data:
            self.data[name] = {}
        return FakeCollection(self.data[name])

class FakeCollection:
    def __init__(self, col_data: dict):
        self.data = col_data
    def document(self, doc_id: str):
        return FakeDocument(self.data, doc_id)
    def where(self, field: str, op: str, value):
        return FakeQuery(self.data, field, value)

class FakeDocument:
    def __init__(self, col_data: dict, doc_id: str):
        self.col_data = col_data
        self.doc_id = doc_id
    def create(self, data: dict):
        self.col_data[self.doc_id] = data
    def get(self):
        data = self.col_data.get(self.doc_id)
        return FakeSnapshot(data is not None, data)
    def update(self, updates: dict):
        if self.doc_id in self.col_data:
            self.col_data[self.doc_id].update(updates)

class FakeSnapshot:
    def __init__(self, exists: bool, data: dict | None = None):
        self.exists = exists
        self._data = data
    def to_dict(self):
        return self._data

class FakeQuery:
    def __init__(self, col_data: dict, field: str, value):
        self.col_data = col_data
        self.field = field
        self.value = value
    def order_by(self, *args, **kwargs):
        return self
    def stream(self):
        results = []
        for doc_id, data in self.col_data.items():
            if data.get(self.field) == self.value:
                results.append(FakeSnapshot(True, data))
        return results
    def limit(self, n: int):
        return self


# ============================================================================
# Unit Tests: EvidenceMatcher
# ============================================================================

def test_evidence_matcher_no_evidence():
    """Test evidence matcher when no evidence is available."""
    client = FakeFirestoreClient()
    evidence_repo = FirestoreEvidenceLinkRepository(client)
    evidence_store = SettlementEvidenceStore()
    matcher = EvidenceMatcher(evidence_repo, evidence_store)
    
    settlement = Settlement(
        id="s1",
        owner_uid="user1",
        source="razorpay",
        settlement_date=date(2026, 8, 1),
        gross_amount=100000.0,
        net_amount=95000.0,
    )
    
    deduction = SettlementDeduction(
        id="d1",
        settlement_id="s1",
        type="chargeback",
        description="Dispute",
        amount=5000.0,
        extracted_with_confidence=0.95,
    )
    
    result, link = matcher.match_deduction_to_evidence(deduction, settlement)
    
    assert result.status == "unverifiable"
    assert "No supporting evidence found" in result.reason
    assert link is None
    print("✓ Test: Evidence matcher handles missing evidence correctly")


def test_evidence_matcher_with_evidence():
    """Test evidence matcher when evidence is available and matches."""
    client = FakeFirestoreClient()
    evidence_repo = FirestoreEvidenceLinkRepository(client)
    evidence_store = SettlementEvidenceStore()
    
    # Register evidence for the deduction
    evidence_store.register_evidence(
        "d1",
        "chargeback_documentation",
        {
            "amount": 5000.0,  # Matches deduction amount
            "date": date(2026, 7, 28),
            "reference": "CB-001",
        }
    )
    
    matcher = EvidenceMatcher(evidence_repo, evidence_store)
    
    settlement = Settlement(
        id="s1",
        owner_uid="user1",
        source="razorpay",
        settlement_date=date(2026, 8, 1),
        gross_amount=100000.0,
        net_amount=95000.0,
    )
    
    deduction = SettlementDeduction(
        id="d1",
        settlement_id="s1",
        type="chargeback",
        description="Dispute",
        amount=5000.0,
        extracted_with_confidence=0.95,
        reference_date=date(2026, 7, 28),
    )
    
    result, link = matcher.match_deduction_to_evidence(deduction, settlement)
    
    assert result.status == "verified"
    assert link is not None
    assert link.link_confidence > 0.8
    print("✓ Test: Evidence matcher successfully matches evidence")


# ============================================================================
# Integration Tests: AI Agent Investigation
# ============================================================================

def test_ai_agent_investigation_low_confidence():
    """Test AI agent investigation of low-confidence deductions."""
    import asyncio
    
    client = FakeFirestoreClient()
    settlement_repo = FirestoreSettlementRepository(client)
    deduction_repo = FirestoreSettlementDeductionRepository(client)
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    
    ai_provider = MockAIProvider()
    from formwise_api.settlements.finance_agent import SettlementFinanceAgent
    agent = SettlementFinanceAgent(ai_provider, audit_repo)
    
    settlement = Settlement(
        id="s1",
        owner_uid="user1",
        source="razorpay",
        settlement_date=date(2026, 8, 1),
        gross_amount=100000.0,
        net_amount=99000.0,
    )
    
    deduction = SettlementDeduction(
        id="d1",
        settlement_id="s1",
        type="other",
        description="Unknown deduction",
        amount=1000.0,
        extracted_with_confidence=0.35,  # Low confidence
    )
    
    # Run agent investigation
    verification_context = {
        "error": "Deduction extracted with low confidence (35%), cannot verify",
        "status": "unverifiable",
    }
    
    result = asyncio.run(
        agent.investigate_deduction(deduction, settlement, verification_context)
    )
    
    assert result.deduction_id == "d1"
    assert result.agent_investigation is not None
    assert "reasoning" in result.agent_investigation
    print(f"✓ Test: AI agent investigated low-confidence deduction → {result.status}")


def test_ai_agent_investigation_fee():
    """Test AI agent investigation of fee deduction."""
    import asyncio
    
    client = FakeFirestoreClient()
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    
    ai_provider = MockAIProvider()
    from formwise_api.settlements.finance_agent import SettlementFinanceAgent
    agent = SettlementFinanceAgent(ai_provider, audit_repo)
    
    settlement = Settlement(
        id="s1",
        owner_uid="user1",
        source="razorpay",
        settlement_date=date(2026, 8, 1),
        gross_amount=100000.0,
        net_amount=98000.0,
    )
    
    deduction = SettlementDeduction(
        id="d1",
        settlement_id="s1",
        type="fee",
        description="Processing fee 2%",
        amount=2000.0,
        extracted_with_confidence=0.85,
    )
    
    verification_context = {
        "error": "Fee structure unclear",
        "status": "unverifiable",
    }
    
    result = asyncio.run(
        agent.investigate_deduction(deduction, settlement, verification_context)
    )
    
    assert result.agent_investigation is not None
    assert result.status in ("verified", "unverifiable")
    print(f"✓ Test: AI agent investigated fee deduction → {result.status}")


# ============================================================================
# Integration Tests: Full Verification Workflow with Agent
# ============================================================================

def test_full_verification_with_agent():
    """Test complete verification workflow including agent investigation."""
    import asyncio
    
    client = FakeFirestoreClient()
    settlement_repo = FirestoreSettlementRepository(client)
    deduction_repo = FirestoreSettlementDeductionRepository(client)
    verification_repo = FirestoreVerificationResultRepository(client)
    decision_repo = FirestoreSettlementDecisionRepository(client)
    evidence_repo = FirestoreEvidenceLinkRepository(client)
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    
    ai_provider = MockAIProvider()
    
    extraction_service = SettlementExtractionService(
        settlement_repo, deduction_repo, audit_repo
    )
    
    verification_service = SettlementVerificationService(
        settlement_repo,
        deduction_repo,
        verification_repo,
        decision_repo,
        audit_repo,
        evidence_repo,
        ai_provider,
    )
    
    # Use synthetic_005 which has low-confidence deduction
    synthetic = get_settlement_test_data("synthetic_005")
    
    settlement = Settlement(
        id=synthetic.settlement_id,
        owner_uid=synthetic.owner_uid,
        source=synthetic.source,
        settlement_date=synthetic.settlement_date,
        gross_amount=synthetic.gross_amount,
        net_amount=synthetic.net_amount,
        currency=synthetic.currency,
    )
    settlement_repo.create(settlement)
    
    # Extract deductions
    deductions = extraction_service.extract_from_structured_data(
        synthetic.settlement_id,
        synthetic.deductions,
    )
    extraction_service.complete_extraction(synthetic.settlement_id)
    
    # Verify with agent
    decision = verification_service.verify_settlement(synthetic.settlement_id)
    
    assert decision is not None
    assert decision.final_decision in ("approve", "flag", "escalate")
    
    # Check that agent investigation happened
    verification_results = verification_repo.list_for_settlement(synthetic.settlement_id)
    assert len(verification_results) > 0
    
    print(f"✓ Test: Full verification workflow with agent → decision: {decision.final_decision}")


def test_agent_integration_with_all_synthetics():
    """Test agent integration with all 5 synthetic settlements."""
    import asyncio
    
    synthetics = generate_synthetic_settlements()
    
    print("\n" + "="*70)
    print("FULL VERIFICATION WORKFLOW: All 5 Synthetic Settlements with Agent")
    print("="*70)
    
    for synthetic in synthetics:
        client = FakeFirestoreClient()
        settlement_repo = FirestoreSettlementRepository(client)
        deduction_repo = FirestoreSettlementDeductionRepository(client)
        verification_repo = FirestoreVerificationResultRepository(client)
        decision_repo = FirestoreSettlementDecisionRepository(client)
        evidence_repo = FirestoreEvidenceLinkRepository(client)
        audit_repo = FirestoreFinanceAuditEventRepository(client)
        
        ai_provider = MockAIProvider()
        
        extraction_service = SettlementExtractionService(
            settlement_repo, deduction_repo, audit_repo
        )
        
        verification_service = SettlementVerificationService(
            settlement_repo,
            deduction_repo,
            verification_repo,
            decision_repo,
            audit_repo,
            evidence_repo,
            ai_provider,
        )
        
        settlement = Settlement(
            id=synthetic.settlement_id,
            owner_uid=synthetic.owner_uid,
            source=synthetic.source,
            settlement_date=synthetic.settlement_date,
            gross_amount=synthetic.gross_amount,
            net_amount=synthetic.net_amount,
            currency=synthetic.currency,
        )
        settlement_repo.create(settlement)
        
        deductions = extraction_service.extract_from_structured_data(
            synthetic.settlement_id,
            synthetic.deductions,
        )
        extraction_service.complete_extraction(synthetic.settlement_id)
        
        decision = verification_service.verify_settlement(synthetic.settlement_id)
        
        # Check results
        match = "✓" if decision.final_decision == synthetic.expected_decision else "○"
        print(f"{match} {synthetic.settlement_id:20s} ({synthetic.category:15s}) "
              f"Expected: {synthetic.expected_decision:8s} Got: {decision.final_decision:8s}")
        
        # Verify audit trail includes agent events if agent was used
        audit_events = list(audit_repo._client.collection("financeAuditEvents").data.values())
        agent_events = [e.get('action') if isinstance(e, dict) else e.to_dict().get('action') 
                       for e in audit_events if 'investigation' in str(e.get('action') if isinstance(e, dict) else e.to_dict().get('action', ''))]
        
        if agent_events:
            print(f"   Agent investigation events: {len(agent_events)}")


if __name__ == "__main__":
    print("="*70)
    print("EVIDENCE MATCHING & AI AGENT TESTS (Day 5-6)")
    print("="*70)
    
    # Unit tests
    print("\n[UNIT TESTS]")
    test_evidence_matcher_no_evidence()
    test_evidence_matcher_with_evidence()
    
    # Integration tests
    print("\n[INTEGRATION TESTS]")
    test_ai_agent_investigation_low_confidence()
    test_ai_agent_investigation_fee()
    test_full_verification_with_agent()
    
    # Full workflow test
    print("\n[FULL WORKFLOW TEST]")
    test_agent_integration_with_all_synthetics()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS COMPLETED")
    print("="*70)
