from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from uuid import uuid4

from formwise_api.conversations.models import Conversation, ConversationMessage


class ConversationRepository(Protocol):
    def create(self, user_id: str, document_id: str, locale: Literal["en", "hi", "te"], provider: str) -> Conversation: ...
    def get_for_owner(self, conversation_id: str, user_id: str) -> Conversation | None: ...
    def get_active_for_document(self, user_id: str, document_id: str) -> Conversation | None: ...
    def list_messages(self, conversation_id: str) -> list[ConversationMessage]: ...
    def save_message(self, message: ConversationMessage) -> None: ...
    def touch(self, conversation_id: str, status: str) -> None: ...
    def revoke(self, conversation_id: str) -> None: ...
    def revoke_excess(self, user_id: str, maximum: int = 5) -> list[Conversation]: ...
    def delete_conversation(self, conversation_id: str) -> None: ...
    def list_messages_for_document(self, user_id: str, document_id: str) -> list[ConversationMessage]: ...


class FirestoreConversationRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, user_id: str, document_id: str, locale: Literal["en", "hi", "te"], provider: str) -> Conversation:
        now = datetime.now(UTC)
        conversation = Conversation(id=uuid4().hex, user_id=user_id, document_id=document_id, status="ready", locale=locale, provider=provider, created_at=now, updated_at=now)
        self._client.collection("conversations").document(conversation.id).create(conversation.model_dump(by_alias=True, mode="python"))
        return conversation

    def get_for_owner(self, conversation_id: str, user_id: str) -> Conversation | None:
        snapshot = self._client.collection("conversations").document(conversation_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        if data.get("userId") != user_id or data.get("status") == "revoked":
            return None
        return Conversation.model_validate(data)

    def get_active_for_document(self, user_id: str, document_id: str) -> Conversation | None:
        query = self._client.collection("conversations").where("userId", "==", user_id).where("documentId", "==", document_id).where("status", "in", ["ready", "in_progress", "ready_to_render"]).limit(1)
        snapshot = next(iter(query.stream()), None)
        return Conversation.model_validate(snapshot.to_dict() or {}) if snapshot is not None else None

    def list_messages(self, conversation_id: str) -> list[ConversationMessage]:
        query = self._client.collection("messages").where("conversationId", "==", conversation_id).order_by("createdAt")
        return [ConversationMessage.model_validate(item.to_dict() or {}) for item in query.stream()]

    def save_message(self, message: ConversationMessage) -> None:
        self._client.collection("messages").document(message.id).create(message.model_dump(by_alias=True, mode="python"))

    def touch(self, conversation_id: str, status: str) -> None:
        self._client.collection("conversations").document(conversation_id).update({"status": status, "updatedAt": datetime.now(UTC)})

    def revoke(self, conversation_id: str) -> None:
        self._client.collection("conversations").document(conversation_id).update(
            {"status": "revoked", "revokedAt": datetime.now(UTC)}
        )

    def revoke_excess(self, user_id: str, maximum: int = 5) -> list[Conversation]:
        active = [Conversation.model_validate(item.to_dict() or {}) for item in self._client.collection("conversations").where("userId", "==", user_id).where("status", "in", ["ready", "in_progress", "ready_to_render"]).order_by("createdAt").stream()]
        revoked = active[:-maximum] if len(active) > maximum else []
        for conversation in revoked:
            self._client.collection("conversations").document(conversation.id).update({"status": "revoked", "revokedAt": datetime.now(UTC)})
        return revoked

    def delete_conversation(self, conversation_id: str) -> None:
        self._client.collection("conversations").document(conversation_id).delete()

    def list_messages_for_document(self, user_id: str, document_id: str) -> list[ConversationMessage]:
        messages: list[ConversationMessage] = []
        conversations = self._client.collection("conversations").where("userId", "==", user_id).where("documentId", "==", document_id).where("status", "in", ["ready", "in_progress", "ready_to_render"]).stream()
        for conversation in conversations:
            messages.extend(self.list_messages(conversation.id))
        return sorted(messages, key=lambda message: message.created_at)

    def delete_where(self, collection: str, field: str, value: str) -> None:
        for snapshot in self._client.collection(collection).where(field, "==", value).stream():
            snapshot.reference.delete()
