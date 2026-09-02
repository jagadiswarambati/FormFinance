from pathlib import Path

import fitz
from PIL import Image

from formwise_worker.rendering.renderers import ImageRenderer, StaticPDFRenderer


def _field_map() -> list[dict[str, object]]:
    return [
        {
            "id": "name",
            "renderMetadata": {
                "privacyTier": "safe",
                "coordinateConfidence": 0.95,
                "pageNumber": 1,
                "boundingBox": {"x": 40, "y": 40, "width": 180, "height": 30},
                "fieldType": "text",
                "textAlignment": "left",
            },
        }
    ]


def _assignments() -> list[dict[str, str]]:
    return [{"fieldId": "name", "status": "approved", "value": "Synthetic User"}]


def test_static_pdf_renderer_preserves_the_golden_page_geometry(tmp_path: Path) -> None:
    original = tmp_path / "synthetic.pdf"
    rendered = tmp_path / "rendered.pdf"
    document = fitz.open()
    document.new_page(width=300, height=200)
    document.save(original)

    pages, warnings = StaticPDFRenderer().render(original, rendered, _field_map(), _assignments())

    output = fitz.open(rendered)
    assert pages == 1
    assert warnings == []
    assert len(output) == 1
    assert output[0].rect == fitz.Rect(0, 0, 300, 200)
    assert "Synthetic User" in output[0].get_text()


def test_image_renderer_writes_only_within_the_synthetic_field_map_bounds(tmp_path: Path) -> None:
    original = tmp_path / "synthetic.png"
    rendered = tmp_path / "rendered.png"
    Image.new("RGB", (300, 200), "white").save(original)

    pages, warnings = ImageRenderer().render(original, rendered, _field_map(), _assignments())

    image = Image.open(rendered)
    assert pages == 1
    assert warnings == []
    assert image.size == (300, 200)
    assert image.getbbox() == (0, 0, 300, 200)
