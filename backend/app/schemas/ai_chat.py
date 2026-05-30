"""Схемы для AI-чата."""

from pydantic import BaseModel, Field


class AiAudioPayload(BaseModel):
    """Аудио-данные."""
    content_type: str
    format: str | None = None
    base64: str | None = None
    url: str | None = None
    duration_ms: int | None = None


class AiChatUserInputPart(BaseModel):
    """Часть ввода пользователя (текст или аудио)."""
    type: str = Field(description="text или audio")
    text: str | None = None
    audio: AiAudioPayload | None = None


class AiAudioResponseOptions(BaseModel):
    """Настройки аудио-ответа."""
    voice: str | None = None
    format: str | None = None
    delivery: str = "temporary_url"


class AiFinancialContextOptions(BaseModel):
    """Настройки финансового контекста."""
    include_accounts: bool = True
    include_transactions: bool = True
    include_assets: bool = True
    include_liabilities: bool = True
    include_goals: bool = True
    date_from: str | None = None
    date_to: str | None = None


class AiChatRequest(BaseModel):
    """Запрос к AI-чату."""
    conversation_id: str | None = None
    title: str | None = Field(None, max_length=200)
    input: list[AiChatUserInputPart] = Field(min_length=1)
    response_modalities: list[str] = Field(default=["text"])
    audio_response: AiAudioResponseOptions | None = None
    context: AiFinancialContextOptions | None = None


class AiChatOutput(BaseModel):
    """Вывод AI-чата."""
    text: str | None = None
    audio: AiAudioPayload | None = None
    transcript: str | None = None
    request_text: str | None = None


class AiUsage(BaseModel):
    """Информация об использовании токенов."""
    input_tokens: int | None = None
    output_tokens: int | None = None
    audio_input_seconds: float | None = None
    audio_output_seconds: float | None = None


class AiChatResponse(BaseModel):
    """Ответ AI-чата."""
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    output: AiChatOutput
    tool_results: list[dict] = []
    usage: AiUsage | None = None


class AiChatMessagePart(BaseModel):
    """Часть сообщения AI-чата."""
    type: str
    text: str | None = None
    audio: AiAudioPayload | None = None


class AiChatMessage(BaseModel):
    """Сообщение в диалоге."""
    id: str
    role: str
    content: list[AiChatMessagePart]
    metadata: dict | None = None
    created_at: str


class AiChatConversationCreate(BaseModel):
    """Запрос на создание диалога."""
    title: str | None = Field(None, max_length=200)


class AiChatConversationSummary(BaseModel):
    """Краткая информация о диалоге."""
    id: str
    title: str | None = None
    last_message_preview: str | None = None
    created_at: str
    updated_at: str


class AiChatConversation(BaseModel):
    """Полный диалог с сообщениями."""
    id: str
    user_id: str
    title: str | None = None
    created_at: str
    updated_at: str
    messages: list[AiChatMessage] = []


class AiChatConversationPage(BaseModel):
    """Страница диалогов."""
    items: list[AiChatConversationSummary]
    meta: dict
