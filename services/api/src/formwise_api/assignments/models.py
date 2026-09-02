from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssignmentSource = Literal["conversation", "structured_document", "previous_approved_answer", "document_metadata", "system_generated", "unknown"]
AssignmentStatus = Literal["pending_review", "approved", "rejected", "manual_only", "conflict", "missing"]


class AssignmentEvidence(BaseModel):
    source_id: str = Field(alias="sourceId")
    description: str

    model_config = ConfigDict(populate_by_name=True)


class FieldAssignment(BaseModel):
    id: str
    document_id: str = Field(alias="documentId")
    field_id: str = Field(alias="fieldId")
    label: str
    value: str | None = None
    confidence: float = Field(ge=0, le=1)
    source: AssignmentSource
    reason: str
    evidence: list[AssignmentEvidence] = Field(default_factory=list)
    requires_review: bool = Field(alias="requiresReview")
    status: AssignmentStatus
    question: str | None = None
    privacy_tier: Literal["safe", "restricted", "sensitive"] = Field(alias="privacyTier")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class AssignmentUpdateRequest(BaseModel):
    action: Literal["approve", "reject", "edit"]
    value: str | None = Field(default=None, max_length=1000)


class AssignmentGenerationResponse(BaseModel):
    assignments: list[FieldAssignment]
