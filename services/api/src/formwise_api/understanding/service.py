from pathlib import Path

from formwise_api.understanding.models import StructuredDocument
from formwise_api.understanding.pipeline import UnderstandingPipeline
from formwise_api.understanding.repository import UnderstandingRepository


class UnderstandingService:
    def __init__(self, repository: UnderstandingRepository, pipeline: UnderstandingPipeline, provider_version: str) -> None:
        self._repository = repository
        self._pipeline = pipeline
        self._provider_version = provider_version

    def understand(self, document_id: str, protected_text_storage_key: str, protected_layout_storage_key: str | None, original_pdf_path: Path | None = None) -> StructuredDocument:
        protected_text = Path(protected_text_storage_key).read_text(encoding="utf-8")
        structured = self._pipeline.understand(document_id, protected_text, self._provider_version, protected_layout_storage_key, original_pdf_path)
        self._repository.save(structured)
        return structured
