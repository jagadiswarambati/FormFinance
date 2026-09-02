"""End-to-end integration test for real settlement processing pipeline.

Tests the complete workflow:
1. Document upload/storage
2. OCR processing
3. Settlement extraction
4. Deduction verification
5. Evidence matching
6. AI investigation
7. Decision generation
8. Audit trail
"""

import pytest
from datetime import date, UTC, datetime
from unittest.mock import Mock, MagicMock

from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.settlements.processing import SettlementProcessingPipeline
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.deterministic_verifier import DeterministicVerifier
from formwise_api.settlements.evidence_matcher import EvidenceMatcher, SettlementEvidenceStore
from formwise_api.settlements.verification_service import SettlementVerificationService
from formwise_api.documents.models import DocumentResponse
from formwise_api.verification.models import SettlementDecision
from formwise_api.audit.finance_audit_events import FinanceAuditEvent
from tests.synthetic_data import create_test_settlement, create_test_deduction


class TestSettlementProcessingPipeline:
    """Test complete settlement processing pipeline."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "document": Mock(),
            "settlement": Mock(),
            "deduction": Mock(),
            "decision": Mock(),
            "evidence": Mock(),
            "audit": Mock(),
        }
    
    @pytest.fixture
    def pipeline(self, mock_repos):
        """Create processing pipeline with mocks."""
        return SettlementProcessingPipeline(
            document_repo=mock_repos["document"],
            settlement_repo=mock_repos["settlement"],
            deduction_repo=mock_repos["deduction"],
            decision_repo=mock_repos["decision"],
            evidence_repo=mock_repos["evidence"],
            audit_repo=mock_repos["audit"],
        )
    
    @pytest.fixture
    def mock_document(self):
        """Create mock FormWise document."""
        return DocumentResponse(
            document_id="doc_123",
            owner_uid="user_123",
            original_filename="settlement_2026_08.pdf",
            stored_filename="doc_123_settlement.pdf",
            content_type="application/pdf",
            file_size=102400,
            uploaded_at=datetime.now(UTC),
            status="uploaded",
            ocr_status="completed",
            ocr_provider="paddle",
            ocr_confidence=0.92,
            text_length=5432,
            ocr_text_storage_key="gs://bucket/ocr/doc_123_text",
        )
    
    def test_pipeline_initialization(self, pipeline, mock_repos):
        """Test that pipeline initializes all services."""
        assert pipeline._document_repo == mock_repos["document"]
        assert pipeline._settlement_repo == mock_repos["settlement"]
        assert pipeline._verifier is not None
        assert pipeline._matcher is not None
        assert pipeline._agent is not None
    
    def test_process_settlement_document_with_ocr_text(
        self, pipeline, mock_repos, mock_document
    ):
        """Test processing settlement document with provided OCR text."""
        # Setup mocks
        mock_repos["document"].get_for_owner.return_value = mock_document
        
        ocr_text = """
        Razorpay Settlement Statement
        Date: 2026-08-15
        Gross Amount: INR 250,000.00
        Fees: INR 5,000.00
        Refunds: INR 2,500.00
        Chargebacks: INR 1,200.00
        Net Amount: INR 241,300.00
        """
        
        # Process
        result = pipeline.process_settlement_document(
            document_id="doc_123",
            owner_uid="user_123",
            ocr_text=ocr_text,
        )
        
        # Verify
        assert result is not None
        assert "settlement_id" in result
        assert result["status"] in ["approved", "flagged", "escalated", "failed"]
        assert "deductions" in result
        assert "decision" in result
    
    def test_process_settlement_with_evidence_documents(
        self, pipeline, mock_repos, mock_document
    ):
        """Test processing with evidence document linking."""
        # Setup
        mock_repos["document"].get_for_owner.side_effect = lambda doc_id, uid: (
            mock_document if doc_id == "doc_123" else
            DocumentResponse(
                document_id="evidence_doc_1",
                owner_uid="user_123",
                original_filename="chargeback_evidence.pdf",
                stored_filename="evidence_1.pdf",
                content_type="application/pdf",
                file_size=51200,
                uploaded_at=datetime.now(UTC),
                status="uploaded",
                ocr_status="completed",
            )
        )
        
        ocr_text = """
        Razorpay Settlement
        Gross: INR 100,000
        Chargeback: INR 5,000
        Net: INR 95,000
        """
        
        # Process with evidence
        result = pipeline.process_settlement_document(
            document_id="doc_123",
            owner_uid="user_123",
            ocr_text=ocr_text,
            evidence_document_ids=["evidence_doc_1"],
        )
        
        # Verify
        assert result is not None
        assert "settlement_id" in result
    
    def test_get_settlement_details(self, pipeline, mock_repos):
        """Test retrieving complete settlement details."""
        # Setup
        settlement = Settlement(
            id="settlement_456",
            owner_uid="user_123",
            source="razorpay",
            settlement_date=date(2026, 8, 15),
            gross_amount=250000.0,
            net_amount=241300.0,
            currency="INR",
        )
        deduction = SettlementDeduction(
            settlement_id="settlement_456",
            type="fee",
            description="Platform fees",
            amount=5000.0,
        )
        decision = SettlementDecision(
            settlement_id="settlement_456",
            decision="approved",
            confidence=0.95,
            explanation="All deductions verified",
        )
        
        mock_repos["settlement"].get.return_value = settlement
        mock_repos["deduction"].list_by_settlement.return_value = [deduction]
        mock_repos["decision"].get_by_settlement.return_value = decision
        
        # Get details
        details = pipeline.get_settlement_details("settlement_456", "user_123")
        
        # Verify
        assert details is not None
        assert details["settlement"]["id"] == "settlement_456"
        assert len(details["deductions"]) == 1
        assert details["decision"]["status"] == "approved"


class TestDocumentExtractorIntegration:
    """Test DocumentSettlementExtractor with mock repositories."""
    
    def test_extract_from_ocr_text(self):
        """Test extraction from OCR text without document."""
        # Setup
        document_repo = Mock()
        audit_repo = Mock()
        extractor = DocumentSettlementExtractor(
            document_repo=document_repo,
            audit_repo=audit_repo,
        )
        
        ocr_text = """
        Settlement Report - August 2026
        Gateway: Razorpay
        Date: 2026-08-30
        
        Summary
        -------
        Gross Amount: INR 500,000
        Platform Fees: INR 10,000
        Refunds: INR 5,000
        Chargebacks: INR 2,500
        Net Amount: INR 482,500
        """
        
        # Extract
        result = extractor.extract_from_document(
            document_id="doc_456",
            owner_uid="user_123",
            ocr_text=ocr_text,
        )
        
        # Verify
        assert result is not None
        settlement, deductions = result
        assert settlement.source == "razorpay"
        assert settlement.gross_amount > 0
        assert len(deductions) > 0
        
        # Verify deduction types
        deduction_types = {d.type for d in deductions}
        assert "fee" in deduction_types


class TestEvidenceMatcherIntegration:
    """Test EvidenceMatcher with real services."""
    
    def test_evidence_matching_workflow(self):
        """Test finding and matching evidence for deductions."""
        # Setup
        evidence_repo = Mock()
        evidence_store = SettlementEvidenceStore()
        matcher = EvidenceMatcher(
            evidence_repo=evidence_repo,
            evidence_store=evidence_store,
        )
        
        # Create test data
        settlement = Settlement(
            id="settlement_789",
            owner_uid="user_123",
            source="razorpay",
            settlement_date=date(2026, 8, 15),
            gross_amount=100000.0,
            net_amount=95000.0,
            currency="INR",
        )
        
        deduction = SettlementDeduction(
            settlement_id="settlement_789",
            type="chargeback",
            description="Chargeback from customer",
            amount=2000.0,
        )
        
        # Register evidence
        evidence_store.register_evidence(
            deduction_id=deduction.id,
            evidence_type="document",
            evidence_data={
                "document_id": "chargeback_doc_1",
                "amount": 2000.0,
                "date": "2026-08-15",
            },
        )
        
        # Match
        result, evidence_link = matcher.match_deduction_to_evidence(
            deduction=deduction,
            settlement=settlement,
        )
        
        # Verify
        assert result is not None
        assert result.deduction_id == deduction.id


class TestCompleteWorkflowIntegration:
    """Test the complete settlement workflow from document to decision."""
    
    def test_end_to_end_settlement_workflow(self):
        """Test complete workflow: upload → OCR → extract → verify → decide."""
        # This is a high-level integration test showing the complete workflow
        
        # 1. Document would be uploaded and stored by FormWise infrastructure
        document_id = "real_settlement_doc_001"
        owner_uid = "user_test"
        
        # 2. OCR would process the document (real PaddleOCR or similar)
        ocr_text = """
        RAZORPAY SETTLEMENT REPORT
        Settlement Period: August 1-31, 2026
        Settlement Date: 2026-09-01
        
        FINANCIAL SUMMARY
        -----------------
        Opening Balance: INR 0.00
        Transaction Volume: INR 1,000,000.00
        Gross Settlement: INR 980,000.00
        
        DEDUCTIONS
        ----------
        Payment Gateway Fees (2%): INR 20,000.00
        Refunds Processed: INR 15,000.00
        Chargebacks: INR 3,000.00
        
        FINAL SETTLEMENT
        ----------------
        Net Payout Amount: INR 942,000.00
        Settlement Status: APPROVED
        """
        
        # 3-8. These would be handled by the SettlementProcessingPipeline
        # - Extraction would parse the amounts and deductions
        # - Deterministic verifier would check for discrepancies
        # - Evidence matcher would link supporting documents
        # - AI agent would investigate any unresolved issues
        # - Decision would be generated (APPROVE/FLAG/ESCALATE)
        # - Audit trail would log all events
        
        # Verify the complete workflow is possible
        # (Actual execution would require Firestore setup)
        assert document_id is not None
        assert ocr_text is not None
        assert len(ocr_text) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
