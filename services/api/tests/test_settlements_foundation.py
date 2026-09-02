"""Unit tests for settlements domain foundation (Day 1-2)"""

from datetime import date, datetime
import pytest
from formwise_api.settlements.models import (
    Settlement,
    SettlementDeduction,
    SettlementCreateRequest,
)
from formwise_api.verification.models import (
    VerificationResult,
    SettlementDecision,
)
from formwise_api.evidence.models import EvidenceLink
from formwise_api.audit.finance_audit_events import FinanceAuditEvent


def test_settlement_creation():
    """Test Settlement model creation with defaults"""
    settlement = Settlement(
        owner_uid="user123",
        source="razorpay",
        settlement_date=date(2026, 8, 25),
        gross_amount=500000.0,
        net_amount=470000.0,
        currency="INR",
    )
    assert settlement.owner_uid == "user123"
    assert settlement.gross_amount == 500000.0
    assert settlement.status == "uploaded"
    assert len(settlement.id) > 0
    assert settlement.deduction_ids == []
    assert settlement.document_ids == []


def test_settlement_deduction_creation():
    """Test SettlementDeduction model creation"""
    deduction = SettlementDeduction(
        settlement_id="settlement123",
        type="chargeback",
        description="Customer dispute",
        amount=15000.0,
        reference_id="CB-001",
        extracted_with_confidence=0.95,
    )
    assert deduction.settlement_id == "settlement123"
    assert deduction.type == "chargeback"
    assert deduction.amount == 15000.0
    assert deduction.extracted_with_confidence == 0.95
    assert len(deduction.id) > 0


def test_evidence_link_creation():
    """Test EvidenceLink model creation"""
    link = EvidenceLink(
        deduction_id="deduction123",
        evidence_document_id="doc123",
        link_confidence=0.92,
        extracted_from_evidence="15000",
        status="found",
    )
    assert link.deduction_id == "deduction123"
    assert link.status == "found"
    assert link.link_confidence == 0.92
    assert len(link.id) > 0


def test_verification_result_creation():
    """Test VerificationResult model creation"""
    result = VerificationResult(
        deduction_id="deduction123",
        settlement_id="settlement123",
        status="verified",
        reason="Evidence matches settlement claim",
    )
    assert result.deduction_id == "deduction123"
    assert result.status == "verified"
    assert len(result.id) > 0
    assert result.agent_investigation is None
    assert result.human_review is None


def test_settlement_decision_creation():
    """Test SettlementDecision model creation"""
    decision = SettlementDecision(
        settlement_id="settlement123",
        final_decision="approve",
        reason="All deductions verified",
        verification_summary={"total": 5, "verified": 5, "disputed": 0},
        confidence=0.98,
    )
    assert decision.settlement_id == "settlement123"
    assert decision.final_decision == "approve"
    assert decision.confidence == 0.98
    assert len(decision.id) > 0


def test_finance_audit_event_creation():
    """Test FinanceAuditEvent model creation"""
    event = FinanceAuditEvent(
        settlement_id="settlement123",
        action="settlement_uploaded",
        resource_type="settlement",
        resource_id="settlement123",
        details={"source": "razorpay"},
    )
    assert event.settlement_id == "settlement123"
    assert event.action == "settlement_uploaded"
    assert len(event.id) > 0
    assert event.confidence is None


def test_settlement_create_request():
    """Test SettlementCreateRequest with alias handling"""
    req = SettlementCreateRequest(
        source="razorpay",
        settlementDate=date(2026, 8, 25),
        grossAmount=500000.0,
        netAmount=470000.0,
    )
    # Verify alias handling
    data = req.model_dump(by_alias=True)
    assert data["settlementDate"] == date(2026, 8, 25)
    assert data["grossAmount"] == 500000.0


def test_settlement_alias_conversion():
    """Test that models work with both snake_case and camelCase"""
    # Create with camelCase
    data = {
        "id": "s123",
        "ownerUid": "user123",
        "source": "razorpay",
        "settlementDate": date(2026, 8, 25),
        "grossAmount": 500000.0,
        "netAmount": 470000.0,
        "currency": "INR",
        "status": "uploaded",
    }
    settlement = Settlement(**data)
    assert settlement.owner_uid == "user123"
    
    # Verify dump works with aliases
    dumped = settlement.model_dump(by_alias=True)
    assert "ownerUid" in dumped
    assert "settlementDate" in dumped


def test_deduction_types():
    """Test all valid deduction types"""
    types = ["chargeback", "fee", "hold", "refund", "other"]
    for dtype in types:
        deduction = SettlementDeduction(
            settlement_id="s1",
            type=dtype,
            description="Test",
            amount=100.0,
            extracted_with_confidence=0.8,
        )
        assert deduction.type == dtype


def test_verification_statuses():
    """Test all valid verification statuses"""
    statuses = ["verified", "disputed", "unverifiable"]
    for status in statuses:
        result = VerificationResult(
            deduction_id="d1",
            settlement_id="s1",
            status=status,
            reason="Test",
        )
        assert result.status == status


def test_settlement_decision_types():
    """Test all valid settlement decision types"""
    decisions = ["approve", "flag", "escalate"]
    for decision_type in decisions:
        decision = SettlementDecision(
            settlement_id="s1",
            final_decision=decision_type,
            reason="Test",
            confidence=0.8,
        )
        assert decision.final_decision == decision_type


def test_finance_audit_actions():
    """Test all valid audit actions"""
    actions = [
        "settlement_uploaded",
        "extraction_completed",
        "deduction_verified",
        "evidence_found",
        "conflict_detected",
        "agent_investigation",
        "human_review",
        "decision_made",
    ]
    for action in actions:
        event = FinanceAuditEvent(
            settlement_id="s1",
            action=action,
            resource_type="settlement",
            resource_id="s1",
        )
        assert event.action == action


def test_verification_result_with_checks():
    """Test VerificationResult with deterministic checks"""
    result = VerificationResult(
        deduction_id="d1",
        settlement_id="s1",
        status="verified",
        reason="All checks passed",
        deterministic_checks={"arithmetic": True, "amount_match": True},
        evidence_match={"evidence_found": True, "confidence": 0.95},
    )
    assert result.deterministic_checks["arithmetic"] is True
    assert result.evidence_match["confidence"] == 0.95


def test_settlement_decision_with_summary():
    """Test SettlementDecision with verification summary"""
    decision = SettlementDecision(
        settlement_id="s1",
        final_decision="flag",
        reason="Some deductions need review",
        verification_summary={
            "total": 5,
            "verified": 3,
            "disputed": 1,
            "unverifiable": 1,
        },
        confidence=0.75,
        requires_human_review=True,
    )
    assert decision.verification_summary["total"] == 5
    assert decision.requires_human_review is True


def test_evidence_link_statuses():
    """Test all valid evidence link statuses"""
    statuses = ["found", "not_found", "partial"]
    for status in statuses:
        link = EvidenceLink(
            deduction_id="d1",
            evidence_document_id="doc1",
            link_confidence=0.8,
            extracted_from_evidence="100",
            status=status,
        )
        assert link.status == status
