from datetime import UTC, datetime
from uuid import uuid4

from formwise_api.ai_provider.interfaces import AIProvider
from formwise_api.conversations.context import ContextBuilder
from formwise_api.conversations.models import (
    ChatResponse,
    Conversation,
    ConversationMessage,
    MessageRole,
)
from formwise_api.conversations.prompt import PromptBuilder
from formwise_api.conversations.repository import ConversationRepository
from formwise_api.conversations.validator import SAFE_FALLBACK, ResponseValidator
from formwise_api.documents.repository import DocumentRepository
from formwise_api.privacy.engine import redact_text, scan_text
from formwise_api.privacy.refresher import PrivacySummaryRefresher
from formwise_api.retention.service import RetentionOrchestrator
from formwise_api.understanding.repository import UnderstandingRepository


class ConversationService:
    def __init__(self, conversations: ConversationRepository, structured_documents: UnderstandingRepository, provider: AIProvider, retention: RetentionOrchestrator, documents: DocumentRepository | None = None, privacy_refresher: PrivacySummaryRefresher | None = None) -> None:
        self._conversations = conversations
        self._structured_documents = structured_documents
        self._provider = provider
        self._retention = retention
        self._context = ContextBuilder()
        self._prompts = PromptBuilder()
        self._validator = ResponseValidator()
        self._documents = documents
        self._privacy_refresher = privacy_refresher

    def create(self, user_id: str, document_id: str, locale: str) -> Conversation:
        if self._structured_documents.get(document_id) is None:
            raise ValueError("The document must be structured before a conversation can begin.")
        existing = self._conversations.get_active_for_document(user_id, document_id)
        if existing is not None:
            return existing
        if locale not in {"en", "hi", "te"}:
            locale = "en"
        from typing import Literal, cast
        conversation = self._conversations.create(user_id, document_id, cast(Literal["en", "hi", "te"], locale), self._provider.provider_name())
        self._retention.enforce_quota(user_id)
        return conversation

    def get_for_owner(self, conversation_id: str, user_id: str) -> Conversation | None:
        return self._conversations.get_for_owner(conversation_id, user_id)

    async def ask(self, conversation: Conversation, user_message: str) -> ChatResponse:
        findings = scan_text(user_message)
        if findings:
            self._save(conversation.id, "user", redact_text(user_message, findings))
            self._save(conversation.id, "assistant", "For your privacy, please do not include personal or sensitive values in chat. I can explain the protected structured document without them.")
            return ChatResponse(reply="For your privacy, please do not include personal or sensitive values in chat. I can explain the protected structured document without them.", conversation_id=conversation.id)
        document = self._structured_documents.get(conversation.document_id)
        if document is None:
            return ChatResponse(reply=SAFE_FALLBACK, conversation_id=conversation.id)
        history = self._conversations.list_messages(conversation.id)
        context, safe_history = self._context.build(document, history)
        self._save(conversation.id, "user", user_message)
        self._conversations.touch(conversation.id, "in_progress")
        provider_completed = False
        try:
            result = await self._provider.generate_response(self._prompts.build(context, safe_history, user_message, conversation.locale, uuid4().hex))
            reply, field_ids = self._validator.validate(result, document)
            self._save(conversation.id, "assistant", reply, field_ids, result.provider, result.token_usage, result.latency_ms)
            provider_completed = True
        except Exception:
            reply = SAFE_FALLBACK
            self._save(conversation.id, "assistant", reply)
        self._conversations.touch(conversation.id, "in_progress")
        if provider_completed and self._documents is not None and self._privacy_refresher is not None:
            persisted_document = self._documents.get_for_owner(conversation.document_id, conversation.user_id)
            if persisted_document is not None:
                self._privacy_refresher.refresh(conversation, persisted_document)
        return ChatResponse(reply=reply, conversation_id=conversation.id)

    def history(self, conversation: Conversation) -> list[ConversationMessage]:
        return self._conversations.list_messages(conversation.id)

    def delete(self, conversation: Conversation) -> None:
        self._retention.revoke_and_enqueue(conversation)

    def _save(self, conversation_id: str, role: MessageRole, content: str, field_ids: list[str] | None = None, provider: str | None = None, token_usage: int | None = None, latency_ms: int | None = None) -> None:
        self._conversations.save_message(ConversationMessage(id=uuid4().hex, conversation_id=conversation_id, role=role, safe_content=content, field_ids=field_ids or [], provider=provider, token_usage=token_usage, latency_ms=latency_ms, created_at=datetime.now(UTC)))
