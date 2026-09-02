from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NativePdfWidgetMetadata:
    widget_id: str
    widget_xref: int
    page_number: int
    widget_type: str | None
    widget_appearance: dict[str, str]


class NativeFillablePdfExtractor:
    """Extracts immutable, value-free widget metadata for Field Map projection."""

    def extract(self, document_path: Path) -> list[NativePdfWidgetMetadata]:
        import fitz

        document = fitz.open(document_path)
        widgets: list[NativePdfWidgetMetadata] = []
        for page_number, page in enumerate(document, start=1):
            for widget in page.widgets() or []:
                if not widget.field_name or not widget.xref:
                    continue
                appearance = {"fieldFlags": str(widget.field_flags)}
                widgets.append(NativePdfWidgetMetadata(widget_id=widget.field_name, widget_xref=widget.xref, page_number=page_number, widget_type=str(widget.field_type), widget_appearance=appearance))
        return widgets
