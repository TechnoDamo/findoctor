"""
OpenAI-клиент для текстовых и аудио-сообщений.

Реализует интерфейс BaseLlmClient через OpenAI REST API.
Поддерживает:
  - Текстовые чат-завершения (gpt-4o и аналоги).
  - Аудио-ввод через GPT-4o Audio Preview.
  - Аудио-вывод с помощью TTS.
"""


from app.clients.http import get_http_client
from app.clients.llm.base import BaseLlmClient, LlmMessage, LlmResponse
from app.settings import settings


class OpenAiLlmClient(BaseLlmClient):
    """Клиент для OpenAI API."""

    def __init__(self) -> None:
        self._base_url = settings.openai_base_url.rstrip("/")
        self._api_key = settings.openai_api_key
        self._text_model = settings.openai_text_model
        self._audio_model = settings.openai_audio_model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[LlmMessage],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> LlmResponse:
        """Отправка текстового запроса в OpenAI Chat Completions."""
        client = get_http_client()

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self._text_model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        resp = await client.post(
            f"{self._base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        return LlmResponse(
            text=choice["message"].get("content"),
            input_tokens=data.get("usage", {}).get("prompt_tokens"),
            output_tokens=data.get("usage", {}).get("completion_tokens"),
        )

    async def chat_with_audio(
        self,
        messages: list[LlmMessage],
        input_audio_base64: str | None = None,
        input_audio_format: str | None = None,
        output_audio_voice: str | None = None,
        output_audio_format: str | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Отправка запроса с аудио в GPT-4o Audio Preview."""
        client = get_http_client()

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            content_parts = []
            if isinstance(msg.content, str):
                content_parts.append({"type": "text", "text": msg.content})
            elif isinstance(msg.content, list):
                content_parts = msg.content

            if input_audio_base64 and msg.role == "user":
                content_parts.append({
                    "type": "input_audio",
                    "input_audio": {
                        "data": input_audio_base64,
                        "format": input_audio_format or "wav",
                    },
                })

            payload_messages.append({"role": msg.role, "content": content_parts})

        payload = {
            "model": self._audio_model,
            "messages": payload_messages,
            "modalities": ["text", "audio"],
            "audio": {
                "voice": output_audio_voice or "alloy",
                "format": output_audio_format or "wav",
            },
        }

        resp = await client.post(
            f"{self._base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        audio_base64_out = None
        audio_format_out = None
        text_out = None

        if isinstance(choice["message"].get("audio"), dict):
            audio_data = choice["message"]["audio"]
            audio_base64_out = audio_data.get("data")
            audio_format_out = audio_data.get("format")
        if choice["message"].get("content"):
            text_out = choice["message"]["content"]

        return LlmResponse(
            text=text_out,
            audio_base64=audio_base64_out,
            audio_format=audio_format_out,
            input_tokens=data.get("usage", {}).get("prompt_tokens"),
            output_tokens=data.get("usage", {}).get("completion_tokens"),
        )
