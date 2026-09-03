import os
import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, date
from pathlib import Path
from unittest.mock import Mock

import fitz
import pytest

from formwise_api.documents.models import DocumentResponse
from formwise_api.settlements.document_extractor import DocumentSettlementExtractor
from formwise_api.settlements.evidence_matcher import EvidenceMatcher, SettlementEvidenceStore
from formwise_api.settlements.models import Settlement, SettlementDeduction
from formwise_api.storage.local import LocalStorageAdapter
from formwise_worker.ocr.store import LocalOcrResultStore
from formwise_api.settlements.processing import SettlementProcessingPipeline
from formwise_api.settlements.router import ProcessSettlementDocumentResponse


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "settlements"
SETTLEMENT_FIXTURES = (
    "valid_settlement.pdf",
    "deduction_mismatch_settlement.pdf",
    "missing_evidence_settlement.pdf",
    "escalation_settlement.pdf",
    "multiple_deductions_settlement.pdf",
)


def pdf_text(filename: str) -> str:
    with fitz.open(FIXTURE_DIR / filename) as document:
        return "\n".join(page.get_text() for page in document)


async def chunks(value: bytes) -> AsyncIterator[bytes]:
    yield value


class InMemoryDocumentRepository:
    def __init__(self, documents: list[DocumentResponse]):
        self.documents = {document.document_id: document for document in documents}

    def get_for_owner(self, document_id: str, owner_uid: str) -> DocumentResponse | None:
        document = self.documents.get(document_id)
        return document if document and document.owner_uid == owner_uid else None

    def list_for_owner(self, owner_uid: str, limit: int) -> list[DocumentResponse]:
        return [document for document in self.documents.values() if document.owner_uid == owner_uid][:limit]


class NoopAuditRepository:
    def create(self, _event):
        return None


class SettlementRepositories:
    def __init__(self):
        self.settlements = {}
        self.deductions = {}
        self.decisions = {}
        self.verifications = {}

    def create_settlement(self, settlement):
        self.settlements[settlement.id] = settlement
        return settlement.id

    def get_settlement(self, settlement_id):
        return self.settlements.get(settlement_id)

    def update_settlement(self, settlement_id, updates):
        settlement = self.settlements.get(settlement_id)
        if settlement:
            for field, value in updates.items():
                if field == "status":
                    settlement.status = value
                elif field == "deductionIds":
                    settlement.deduction_ids = value
        return settlement

    def create_deduction(self, deduction):
        self.deductions[deduction.id] = deduction
        return deduction.id

    def list_deductions(self, settlement_id):
        return [d for d in self.deductions.values() if d.settlement_id == settlement_id]

    def create_verification(self, result):
        self.verifications[result.id] = result
        return result.id

    def create_decision(self, decision):
        self.decisions[decision.id] = decision
        return decision.id

    def get_decision(self, decision_id):
        return self.decisions.get(decision_id)


def make_pipeline(document_repo, repositories):
    settlement_repo = Mock()
    settlement_repo.create.side_effect = repositories.create_settlement
    settlement_repo.get.side_effect = repositories.get_settlement
    settlement_repo.update.side_effect = repositories.update_settlement
    deduction_repo = Mock()
    deduction_repo.create.side_effect = repositories.create_deduction
    deduction_repo.list_for_settlement.side_effect = repositories.list_deductions
    verification_repo = Mock()
    verification_repo.create.side_effect = repositories.create_verification
    decision_repo = Mock()
    decision_repo.create.side_effect = repositories.create_decision
    decision_repo.get.side_effect = repositories.get_decision
    audit_repo = NoopAuditRepository()
    return SettlementProcessingPipeline(
        document_repo=document_repo,
        settlement_repo=settlement_repo,
        deduction_repo=deduction_repo,
        verification_repo=verification_repo,
        decision_repo=decision_repo,
        evidence_repo=Mock(),
        audit_repo=audit_repo,
    )


def document(document_id: str, filename: str, ocr_key: str | None = None) -> DocumentResponse:
    return DocumentResponse(
        document_id=document_id,
        owner_uid="fixture-user",
        original_filename=filename,
        stored_filename=filename,
        content_type="application/pdf",
        file_size=(FIXTURE_DIR / filename).stat().st_size,
        uploaded_at=datetime.now(UTC),
        status="ocr_completed" if ocr_key else "uploaded",
        ocr_status="completed" if ocr_key else "not_started",
        ocr_provider="paddleocr" if ocr_key else None,
        ocr_text_storage_key=ocr_key,
    )


def test_fixture_set_is_real_pdf_and_covers_required_cases():
    assert len(SETTLEMENT_FIXTURES) == 5
    for filename in SETTLEMENT_FIXTURES:
        path = FIXTURE_DIR / filename
        assert path.is_file()
        with fitz.open(path) as pdf:
            assert len(pdf) == 1
            assert "Settlement" in pdf[0].get_text() or "Payout" in pdf[0].get_text()


def test_fixture_enters_existing_upload_storage(tmp_path: Path):
    fixture = FIXTURE_DIR / "valid_settlement.pdf"
    storage = LocalStorageAdapter(str(tmp_path / "uploads"), str(tmp_path / "quarantine"))
    content = fixture.read_bytes()

    stored = asyncio.run(
        storage.write_upload(
            fixture.name,
            "application/pdf",
            chunks(content),
            maximum_size=10 * 1024 * 1024,
        )
    )

    assert stored.file_size == len(content)
    assert storage.inspect(fixture.name).file_size == len(content)
    assert storage.release_quarantined(fixture.name)
    assert (tmp_path / "uploads" / fixture.name).read_bytes() == content


@pytest.mark.parametrize("filename", SETTLEMENT_FIXTURES)
def test_fixture_text_flows_into_existing_settlement_extractor(filename: str):
    repository = InMemoryDocumentRepository([document("settlement-1", filename)])
    extractor = DocumentSettlementExtractor(repository, NoopAuditRepository())

    result = extractor.extract_from_document("settlement-1", "fixture-user", pdf_text(filename))

    assert result is not None
    settlement, deductions = result
    assert settlement.gross_amount > 0
    assert settlement.net_amount > 0
    assert deductions
    assert all(deduction.settlement_id == settlement.id for deduction in deductions)
    if filename == "multiple_deductions_settlement.pdf":
        assert len(deductions) == 5


def test_pdf_evidence_fixture_proves_match_and_mismatch(tmp_path: Path):
    ocr_store = LocalOcrResultStore(str(tmp_path / "ocr"))
    match_key = ocr_store.write("evidence-match", pdf_text("chargeback_evidence_match.pdf"))
    mismatch_key = ocr_store.write("evidence-mismatch", pdf_text("chargeback_evidence_mismatch.pdf"))
    documents = [
        document("evidence-match", "chargeback_evidence_match.pdf", match_key),
        document("evidence-mismatch", "chargeback_evidence_mismatch.pdf", mismatch_key),
    ]
    repository = InMemoryDocumentRepository(documents)
    evidence_store = SettlementEvidenceStore(repository)
    deduction = SettlementDeduction(
        id="deduction-1",
        settlement_id="settlement-1",
        type="chargeback",
        description="Chargeback",
        amount=500.0,
        reference_id="TXN-DEMO-001",
        reference_date=date(2026, 8, 20),
        extracted_with_confidence=0.95,
    )
    settlement = Settlement(
        id="settlement-1",
        owner_uid="fixture-user",
        source="razorpay",
        settlement_date=date(2026, 8, 20),
        gross_amount=100000.0,
        net_amount=99500.0,
    )
    matcher = EvidenceMatcher(NoopAuditRepository(), evidence_store)

    evidence_store.link_evidence_document(deduction.id, "evidence-match", "chargeback_document")
    matched, _ = matcher.match_deduction_to_evidence(deduction, settlement)
    assert matched.status == "verified"

    evidence_store.evidence_database[deduction.id] = []
    evidence_store.link_evidence_document(deduction.id, "evidence-mismatch", "chargeback_document")
    mismatched, _ = matcher.match_deduction_to_evidence(deduction, settlement)
    assert mismatched.status == "disputed"
    assert "Amount mismatch" in mismatched.reason


def test_stored_ocr_flows_through_settlement_processing(tmp_path: Path):
    ocr_key = LocalOcrResultStore(str(tmp_path / "ocr")).write(
        "settlement-1", pdf_text("valid_settlement.pdf")
    )
    repository = InMemoryDocumentRepository([
        document("settlement-1", "valid_settlement.pdf", ocr_key)
    ])
    repositories = SettlementRepositories()
    pipeline = make_pipeline(repository, repositories)

    result = pipeline.process_settlement_document("settlement-1", "fixture-user")

    assert result["status"] == "approve"
    assert result["gross_amount"] == 100000.0
    assert result["net_amount"] == 96500.0
    assert len(result["deductions"]) == 3
    assert repositories.settlements["settlement-1"].deduction_ids
    serialized = ProcessSettlementDocumentResponse.model_validate(result).model_dump(by_alias=True)
    assert {
        "settlementId", "documentId", "reference", "currency", "grossAmount",
        "totalDeductions", "netAmount", "deductions", "verification", "evidence",
        "decision", "auditEvents", "processedAt",
    }.issubset(serialized)


def test_missing_ocr_storage_fails_without_fake_text(tmp_path: Path):
    missing_key = str(tmp_path / "ocr" / "does-not-exist.txt")
    repository = InMemoryDocumentRepository([
        document("settlement-1", "valid_settlement.pdf", missing_key)
    ])
    repositories = SettlementRepositories()
    pipeline = make_pipeline(repository, repositories)

    result = pipeline.process_settlement_document("settlement-1", "fixture-user")

    assert result == {
        "error": "Document OCR result is unavailable",
        "status": "ocr_unavailable",
        "document_id": "settlement-1",
    }
    assert repositories.settlements == {}
    assert repositories.deductions == {}


@pytest.mark.skipif(
    os.environ.get("FORMWISE_RUN_REAL_PADDLEOCR") != "1",
    reason="Set FORMWISE_RUN_REAL_PADDLEOCR=1 to run the model-backed OCR fixture test",
)
def test_valid_fixture_with_real_paddleocr():
    from formwise_worker.ocr.paddle import PaddleOCRProvider

    result = PaddleOCRProvider().extract(FIXTURE_DIR / "valid_settlement.pdf")

    assert "RZP-DEMO-001" in result.text
    assert "100,000.00" in result.text