import re

from formwise_api.understanding.models import SignatureStatus


class LabelBasedSignatureDetector:
    _present = re.compile(r"\b(?:signature|signed by)\b\s*[:#-]?\s*\S+", re.IGNORECASE)
    _missing = re.compile(r"\b(?:signature|sign here)\b\s*[:#-]?\s*(?:_{2,}|$)", re.IGNORECASE | re.MULTILINE)

    def detect(self, text: str) -> SignatureStatus:
        if self._present.search(text):
            return "present"
        if self._missing.search(text):
            return "missing"
        return "unknown"
