from pathlib import Path

from formwise_worker.ocr.providers import OcrResult, ProviderDisabledError


class _DisabledOCRProvider:
    enabled = False
    name = "disabled"

    def extract(self, document_path: Path) -> OcrResult:
        raise ProviderDisabledError(f"{self.name} is not enabled.")


class GoogleVisionOCRProvider(_DisabledOCRProvider):
    name = "google_vision"


class AzureOCRProvider(_DisabledOCRProvider):
    name = "azure_ocr"


class AWSTextractOCRProvider(_DisabledOCRProvider):
    name = "aws_textract"


class TesseractOCRProvider(_DisabledOCRProvider):
    name = "tesseract"
