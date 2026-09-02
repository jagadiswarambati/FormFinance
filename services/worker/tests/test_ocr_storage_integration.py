from pathlib import Path

from formwise_worker.ocr.providers import OcrLayoutToken
from formwise_worker.ocr.store import LocalOcrResultStore


def test_local_ocr_store_persists_text_and_layout_artifacts(tmp_path: Path) -> None:
    store = LocalOcrResultStore(str(tmp_path))

    text_key = store.write("document-1", "Synthetic OCR text")
    layout_key = store.write_layout(
        "document-1",
        (
            OcrLayoutToken("Synthetic", 1, 0, 0, 10, 10, 0.99, 0),
        ),
    )

    assert Path(text_key).read_text(encoding="utf-8") == "Synthetic OCR text"
    assert '"page": 1' in Path(layout_key).read_text(encoding="utf-8")
