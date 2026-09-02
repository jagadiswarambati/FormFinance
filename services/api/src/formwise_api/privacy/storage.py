import json
from pathlib import Path


class LocalPrivacyTextStore:
    def __init__(self, directory: str) -> None:
        self._directory = Path(directory)

    def read_ocr(self, storage_key: str) -> str:
        return Path(storage_key).read_text(encoding="utf-8")

    def write_protected(self, document_id: str, text: str) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{document_id}.protected.txt"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def write_protected_layout(self, document_id: str, tokens: list[dict[str, object]]) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{document_id}.protected-layout.json"
        path.write_text(json.dumps(tokens), encoding="utf-8")
        return str(path)

    @staticmethod
    def read_layout(storage_key: str) -> list[dict[str, object]]:
        parsed = json.loads(Path(storage_key).read_text(encoding="utf-8"))
        return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []
