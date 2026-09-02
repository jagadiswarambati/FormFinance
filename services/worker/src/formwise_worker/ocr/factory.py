from formwise_worker.ocr.paddle import PaddleOCRProvider
from formwise_worker.ocr.providers import OCRProvider


def get_ocr_provider(provider_name: str) -> OCRProvider:
    if provider_name == "paddleocr":
        return PaddleOCRProvider()
    raise RuntimeError(f"OCR provider '{provider_name}' is disabled or unknown.")
