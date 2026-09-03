from datetime import date
from types import SimpleNamespace

import pytest

from formwise_api.evidence.repository import FirestoreEvidenceLinkRepository
from formwise_api.settlements.evidence_matcher import EvidenceMatcher, SettlementEvidenceStore
from formwise_api.settlements.models import Settlement, SettlementDeduction


class EmptyFirestore:
    def collection(self, _name):
        return SimpleNamespace()


class DocumentRepository:
    def __init__(self, document):
        self.document = document

    def get_for_owner(self, document_id, owner_uid):
        if document_id == self.document.document_id and owner_uid == self.document.owner_uid:
            return self.document
        return None


def make_matcher(tmp_path, ocr_text):
    path = tmp_path / "evidence.txt"
    path.write_text(ocr_text, encoding="utf-8")
    document = SimpleNamespace(
        document_id="evidence-1",
        owner_uid="user-1",
        ocr_status="completed",
        ocr_text_storage_key=str(path),
        original_filename="chargeback.pdf",
    )
    store = SettlementEvidenceStore(DocumentRepository(document))
    deduction = SettlementDeduction(
        id="deduction-1",
        settlement_id="settlement-1",
        type="chargeback",
        description="Customer dispute",
        amount=500.0,
        reference_id="TXN12345",
        reference_date=date(2026, 8, 20),
        extracted_with_confidence=0.95,
    )
    store.link_evidence_document(deduction.id, document.document_id, "chargeback_document")
    matcher = EvidenceMatcher(FirestoreEvidenceLinkRepository(EmptyFirestore()), store)
    settlement = Settlement(
        id="settlement-1",
        owner_uid="user-1",
        source="razorpay",
        settlement_date=date(2026, 8, 31),
        gross_amount=1000.0,
        net_amount=500.0,
    )
    return matcher, deduction, settlement


def test_ocr_evidence_all_fields_match(tmp_path):
    matcher, deduction, settlement = make_matcher(
        tmp_path,
        "Amount: INR 500.00\nDate: 20/08/2026\nTransaction ID: TXN12345",
    )

    result, link = matcher.match_deduction_to_evidence(deduction, settlement)

    assert result.status == "verified"
    assert result.evidence_match["amount_match"] is True
    assert result.evidence_match["date_match"] is True
    assert result.evidence_match["reference_match"] is True
    assert link.evidence_document_id == "evidence-1"


@pytest.mark.parametrize(
    ("ocr_text", "reason"),
    [
        ("Amount: INR 700\nDate: 20/08/2026\nTransaction ID: TXN12345", "Amount mismatch"),
        ("Amount: INR 500\nDate: 21/08/2026\nTransaction ID: TXN12345", "Date mismatch"),
        ("Amount: INR 500\nDate: 20/08/2026\nTransaction ID: TXN99999", "Reference mismatch"),
    ],
)
def test_ocr_evidence_field_mismatch_is_disputed(tmp_path, ocr_text, reason):
    matcher, deduction, settlement = make_matcher(tmp_path, ocr_text)

    result, _ = matcher.match_deduction_to_evidence(deduction, settlement)

    assert result.status == "disputed"
    assert reason in result.reason


def test_missing_evidence_is_not_matched(tmp_path):
    matcher, deduction, settlement = make_matcher(tmp_path, "")
    matcher._evidence_store = SettlementEvidenceStore()

    result, link = matcher.match_deduction_to_evidence(deduction, settlement)

    assert result.status == "unverifiable"
    assert "No supporting evidence found" in result.reason
    assert link is None


def test_missing_required_ocr_field_is_explicit(tmp_path):
    matcher, deduction, settlement = make_matcher(
        tmp_path,
        "Amount: INR 500\nDate: 20/08/2026",
    )

    result, _ = matcher.match_deduction_to_evidence(deduction, settlement)

    assert result.status == "unverifiable"
    assert "Missing reference in evidence OCR" in result.reason
    assert result.evidence_match["reference_match"] is False


def test_normalized_ocr_values_match(tmp_path):
    matcher, deduction, settlement = make_matcher(
        tmp_path,
        "Amount: ₹500\nDate: 2026-08-20\nReference: txn-12345",
    )

    result, _ = matcher.match_deduction_to_evidence(deduction, settlement)

    assert result.status == "verified"