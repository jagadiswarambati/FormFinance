from datetime import datetime
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


DeductionVerificationStatus = Literal["verified", "disputed", "unverifiable"]
SettlementDecisionType = Literal["approve", "flag", "escalate"]


class DeterministicCheckResult(BaseModel):
    """Result of a deterministic verification check"""
    
    check_name: str
    passed: bool
    message: str = ""
    
    model_config = ConfigDict(populate_by_name=True)


class EvidenceMatchResult(BaseModel):
    """Result of evidence matching"""
    
    evidence_found: bool
    confidence: float = Field(ge=0, le=1)
    discrepancy: str | None = None  # "amount_mismatch", "date_mismatch", etc.
    
    model_config = ConfigDict(populate_by_name=True)


class VerificationResult(BaseModel):
    """Verification result for a single deduction"""
    
    id: str = Field(default_factory=lambda: uuid4().hex)
    deduction_id: str = Field(alias="deductionId")
    settlement_id: str = Field(alias="settlementId")
    status: DeductionVerificationStatus
    reason: str
    
    # Deterministic checks
    deterministic_checks: dict = Field(default_factory=dict, alias="deterministicChecks")
    
    # Evidence matching
    evidence_match: dict = Field(default_factory=dict, alias="evidenceMatch")
    
    # Agent investigation (optional, added later)
    agent_investigation: dict | None = Field(default=None, alias="agentInvestigation")
    
    # Human review (optional)
    human_review: dict | None = Field(default=None, alias="humanReview")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    
    model_config = ConfigDict(populate_by_name=True)


class SettlementDecision(BaseModel):
    """Final decision for a settlement"""
    
    id: str = Field(default_factory=lambda: uuid4().hex)
    settlement_id: str = Field(alias="settlementId")
    final_decision: SettlementDecisionType = Field(alias="finalDecision")
    reason: str
    
    # Summary
    verification_summary: dict = Field(default_factory=dict, alias="verificationSummary")
    gaps_identified: list[str] = Field(default_factory=list, alias="gapsIdentified")
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool = Field(default=False, alias="requiresHumanReview")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    
    model_config = ConfigDict(populate_by_name=True)
