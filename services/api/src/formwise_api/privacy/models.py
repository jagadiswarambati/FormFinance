from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PrivacyAction = Literal["ALLOW", "REDACT", "ASK_USER", "BLOCK"]
ConsentDecision = Literal["continue_with_redaction", "continue_protected", "cancel"]


class PrivacyFindingSummary(BaseModel):
    category: str
    count: int
    action: PrivacyAction


class PrivacyReportResponse(BaseModel):
    document_id: str = Field(alias="documentId")
    status: str
    policy_version: str = Field(alias="policyVersion")
    findings: list[PrivacyFindingSummary]
    pii_categories: list[str] = Field(alias="piiCategories")
    requires_consent: bool = Field(alias="requiresConsent")
    consent_decision: ConsentDecision | None = Field(default=None, alias="consentDecision")
    protected_text_ready: bool = Field(alias="protectedTextReady")
    completed_at: datetime | None = Field(default=None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


class PrivacyConsentRequest(BaseModel):
    decision: ConsentDecision
