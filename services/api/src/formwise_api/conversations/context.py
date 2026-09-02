import re

from formwise_api.conversations.models import ConversationMessage
from formwise_api.understanding.models import StructuredDocument


class ContextBuilder:
    _redacted = re.compile(r"\[[A-Z_ ]+REDACTED\]")

    def build(self, document: StructuredDocument, history: list[ConversationMessage]) -> tuple[dict[str, object], list[dict[str, str]]]:
        context = self._clean(document.model_dump(by_alias=True, mode="json"))
        if not isinstance(context, dict):
            context = {}
        safe_history = [{"role": message.role, "content": message.safe_content} for message in history if message.role in {"user", "assistant"}][-12:]
        return context, safe_history

    def _clean(self, value: object) -> object:
        if isinstance(value, str):
            return None if self._redacted.search(value) else value
        if isinstance(value, list):
            return [cleaned for item in value if (cleaned := self._clean(item)) is not None]
        if isinstance(value, dict):
            return {key: cleaned for key, item in value.items() if (cleaned := self._clean(item)) is not None}
        return value
