from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UploadIntentRequest(BaseModel):
    original_filename: str = Field(min_length=1, max_length=255, alias="originalFilename")
    content_type: str = Field(alias="contentType")
    file_size: int = Field(gt=0, le=10 * 1024 * 1024, alias="fileSize")

    model_config = ConfigDict(populate_by_name=True)


class UploadIntentResponse(BaseModel):
    document_id: str = Field(alias="documentId")
    upload_url: str = Field(alias="uploadUrl")
    expires_at: datetime = Field(alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)


class DocumentResponse(BaseModel):
    document_id: str = Field(alias="documentId")
    owner_uid: str = Field(alias="ownerUid")
    original_filename: str = Field(alias="originalFilename")
    stored_filename: str = Field(alias="storedFilename")
    content_type: str = Field(alias="contentType")
    file_size: int = Field(alias="fileSize")
    uploaded_at: datetime = Field(alias="uploadedAt")
    status: str
    quarantine_status: str = Field(default="not_quarantined", alias="quarantineStatus")
    scan_status: str = Field(default="not_requested", alias="scanStatus")
    scan_started_at: datetime | None = Field(default=None, alias="scanStartedAt")
    scan_completed_at: datetime | None = Field(default=None, alias="scanCompletedAt")
    scan_provider: str | None = Field(default=None, alias="scanProvider")
    scan_reason: str | None = Field(default=None, alias="scanReason")
    ocr_status: str = Field(default="not_started", alias="ocrStatus")
    ocr_started_at: datetime | None = Field(default=None, alias="ocrStartedAt")
    ocr_completed_at: datetime | None = Field(default=None, alias="ocrCompletedAt")
    ocr_provider: str | None = Field(default=None, alias="ocrProvider")
    ocr_confidence: float | None = Field(default=None, alias="ocrConfidence")
    text_length: int | None = Field(default=None, alias="textLength")
    ocr_text_storage_key: str | None = Field(default=None, alias="ocrTextStorageKey")
    ocr_layout_storage_key: str | None = Field(default=None, alias="ocrLayoutStorageKey")
    protected_layout_storage_key: str | None = Field(default=None, alias="protectedLayoutStorageKey")
    privacy_status: str = Field(default="not_started", alias="privacyStatus")
    privacy_completed_at: datetime | None = Field(default=None, alias="privacyCompletedAt")
    privacy_policy_version: str | None = Field(default=None, alias="privacyPolicyVersion")
    pii_categories: list[str] = Field(default_factory=list, alias="piiCategories")
    redacted_text_storage_key: str | None = Field(default=None, alias="redactedTextStorageKey")
    consent_decision: str | None = Field(default=None, alias="consentDecision")

    model_config = ConfigDict(populate_by_name=True)


class OcrStatusResponse(BaseModel):
    status: str
    provider: str | None
    confidence: float | None
    text_length: int | None = Field(alias="textLength")

    model_config = ConfigDict(populate_by_name=True)
