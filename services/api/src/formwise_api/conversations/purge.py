from pathlib import Path
from typing import Any

from formwise_api.conversations.models import Conversation
from formwise_api.conversations.repository import FirestoreConversationRepository
from formwise_api.storage.interfaces import StorageAdapter


class ConversationPurger:
    def __init__(self, client: Any, conversations: FirestoreConversationRepository, storage: StorageAdapter) -> None:
        self._client = client
        self._conversations = conversations
        self._storage = storage

    def purge(self, conversation: Conversation) -> None:
        """Remove all artifacts associated with an access-revoked conversation."""
        document_ref = self._client.collection("documents").document(conversation.document_id)
        document = document_ref.get().to_dict() or {}
        if document.get("ownerUid") == conversation.user_id:
            stored_filename = document.get("storedFilename")
            if isinstance(stored_filename, str):
                self._storage.delete(stored_filename)
            for key in ("ocrTextStorageKey", "redactedTextStorageKey"):
                path = document.get(key)
                if isinstance(path, str):
                    Path(path).unlink(missing_ok=True)
            document_ref.delete()
            self._client.collection("structured_documents").document(conversation.document_id).delete()
            self._client.collection("privacy_reports").document(conversation.document_id).delete()
            self._client.collection("ocr_jobs").document(conversation.document_id).delete()
        for collection, field in (("messages", "conversationId"), ("fieldAnswers", "conversationId"), ("renderedOutputs", "conversationId"), ("auditEvents", "conversationId")):
            self._conversations.delete_where(collection, field, conversation.id)
        self._conversations.delete_conversation(conversation.id)
