"""Tests for Day 7-8: Document extraction and evidence integration."""

import sys
sys.path.insert(0, 'tests')

from datetime import date
from formwise_api.settlements.models import Settlement
from formwise_api.settlements.repository import (
    FirestoreSettlementRepository,
    FirestoreSettlementDeductionRepository,
)
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.settlements.evidence_matcher import EvidenceMatcher, SettlementEvidenceStore
from formwise_api.verification.repository import (
    FirestoreVerificationResultRepository,
    FirestoreSettlementDecisionRepository,
)
from formwise_api.evidence.repository import FirestoreEvidenceLinkRepository
from formwise_api.audit.repository import FirestoreFinanceAuditEventRepository
from formwise_api.documents.repository import DocumentRepository
from formwise_api.documents.models import DocumentResponse
from formwise_api.ai_provider.mock import MockAIProvider
from synthetic_documents import get_synthetic_documents, get_document


# Fake Firestore
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


# Mock Document Repository
class MockDocumentRepository:
    def __init__(self):
        self.documents = {}
    
    def create_mock_document(self, doc_id: str, owner_uid: str, filename: str):
        """Create a mock document for testing."""
        doc = DocumentResponse(
            document_id=doc_id,
            owner_uid=owner_uid,
            original_filename=filename,
            stored_filename=f"stored_{doc_id}",
            content_type="application/pdf",
            file_size=102400,
            uploaded_at=__import__('datetime').datetime.now(__import__('datetime').UTC),
            status="scanned",
            ocr_status="completed",
            ocr_confidence=0.95,
        )
        self.documents[doc_id] = doc
    
    def get_for_owner(self, document_id: str, owner_uid: str) -> DocumentResponse | None:
        if document_id in self.documents:
            doc = self.documents[document_id]
            if doc.owner_uid == owner_uid:
                return doc
        return None
    
    def mark_quarantined(self, document_id: str) -> DocumentResponse:
        pass
    
    def list_for_owner(self, owner_uid: str, limit: int) -> list[DocumentResponse]:
        pass
    
    def start_ocr(self, document_id: str, owner_uid: str, provider: str) -> DocumentResponse | None:
        pass
    
    def update_privacy(self, document_id: str, owner_uid: str, updates: dict) -> DocumentResponse | None:
        pass


# ============================================================================
# Tests
# ============================================================================

def test_document_extractor_clean_settlement():
    """Test extracting a clean settlement from document."""
    doc_data = get_document("doc_001_clean")
    
    client = FakeFirestoreClient()
    doc_repo = MockDocumentRepository()
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    
    doc_repo.create_mock_document("doc_001_clean", "user1", "settlement_clean.pdf")
    
    extractor = DocumentSettlementExtractor(doc_repo, audit_repo)
    
    result = extractor.extract_from_document("doc_001_clean", "user1", doc_data.ocr_text)
    
    assert result is not None
    settlement, deductions = result
    assert settlement.id == "doc_001_clean"
    assert settlement.gross_amount == 100000.0
    assert settlement.net_amount == 100000.0
    assert len(deductions) == 0
    print("✓ Test: Clean settlement extraction")


def test_document_extractor_with_deductions():
    """Test extracting settlement with multiple deductions."""
    doc_data = get_document("doc_002_fee_mismatch")
    
    client = FakeFirestoreClient()
    doc_repo = MockDocumentRepository()
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    
    doc_repo.create_mock_document("doc_002_fee_mismatch", "user1", "settlement_fee.pdf")
    
    extractor = DocumentSettlementExtractor(doc_repo, audit_repo)
    
    result = extractor.extract_from_document("doc_002_fee_mismatch", "user1", doc_data.ocr_text)
    
    assert result is not None
    settlement, deductions = result
    assert settlement.gross_amount == 250000.0
    assert settlement.net_amount == 245000.0
    assert len(deductions) >= 1
    assert any(d.type == "fee" for d in deductions)
    print("✓ Test: Settlement extraction with deductions")


def test_full_document_verification_flow():
    """Test complete flow: document → extraction → verification → decision."""
    doc_data = get_document("doc_004_chargeback")
    
    client = FakeFirestoreClient()
    settlement_repo = FirestoreSettlementRepository(client)
    deduction_repo = FirestoreSettlementDeductionRepository(client)
    verification_repo = FirestoreVerificationResultRepository(client)
    decision_repo = FirestoreSettlementDecisionRepository(client)
    evidence_repo = FirestoreEvidenceLinkRepository(client)
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    doc_repo = MockDocumentRepository()
    
    ai_provider = MockAIProvider()
    
    # Setup document
    doc_repo.create_mock_document("doc_004_chargeback", "user1", "settlement_chargeback.pdf")
    
    # Step 1: Extract from document
    extractor = DocumentSettlementExtractor(doc_repo, audit_repo)
    result = extractor.extract_from_document("doc_004_chargeback", "user1", doc_data.ocr_text)
    
    assert result is not None
    settlement, deductions = result
    
    # Step 2: Store settlement and deductions
    settlement_repo.create(settlement)
    for deduction in deductions:
        deduction_repo.create(deduction)
    
    # Step 3: Run verification with agent
    verification_service = SettlementVerificationService(
        settlement_repo,
        deduction_repo,
        verification_repo,
        decision_repo,
        audit_repo,
        evidence_repo,
        ai_provider,
    )
    
    decision = verification_service.verify_settlement(settlement.id)
    
    assert decision is not None
    assert decision.final_decision in ("approve", "flag", "escalate")
    print(f"✓ Test: Full document flow → decision: {decision.final_decision}")


def test_all_10_documents():
    """Test extraction of all 10 synthetic documents."""
    print("\n" + "="*70)
    print("DOCUMENT EXTRACTION TEST: All 10 Synthetic Settlements")
    print("="*70)
    
    docs = get_synthetic_documents()
    results = []
    
    for doc_data in docs:
        client = FakeFirestoreClient()
        doc_repo = MockDocumentRepository()
        settlement_repo = FirestoreSettlementRepository(client)
        deduction_repo = FirestoreSettlementDeductionRepository(client)
        verification_repo = FirestoreVerificationResultRepository(client)
        decision_repo = FirestoreSettlementDecisionRepository(client)
        evidence_repo = FirestoreEvidenceLinkRepository(client)
        audit_repo = FirestoreFinanceAuditEventRepository(client)
        
        ai_provider = MockAIProvider()
        
        # Setup document
        doc_repo.create_mock_document(doc_data.doc_id, "user1", f"{doc_data.doc_id}.pdf")
        
        # Extract
        extractor = DocumentSettlementExtractor(doc_repo, audit_repo)
        extract_result = extractor.extract_from_document(doc_data.doc_id, "user1", doc_data.ocr_text)
        
        if extract_result is None:
            print(f"✗ {doc_data.doc_id:25s} - Extraction failed")
            continue
        
        settlement, deductions = extract_result
        
        # Store
        settlement_repo.create(settlement)
        for deduction in deductions:
            deduction_repo.create(deduction)
        
        # Verify
        verification_service = SettlementVerificationService(
            settlement_repo,
            deduction_repo,
            verification_repo,
            decision_repo,
            audit_repo,
            evidence_repo,
            ai_provider,
        )
        
        decision = verification_service.verify_settlement(settlement.id)
        
        # Check results
        deduction_match = len(deductions) == doc_data.expected_deductions
        decision_match = decision.final_decision == doc_data.expected_decision
        
        status = "✓" if decision_match else "○"
        
        print(f"{status} {doc_data.doc_id:25s} ({doc_data.category:20s})")
        print(f"   Deductions: {len(deductions)}/{doc_data.expected_deductions} extracted")
        print(f"   Decision: {decision.final_decision} (expected: {doc_data.expected_decision})")
        print(f"   {doc_data.description}")
        
        results.append({
            "doc_id": doc_data.doc_id,
            "category": doc_data.category,
            "extracted": len(deductions) == doc_data.expected_deductions,
            "decision_match": decision_match,
            "actual_decision": decision.final_decision,
        })
    
    # Summary
    print("\n" + "="*70)
    extracted_ok = sum(1 for r in results if r["extracted"])
    decision_ok = sum(1 for r in results if r["decision_match"])
    print(f"Extraction accuracy: {extracted_ok}/{len(results)}")
    print(f"Decision accuracy: {decision_ok}/{len(results)}")
    print("="*70)


def test_evidence_integration_with_documents():
    """Test evidence matching with extracted settlement."""
    doc_data = get_document("doc_002_fee_mismatch")
    
    client = FakeFirestoreClient()
    settlement_repo = FirestoreSettlementRepository(client)
    deduction_repo = FirestoreSettlementDeductionRepository(client)
    verification_repo = FirestoreVerificationResultRepository(client)
    decision_repo = FirestoreSettlementDecisionRepository(client)
    evidence_repo = FirestoreEvidenceLinkRepository(client)
    audit_repo = FirestoreFinanceAuditEventRepository(client)
    doc_repo = MockDocumentRepository()
    
    evidence_store = SettlementEvidenceStore()
    
    # Setup evidence for the fee deduction
    evidence_store.register_evidence(
        "fee_deduction_id",
        "fee_documentation",
        {
            "amount": 5500.0,  # Expected fee
            "date": date(2026, 8, 14),
            "reason": "Processing fee",
        }
    )
    
    # Extract settlement
    doc_repo.create_mock_document("doc_002_fee_mismatch", "user1", "settlement_fee.pdf")
    extractor = DocumentSettlementExtractor(doc_repo, audit_repo)
    result = extractor.extract_from_document("doc_002_fee_mismatch", "user1", doc_data.ocr_text)
    
    assert result is not None
    settlement, deductions = result
    
    # Store
    settlement_repo.create(settlement)
    for deduction in deductions:
        deduction_repo.create(deduction)
    
    # Try evidence matching
    matcher = EvidenceMatcher(evidence_repo, evidence_store)
    results = matcher.match_settlement_evidence(settlement, deductions)
    
    assert len(results) == len(deductions)
    print("✓ Test: Evidence matching with extracted settlement")


if __name__ == "__main__":
    print("="*70)
    print("DAY 7-8 TESTS: DOCUMENT EXTRACTION & EVIDENCE INTEGRATION")
    print("="*70)
    
    print("\n[UNIT TESTS]")
    test_document_extractor_clean_settlement()
    test_document_extractor_with_deductions()
    
    print("\n[INTEGRATION TESTS]")
    test_full_document_verification_flow()
    test_evidence_integration_with_documents()
    
    print("\n[BATCH TEST]")
    test_all_10_documents()
    
    print("\n✓ ALL DAY 7-8 TESTS COMPLETED")
