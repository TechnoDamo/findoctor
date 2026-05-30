"""Схемы для AI-чата."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


def to_camel(value: str) -> str:
    """Convert snake_case field names to lower camelCase for the public API."""
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class AiBaseModel(BaseModel):
    """Base schema for AI chat API models."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AiAudioPayload(AiBaseModel):
    """Аудио-данные."""
    content_type: str
    format: str | None = None
    base64: str | None = None
    url: str | None = None
    duration_ms: int | None = None


class AiChatUserInputPart(AiBaseModel):
    """Часть ввода пользователя (текст или аудио)."""
    type: str = Field(description="text или audio")
    text: str | None = None
    audio: AiAudioPayload | None = None


class AiAudioResponseOptions(AiBaseModel):
    """Настройки аудио-ответа."""
    voice: str | None = None
    format: str | None = None
    delivery: str = "temporary_url"


class AiFinancialContextOptions(AiBaseModel):
    """Настройки финансового контекста."""
    include_accounts: bool = True
    include_transactions: bool = True
    include_assets: bool = True
    include_liabilities: bool = True
    include_goals: bool = True
    transaction_history_months: int = 3
    base_currency: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class AiChatRequest(AiBaseModel):
    """Запрос к AI-чату."""
    conversation_id: str | None = None
    title: str | None = Field(None, max_length=200)
    input: list[AiChatUserInputPart] = Field(min_length=1)
    response_modalities: list[str] = Field(default=["text"])
    audio_response: AiAudioResponseOptions | None = None
    context: AiFinancialContextOptions | None = None


class AiChatOutput(AiBaseModel):
    """Вывод AI-чата."""
    text: str | None = None
    audio: AiAudioPayload | None = None
    transcript: str | None = None
    request_text: str | None = None


class AiUsage(AiBaseModel):
    """Информация об использовании токенов."""
    input_tokens: int | None = None
    output_tokens: int | None = None
    audio_input_seconds: float | None = None
    audio_output_seconds: float | None = None


class AiChatResponse(AiBaseModel):
    """Ответ AI-чата."""
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    request_text: str | None = None
    output: AiChatOutput
    tool_results: list[dict] = []
    usage: AiUsage | None = None


class AiChatMessagePart(AiBaseModel):
    """Часть сообщения AI-чата."""
    type: str
    text: str | None = None
    audio: AiAudioPayload | None = None


class AiChatMessage(AiBaseModel):
    """Сообщение в диалоге."""
    id: UUID
    role: str
    content: list[AiChatMessagePart]
    metadata: dict | None = None
    created_at: datetime


class AiChatConversationCreate(AiBaseModel):
    """Запрос на создание диалога."""
    title: str | None = Field(None, max_length=200)


class AiChatConversationSummary(AiBaseModel):
    """Краткая информация о диалоге."""
    id: UUID
    title: str | None = None
    last_message_preview: str | None = None
    created_at: datetime
    updated_at: datetime


class AiChatConversation(AiBaseModel):
    """Полный диалог с сообщениями."""
    id: UUID
    user_id: UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[AiChatMessage] = []


class AiChatConversationPage(AiBaseModel):
    """Страница диалогов."""
    items: list[AiChatConversationSummary]
    meta: dict
