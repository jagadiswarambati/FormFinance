from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentType = Literal["government_form", "application_form", "certificate", "identity_document", "academic_record", "medical_form", "financial_form", "unknown"]
CheckState = Literal["checked", "unchecked", "unknown"]
SignatureStatus = Literal["present", "missing", "unknown"]


class BoundingRegion(BaseModel):
    start: int
    end: int


class PageBoundingBox(BaseModel):
    page: int
    x: float
    y: float
    width: float
    height: float


class FieldRenderMetadata(BaseModel):
    page_number: int | None = Field(default=None, alias="pageNumber")
    bounding_box: PageBoundingBox | None = Field(default=None, alias="boundingBox")
    widget_id: str | None = Field(default=None, alias="widgetId")
    widget_xref: int | None = Field(default=None, alias="widgetXref", ge=1)
    coordinate_confidence: float = Field(default=0, alias="coordinateConfidence", ge=0, le=1)
    privacy_tier: Literal["safe", "restricted", "sensitive"] = Field(default="safe", alias="privacyTier")
    privacy_reason: str = Field(default="Pending policy classification", alias="privacyReason")
    field_type: Literal["text", "checkbox", "table_cell", "date", "signature_placeholder", "unknown"] = Field(default="unknown", alias="fieldType")
    text_alignment: Literal["left", "center", "right"] = Field(default="left", alias="textAlignment")
    multiline: bool = False
    overflow_policy: Literal["wrap", "shrink", "clip", "manual_only"] = Field(default="manual_only", alias="overflowPolicy")
    table_id: str | None = Field(default=None, alias="tableId")
    row_index: int | None = Field(default=None, alias="rowIndex")
    column_index: int | None = Field(default=None, alias="columnIndex")
    cell_bounds: PageBoundingBox | None = Field(default=None, alias="cellBounds")
    checkbox_mapping: dict[str, str] = Field(default_factory=dict, alias="checkboxMapping")
    widget_type: str | None = Field(default=None, alias="widgetType")
    widget_appearance: dict[str, str] = Field(default_factory=dict, alias="widgetAppearance")

    model_config = ConfigDict(populate_by_name=True)


class StructuredField(BaseModel):
    id: str
    label: str
    value: str | None = None
    normalized_value: str | None = Field(default=None, alias="normalizedValue")
    section_id: str | None = Field(default=None, alias="sectionId")
    confidence: float
    region: BoundingRegion | None = None
    required: bool = False
    render_metadata: FieldRenderMetadata = Field(default_factory=FieldRenderMetadata, alias="renderMetadata")

    model_config = ConfigDict(populate_by_name=True)


class StructuredSection(BaseModel):
    id: str
    title: str
    start: int
    end: int
    field_ids: list[str] = Field(default_factory=list, alias="fieldIds")

    model_config = ConfigDict(populate_by_name=True)


class StructuredTable(BaseModel):
    id: str
    section_id: str | None = Field(default=None, alias="sectionId")
    headers: list[str]
    rows: list[list[str]]
    confidence: float

    model_config = ConfigDict(populate_by_name=True)


class StructuredCheckbox(BaseModel):
    id: str
    label: str
    state: CheckState
    section_id: str | None = Field(default=None, alias="sectionId")
    confidence: float

    model_config = ConfigDict(populate_by_name=True)


class MissingField(BaseModel):
    field_id: str = Field(alias="fieldId")
    label: str
    certainty: Literal["missing", "potentially_missing"]
    confidence: float

    model_config = ConfigDict(populate_by_name=True)


class ConfidenceSummary(BaseModel):
    overall: float
    fields: float
    tables: float
    checkboxes: float


class StructuredDocument(BaseModel):
    document_id: str = Field(alias="documentId")
    document_type: DocumentType = Field(alias="documentType")
    sections: list[StructuredSection]
    fields: list[StructuredField]
    tables: list[StructuredTable]
    checkboxes: list[StructuredCheckbox]
    signature_status: SignatureStatus = Field(alias="signatureStatus")
    missing_fields: list[MissingField] = Field(alias="missingFields")
    confidence_summary: ConfidenceSummary = Field(alias="confidenceSummary")
    processing_status: Literal["completed", "failed"] = Field(alias="processingStatus")
    provider_version: str = Field(alias="providerVersion")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)
