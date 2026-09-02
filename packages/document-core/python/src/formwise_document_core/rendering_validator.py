from typing import Any

from formwise_document_core.rendering_models import RenderValidationReport


class RenderValidator:
    """Validates immutable Field Map v1 placements without discovering document data."""

    def validate(self, document_exists: bool, renderer_available: bool, renderer_type: str, page_count: int, field_map: list[dict[str, Any]], assignments: list[dict[str, Any]], coordinate_threshold: float) -> RenderValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        rendered: list[str] = []
        if not document_exists:
            errors.append("DOCUMENT_NOT_FOUND")
        if not renderer_available or renderer_type not in {"fillable_pdf", "static_pdf", "image"}:
            errors.append("RENDERER_UNAVAILABLE")
        fields = {str(field.get("id")): field for field in field_map}
        regions: list[tuple[int, float, float, float, float]] = []
        for assignment in assignments:
            assignment_id = str(assignment.get("id", "unknown"))
            if assignment.get("status") != "approved":
                continue
            field = fields.get(str(assignment.get("fieldId")))
            if field is None:
                errors.append(f"FIELD_NOT_FOUND:{assignment_id}")
                continue
            metadata = field.get("renderMetadata") if isinstance(field.get("renderMetadata"), dict) else {}
            if metadata.get("privacyTier") != "safe":
                warnings.append(f"MANUAL_ONLY:{assignment_id}")
                continue
            if metadata.get("fieldType") not in {"text", "checkbox", "table_cell", "date"}:
                errors.append(f"UNSUPPORTED_FIELD_TYPE:{assignment_id}")
                continue
            widget_xref = metadata.get("widgetXref")
            if isinstance(widget_xref, int):
                page = metadata.get("pageNumber")
                if (
                    not isinstance(metadata.get("widgetId"), str)
                    or not isinstance(metadata.get("widgetType"), str)
                    or not isinstance(page, int)
                    or page < 1
                    or page > page_count
                ):
                    errors.append(f"INVALID_WIDGET_REFERENCE:{assignment_id}")
                    continue
                rendered.append(assignment_id)
                continue
            if metadata.get("coordinateConfidence", 0) < coordinate_threshold:
                warnings.append(f"LOW_COORDINATE_CONFIDENCE:{assignment_id}")
                continue
            page, box = metadata.get("pageNumber"), metadata.get("cellBounds") or metadata.get("boundingBox")
            if not isinstance(page, int) or page < 1 or page > page_count or not isinstance(box, dict):
                errors.append(f"INVALID_PLACEMENT:{assignment_id}")
                continue
            try:
                x, y, width, height = (float(box[key]) for key in ("x", "y", "width", "height"))
            except (KeyError, TypeError, ValueError):
                errors.append(f"INVALID_BOUNDING_BOX:{assignment_id}")
                continue
            if width <= 0 or height <= 0 or x < 0 or y < 0 or any(page == p and x < ox + ow and x + width > ox and y < oy + oh and y + height > oy for p, ox, oy, ow, oh in regions):
                errors.append(f"INVALID_OR_OVERLAPPING_REGION:{assignment_id}")
                continue
            regions.append((page, x, y, width, height))
            rendered.append(assignment_id)
        return RenderValidationReport(valid=not errors, rendered_assignment_ids=rendered, warnings=warnings, errors=errors)
