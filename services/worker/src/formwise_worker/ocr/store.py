import json
from pathlib import Path

from formwise_worker.ocr.providers import OcrLayoutToken


class LocalOcrResultStore:
    def __init__(self, directory: str) -> None:
        self._directory = Path(directory)

    def write(self, document_id: str, text: str) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        filename = f"{document_id}.txt"
        path = self._directory / filename
        path.write_text(text, encoding="utf-8")
        return str(path)

    def read(self, storage_key: str) -> str:
        """Read an OCR result previously written by this store."""
        return Path(storage_key).read_text(encoding="utf-8")

    def write_layout(self, document_id: str, tokens: tuple[OcrLayoutToken, ...]) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{document_id}.layout.json"
        path.write_text(json.dumps([token.__dict__ for token in tokens]), encoding="utf-8")
        return str(path)
