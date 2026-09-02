from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Protocol
from uuid import uuid4

from formwise_document_core.rendering_models import (
    RenderRecord,
    RenderResult,
    RenderValidationReport,
)
from formwise_document_core.rendering_validator import RenderValidator


class RenderArtifactStore(Protocol):
    def original_path(self, document_id: str) -> Path | None: ...
    def output_path(self, render_id: str, renderer_type: str) -> Path: ...
    def temporary_output_path(self, render_id: str, execution_token: str, renderer_type: str) -> Path: ...
    def promote(self, temporary: Path, final: Path) -> None: ...
    def discard(self, temporary: Path) -> None: ...
    def open_completed_artifact(self, output_key: str) -> BinaryIO | None:
        """Open the completed artifact identified by ``RenderRecord.output_key``.

        ``None`` indicates that the artifact is unavailable. Callers own the
        returned stream and must close it after reading.
        """
        ...


class RenderRecordRepository(Protocol):
    def save(self, record: RenderRecord) -> None: ...
    def is_active_execution(self, render_id: str, execution_token: str) -> bool: ...


class RendererSelector(Protocol):
    def select(self, content_type: str, widget_fields: bool) -> Any: ...


class RenderService:
    def __init__(self, validator: RenderValidator, factory: RendererSelector, artifacts: RenderArtifactStore, records: RenderRecordRepository, coordinate_threshold: float) -> None:
        self._validator, self._factory, self._artifacts, self._records, self._threshold = validator, factory, artifacts, records, coordinate_threshold

    def render(self, document_id: str, content_type: str, field_map: list[dict[str, Any]], assignments: list[dict[str, Any]], render_id: str | None = None, execution_token: str | None = None) -> RenderResult:
        render_id, now, execution_token = render_id or uuid4().hex, datetime.now(UTC), execution_token or uuid4().hex
        original = self._artifacts.original_path(document_id)
        widget_fields = any(isinstance(field.get("renderMetadata"), dict) and field["renderMetadata"].get("widgetId") for field in field_map)
        renderer_type = "fillable_pdf" if content_type == "application/pdf" and widget_fields else "static_pdf" if content_type == "application/pdf" else "image"
        try:
            renderer = self._factory.select(content_type, widget_fields)
            page_count = self._page_count(original, content_type) if original else 0
            validation = self._validator.validate(original is not None, True, renderer_type, page_count, field_map, assignments, self._threshold)
            if not validation.valid:
                return self._persist(render_id, document_id, renderer_type, "failed", validation, 0, now, "VALIDATION_FAILED")
            output = self._artifacts.output_path(render_id, renderer_type)
            temporary = self._artifacts.temporary_output_path(render_id, execution_token, renderer_type)
            pages, warnings = renderer.render(original, temporary, field_map, assignments)
            validation.warnings.extend(warnings)
            if not self._records.is_active_execution(render_id, execution_token):
                self._artifacts.discard(temporary)
                return RenderResult(record=RenderRecord(id=render_id, document_id=document_id, renderer_type=renderer_type, render_status="failed", validation_result=validation, page_count=0, started_at=now, completed_at=datetime.now(UTC), render_version="v1"), validation=validation, error_code="STALE_EXECUTION")
            self._artifacts.promote(temporary, output)
            return self._persist(render_id, document_id, renderer_type, "completed", validation, pages, now, None, str(output))
        except ValueError as error:
            return self._persist(render_id, document_id, renderer_type, "failed", RenderValidationReport(valid=False, errors=[str(error)]), 0, now, "RENDER_UNSUPPORTED")
        except (OSError, RuntimeError):
            return self._persist(render_id, document_id, renderer_type, "failed", RenderValidationReport(valid=False, errors=["RENDER_IO_FAILURE"]), 0, now, "RENDER_IO_FAILURE")

    def _persist(self, render_id: str, document_id: str, renderer_type: str, status: str, validation: RenderValidationReport, pages: int, started: datetime, error: str | None, output: str | None = None) -> RenderResult:
        record = RenderRecord(id=render_id, document_id=document_id, renderer_type=renderer_type, render_status=status, validation_result=validation, page_count=pages, output_key=output, started_at=started, completed_at=datetime.now(UTC), render_version="v1")
        try:
            self._records.save(record)
        except OSError:
            return RenderResult(record=record, validation=validation, error_code="REPOSITORY_FAILURE")
        return RenderResult(record=record, validation=validation, error_code=error)

    @staticmethod
    def _page_count(path: Path | None, content_type: str) -> int:
        if path is None:
            return 0
        if content_type == "application/pdf":
            import fitz
            return len(fitz.open(path))
        return 1
