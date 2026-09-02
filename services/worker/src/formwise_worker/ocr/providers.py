from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None
    layout_tokens: tuple["OcrLayoutToken", ...] = ()


@dataclass(frozen=True)
class OcrLayoutToken:
    text: str
    page: int
    x: float
    y: float
    width: float
    height: float
    confidence: float | None
    reading_order: int
    region_type: str = "text"
    table_id: str | None = None
    widget_id: str | None = None


class OCRProvider(Protocol):
    name: str
    enabled: bool

    def extract(self, document_path: Path) -> OcrResult: ...


class ProviderDisabledError(RuntimeError):
    pass
