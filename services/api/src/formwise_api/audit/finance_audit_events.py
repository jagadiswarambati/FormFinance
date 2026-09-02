from datetime import datetime
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


FinanceAuditAction = Literal[
    "settlement_uploaded",
    "deduction_extracted",      # Individual deduction extracted from document
    "extraction_completed",     # Settlement-level extraction complete
    "deduction_verified",       # Deduction passed verification checks
    "evidence_found",
    "conflict_detected",
    "agent_investigation",
    "human_review",
    "decision_made"
]

FinanceResourceType = Literal[
    "settlement",
    "deduction",
    "evidence_link",
    "verification_result"
]


class FinanceAuditEvent(BaseModel):
    """Immutable audit event for settlement verification workflow"""
    
    id: str = Field(default_factory=lambda: uuid4().hex)
    settlement_id: str = Field(alias="settlementId")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: FinanceAuditAction
    resource_type: FinanceResourceType = Field(alias="resourceType")
    resource_id: str = Field(alias="resourceId")
    details: dict = Field(default_factory=dict)
    evidence_links: list[str] = Field(default_factory=list, alias="evidenceLinks")
    confidence: float | None = Field(default=None, ge=0, le=1)
    outcome: str | None = None
    
    model_config = ConfigDict(populate_by_name=True)
