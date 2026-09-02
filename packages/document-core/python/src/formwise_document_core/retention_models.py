"""Provider-neutral, response-safe retention and purge lifecycle models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RetentionLifecycleState = Literal[
    "active",
    "revoked",
    "queued",
    "processing",
    "completed",
    "failed",
]
PurgeJobStatus = Literal["queued", "processing", "completed", "failed"]


class RetentionState(BaseModel):
    """Immutable retention lifecycle metadata for one conversation."""

    conversation_id: str = Field(alias="conversationId")
    state: RetentionLifecycleState
    revoked_at: datetime | None = Field(default=None, alias="revokedAt")
    queued_at: datetime | None = Field(default=None, alias="queuedAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_count: int = Field(default=0, ge=0, alias="failureCount")
    last_failure_at: datetime | None = Field(default=None, alias="lastFailureAt")

    model_config = ConfigDict(populate_by_name=True, frozen=True)


class RetentionJob(BaseModel):
    """Immutable identifier-only request for a conversation purge."""

    job_id: str = Field(alias="jobId")
    conversation_id: str = Field(alias="conversationId")
    created_at: datetime = Field(alias="createdAt")
    status: PurgeJobStatus
    retry_count: int = Field(default=0, ge=0, alias="retryCount")
    next_attempt_at: datetime | None = Field(default=None, alias="nextAttemptAt")
    request_id: str | None = Field(default=None, alias="requestId")

    model_config = ConfigDict(populate_by_name=True, frozen=True)


class PurgeStatus(BaseModel):
    """Response-safe purge lifecycle state without worker or storage details."""

    state: PurgeJobStatus
    queued_at: datetime | None = Field(default=None, alias="queuedAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    retry_count: int = Field(default=0, ge=0, alias="retryCount")

    model_config = ConfigDict(populate_by_name=True, frozen=True)
