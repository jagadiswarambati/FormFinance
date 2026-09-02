from formwise_api.ai_provider.models import AIProviderResult
from formwise_api.privacy.engine import scan_text
from formwise_api.understanding.models import StructuredDocument

SAFE_FALLBACK = "I can only answer from the protected structured document. Please review the relevant field or try a more specific question."


class ResponseValidator:
    def validate(self, result: AIProviderResult, document: StructuredDocument) -> tuple[str, list[str]]:
        reply = result.content.get("reply")
        referenced = result.content.get("referencedFieldIds")
        if not isinstance(reply, str) or not reply.strip() or not isinstance(referenced, list) or not all(isinstance(item, str) for item in referenced):
            return SAFE_FALLBACK, []
        field_ids = {field.id for field in document.fields}
        if not set(referenced).issubset(field_ids) or "[" in reply and "REDACTED" in reply.upper():
            return SAFE_FALLBACK, []
        if scan_text(reply):
            return SAFE_FALLBACK, []
        return reply.strip(), referenced
