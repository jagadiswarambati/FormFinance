"""Provider-neutral, response-safe privacy projection models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrivacySummary(BaseModel):
    """Immutable privacy-dashboard data with no document or answer content."""

    policy_version: str = Field(alias="policyVersion")
    provider_id: str = Field(alias="providerId")
    processing_mode: str = Field(alias="processingMode")
    safe_field_count: int = Field(ge=0, alias="safeFieldCount")
    restricted_field_count: int = Field(ge=0, alias="restrictedFieldCount")
    sensitive_field_count: int = Field(ge=0, alias="sensitiveFieldCount")
    ai_data_categories: tuple[str, ...] = Field(default_factory=tuple, alias="aiDataCategories")
    excluded_data_categories: tuple[str, ...] = Field(
        default_factory=tuple,
        alias="excludedDataCategories",
    )
    last_evaluated_at: datetime = Field(alias="lastEvaluatedAt")
    explanation_locale: str = Field(alias="explanationLocale")

    model_config = ConfigDict(populate_by_name=True, frozen=True)


class PrivacyAuditEvent(BaseModel):
    """Immutable, response-safe provenance for a privacy decision."""

    event_id: str = Field(alias="eventId")
    conversation_id: str = Field(alias="conversationId")
    event_type: str = Field(alias="eventType")
    policy_version: str = Field(alias="policyVersion")
    timestamp: datetime
    provider_id: str | None = Field(default=None, alias="providerId")
    processing_mode: str | None = Field(default=None, alias="processingMode")
    actor_type: str = Field(alias="actorType")
    explanation_key: str = Field(alias="explanationKey")

    model_config = ConfigDict(populate_by_name=True, frozen=True)
