from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RenderValidationReport(BaseModel):
    valid: bool
    rendered_assignment_ids: list[str] = Field(default_factory=list, alias="renderedAssignmentIds")
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)


class RenderRecord(BaseModel):
    id: str
    document_id: str = Field(alias="documentId")
    renderer_type: Literal["fillable_pdf", "static_pdf", "image"] = Field(alias="rendererType")
    render_status: Literal["queued", "processing", "completed", "failed"] = Field(alias="renderStatus")
    validation_result: RenderValidationReport = Field(alias="validationResult")
    page_count: int = Field(alias="pageCount")
    preview_key: str | None = Field(default=None, alias="previewKey")
    output_key: str | None = Field(default=None, alias="outputKey")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    render_version: str = Field(alias="renderVersion")
    model_config = ConfigDict(populate_by_name=True)


class RenderResult(BaseModel):
    record: RenderRecord
    validation: RenderValidationReport
    error_code: str | None = Field(default=None, alias="errorCode")
    model_config = ConfigDict(populate_by_name=True)
