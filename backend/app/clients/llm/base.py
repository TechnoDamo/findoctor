"""
Абстрактный интерфейс LLM-клиента.

Все реализации (OpenAI, Anthropic, локальные модели) должны наследовать BaseLlmClient.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LlmMessage:
    """Сообщение для LLM."""
    role: str
    content: str | list[dict]


@dataclass
class LlmResponse:
    """Ответ от LLM."""
    text: str | None = None
    audio_base64: str | None = None
    audio_format: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    tool_calls: list[dict] = field(default_factory=list)


class BaseLlmClient(ABC):
    """Абстрактный клиент для языковых моделей."""

    @abstractmethod
    async def chat(
        self,
        messages: list[LlmMessage],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> LlmResponse:
        """Отправляет сообщения модели и возвращает текстовый ответ."""
        ...

    @abstractmethod
    async def chat_with_audio(
        self,
        messages: list[LlmMessage],
        input_audio_base64: str | None = None,
        input_audio_format: str | None = None,
        output_audio_voice: str | None = None,
        output_audio_format: str | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Отправляет сообщения модели с возможностью аудио-ввода/вывода."""
        ...
