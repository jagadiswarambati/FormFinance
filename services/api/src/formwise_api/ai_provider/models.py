from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIProviderRequest(BaseModel):
    system_instruction: str = Field(alias="systemInstruction")
    structured_context: dict[str, object] = Field(alias="structuredContext")
    history: list[dict[str, str]]
    user_message: str = Field(alias="userMessage")
    response_schema: dict[str, object] = Field(alias="responseSchema")
    locale: Literal["en", "hi", "te"]
    task_type: str = Field(alias="taskType")
    correlation_id: str = Field(alias="correlationId")

    model_config = ConfigDict(populate_by_name=True)


class AIProviderResult(BaseModel):
    content: dict[str, object]
    provider: str
    model: str
    latency_ms: int = Field(alias="latencyMs")
    token_usage: int | None = Field(default=None, alias="tokenUsage")

    model_config = ConfigDict(populate_by_name=True)
