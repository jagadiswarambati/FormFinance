from pathlib import Path
from typing import Any, TypeAlias

import fitz
from PIL import Image, ImageDraw, ImageFont


RenderData: TypeAlias = dict[str, Any]
FieldMap: TypeAlias = list[RenderData]
Assignments: TypeAlias = list[RenderData]


class _Base:
    name: str

    def _eligible(
        self,
        field: RenderData,
        assignment: RenderData,
    ) -> bool:
        metadata = field.get("renderMetadata", {})
        return (
            isinstance(metadata, dict)
            and metadata.get("privacyTier") == "safe"
            and assignment.get("status") == "approved"
        )

    def _box(self, metadata: RenderData) -> fitz.Rect | None:
        bounds = metadata.get("cellBounds") or metadata.get("boundingBox")

        if not isinstance(bounds, dict):
            return None

        x = bounds.get("x")
        y = bounds.get("y")
        width = bounds.get("width")
        height = bounds.get("height")

        if not isinstance(x, (int, float)):
          return None
        if not isinstance(y, (int, float)):
          return None
        if not isinstance(width, (int, float)):
          return None
        if not isinstance(height, (int, float)):
          return None

        return fitz.Rect(
          float(x),
          float(y),
          float(x) + float(width),
          float(y) + float(height),
        )


class FillablePDFRenderer(_Base):
    name = "fillable_pdf"

    def render(
        self,
        original: Path,
        output: Path,
        field_map: FieldMap,
        assignments: Assignments,
    ) -> tuple[int, list[str]]:
        doc = fitz.open(original)
        warnings: list[str] = []

        for assignment in assignments:
            field = next(
                (
                    item
                    for item in field_map
                    if item.get("id") == assignment.get("fieldId")
                ),
                None,
            )

            if not field or not self._eligible(field, assignment):
                warnings.append(str(assignment.get("fieldId")))
                continue

            metadata = field.get("renderMetadata", {})
            if not isinstance(metadata, dict):
                warnings.append(
                    f"RENDER_METADATA_INVALID:{assignment.get('fieldId')}"
                )
                continue

            widget_id = metadata.get("widgetId")
            widget_xref = metadata.get("widgetXref")
            page_number = metadata.get("pageNumber")
            expected_type = metadata.get("widgetType")

            if (
                not isinstance(widget_xref, int)
                or not isinstance(page_number, int)
                or page_number < 1
                or page_number > len(doc)
            ):
                warnings.append(
                    f"WIDGET_REFERENCE_INVALID:{assignment.get('fieldId')}"
                )
                continue

            try:
                widget = doc[page_number - 1].load_widget(widget_xref)
            except (RuntimeError, ValueError):
                widget = None

            if (
                not widget
                or widget.field_name != widget_id
                or (
                    expected_type is not None
                    and str(widget.field_type) != str(expected_type)
                )
            ):
                warnings.append(
                    f"WIDGET_MISMATCH:{assignment.get('fieldId')}"
                )
                continue

            value = assignment.get("value", "")

            if (
                metadata.get("fieldType") == "checkbox"
                and str(value).lower() in {"checked", "true", "yes"}
            ):
                widget.field_value = "Yes"
            else:
                widget.field_value = str(value)

            widget.update()

        doc.save(output)
        return len(doc), warnings


class StaticPDFRenderer(_Base):
    name = "static_pdf"

    def render(
        self,
        original: Path,
        output: Path,
        field_map: FieldMap,
        assignments: Assignments,
    ) -> tuple[int, list[str]]:
        doc = fitz.open(original)
        warnings: list[str] = []

        for assignment in assignments:
            field = next(
                (
                    item
                    for item in field_map
                    if item.get("id") == assignment.get("fieldId")
                ),
                None,
            )

            if not field or not self._eligible(field, assignment):
                warnings.append(str(assignment.get("fieldId")))
                continue

            metadata = field.get("renderMetadata", {})
            if not isinstance(metadata, dict):
                warnings.append(str(assignment.get("fieldId")))
                continue

            rect = self._box(metadata)

            try:
                page_number = int(metadata.get("pageNumber", 0)) - 1
            except (TypeError, ValueError):
                page_number = -1

            if rect is None or page_number < 0 or page_number >= len(doc):
                warnings.append(str(assignment.get("fieldId")))
                continue

            value = assignment.get("value", "")

            if (
                metadata.get("fieldType") == "checkbox"
                and str(value).lower() in {"checked", "true", "yes"}
            ):
                text = "✓"
            else:
                text = str(value)

            alignment = {
                "left": 0,
                "center": 1,
                "right": 2,
            }.get(str(metadata.get("textAlignment")), 0)

            doc[page_number].insert_textbox(
                rect,
                text,
                fontsize=10,
                align=alignment,
                fontname="helv",
            )

        doc.save(output)
        return len(doc), warnings


class ImageRenderer(_Base):
    name = "image"

    def render(
        self,
        original: Path,
        output: Path,
        field_map: FieldMap,
        assignments: Assignments,
    ) -> tuple[int, list[str]]:
        image = Image.open(original).convert("RGB")
        draw = ImageDraw.Draw(image)
        warnings: list[str] = []

        for assignment in assignments:
            field = next(
                (
                    item
                    for item in field_map
                    if item.get("id") == assignment.get("fieldId")
                ),
                None,
            )

            if not field or not self._eligible(field, assignment):
                warnings.append(str(assignment.get("fieldId")))
                continue

            metadata = field.get("renderMetadata", {})
            if not isinstance(metadata, dict):
                warnings.append(str(assignment.get("fieldId")))
                continue

            bounds = metadata.get("cellBounds") or metadata.get("boundingBox")

            if not isinstance(bounds, dict):
                warnings.append(str(assignment.get("fieldId")))
                continue

            x = bounds.get("x")
            y = bounds.get("y")

            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                warnings.append(str(assignment.get("fieldId")))
                continue

            if metadata.get("fieldType") == "checkbox":
                text = "✓"
            else:
                text = str(assignment.get("value", ""))

            draw.text(
                (float(x), float(y)),
                text,
                fill="black",
                font=ImageFont.load_default(),
            )

        image.save(output)
        return 1, warnings