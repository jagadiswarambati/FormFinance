from datetime import datetime
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


EvidenceLinkStatus = Literal["found", "not_found", "partial"]


class EvidenceLink(BaseModel):
    """Link between a settlement deduction and supporting evidence document"""
    
    id: str = Field(default_factory=lambda: uuid4().hex)
    deduction_id: str = Field(alias="deductionId")
    evidence_document_id: str = Field(alias="evidenceDocumentId")
    link_confidence: float = Field(ge=0, le=1, alias="linkConfidence")
    extracted_from_evidence: str = Field(alias="extractedFromEvidence")  # Amount/detail found in doc
    status: EvidenceLinkStatus
    notes: str | None = None
    matched_at: datetime = Field(default_factory=datetime.utcnow, alias="matchedAt")
    
    model_config = ConfigDict(populate_by_name=True)


class EvidenceLinkResponse(BaseModel):
    """Response containing evidence link data"""
    
    id: str
    deduction_id: str = Field(alias="deductionId")
    evidence_document_id: str = Field(alias="evidenceDocumentId")
    link_confidence: float = Field(alias="linkConfidence")
    extracted_from_evidence: str = Field(alias="extractedFromEvidence")
    status: EvidenceLinkStatus
    notes: str | None = None
    matched_at: datetime = Field(alias="matchedAt")
    
    model_config = ConfigDict(populate_by_name=True)
