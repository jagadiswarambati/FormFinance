from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConversationStatus = Literal["ready", "in_progress", "ready_to_render", "revoked"]
MessageRole = Literal["user", "assistant", "system", "tool"]


class CreateConversationRequest(BaseModel):
    document_id: str = Field(alias="documentId")
    locale: Literal["en", "hi", "te"] = "en"

    model_config = ConfigDict(populate_by_name=True)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ConversationMessage(BaseModel):
    id: str
    conversation_id: str = Field(alias="conversationId")
    role: MessageRole
    safe_content: str = Field(alias="safeContent")
    field_ids: list[str] = Field(default_factory=list, alias="fieldIds")
    provider: str | None = None
    token_usage: int | None = Field(default=None, alias="tokenUsage")
    latency_ms: int | None = Field(default=None, alias="latencyMs")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class Conversation(BaseModel):
    id: str
    user_id: str = Field(alias="userId")
    document_id: str = Field(alias="documentId")
    status: ConversationStatus
    locale: Literal["en", "hi", "te"]
    provider: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    revoked_at: datetime | None = Field(default=None, alias="revokedAt")

    model_config = ConfigDict(populate_by_name=True)


class ConversationDetail(Conversation):
    messages: list[ConversationMessage]


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str = Field(alias="conversationId")

    model_config = ConfigDict(populate_by_name=True)
