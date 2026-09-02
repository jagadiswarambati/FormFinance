import json
from pathlib import Path

from formwise_api.understanding.models import PageBoundingBox, StructuredField
from formwise_api.understanding.native_projection import NativeWidgetProjection


class LayoutFieldMapBuilder:
    def attach(self, fields: list[StructuredField], protected_layout_key: str | None, native_widgets: NativeWidgetProjection | None = None) -> list[StructuredField]:
        if not protected_layout_key:
            return [field.model_copy(update={"render_metadata": field.render_metadata.model_copy(update={"widget_id": native.widget_id, "widget_xref": native.widget_xref, "page_number": native.page_number, "widget_type": native.widget_type, "widget_appearance": native.widget_appearance})}) if native_widgets and (native := native_widgets.match(field.render_metadata.widget_id, field.label)) else field for field in fields]
        parsed = json.loads(Path(protected_layout_key).read_text(encoding="utf-8"))
        tokens = [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []
        mapped: list[StructuredField] = []
        for field in fields:
            token = next((item for item in tokens if isinstance(item.get("text"), str) and item["text"].strip().casefold() == field.label.casefold()), None)
            if token is None:
                native = native_widgets.match(field.render_metadata.widget_id, field.label) if native_widgets else None
                if native:
                    metadata = field.render_metadata.model_copy(update={"widget_id": native.widget_id, "widget_xref": native.widget_xref, "page_number": native.page_number, "widget_type": native.widget_type, "widget_appearance": native.widget_appearance})
                    mapped.append(field.model_copy(update={"render_metadata": metadata}))
                else:
                    mapped.append(field)
                continue
            val = token.get("confidence")
            confidence = float(val) if isinstance(val, (int, float)) else 0.0
            box = PageBoundingBox(page=int(token.get("page", 1)), x=float(token.get("x", 0)), y=float(token.get("y", 0)), width=float(token.get("width", 0)), height=float(token.get("height", 0)))
            metadata = field.render_metadata.model_copy(update={"page_number": box.page, "bounding_box": box, "widget_id": token.get("widget_id") if isinstance(token.get("widget_id"), str) else None, "coordinate_confidence": confidence})
            native = native_widgets.match(metadata.widget_id, field.label) if native_widgets else None
            if native:
                metadata = metadata.model_copy(update={"widget_id": native.widget_id, "widget_xref": native.widget_xref, "page_number": native.page_number, "widget_type": native.widget_type, "widget_appearance": native.widget_appearance})
            mapped.append(field.model_copy(update={"render_metadata": metadata}))
        return mapped
