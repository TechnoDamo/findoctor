"""Сервис AI-чата: управление диалогами и реальные OpenAI-compatible вызовы."""

import base64
import json
from pathlib import Path

import httpx
from psycopg import AsyncConnection

from app.clients.http import get_http_client
from app.core.errors import NotFoundError
from app.repositories import ai_chat as chat_repo
from app.settings import settings

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def _read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def _provider_config(kind: str) -> tuple[str, str, str]:
    base_url = getattr(settings, f"{kind}_base_url") or settings.openai_base_url
    api_key = getattr(settings, f"{kind}_api_key") or settings.openai_api_key
    model = getattr(settings, f"{kind}_model") or (
        settings.openai_audio_model if kind in {"stt", "tts"} else settings.openai_text_model
    )
    return base_url.rstrip("/"), api_key, model


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


async def _chat_completion(kind: str, payload: dict) -> dict:
    base_url, api_key, _model = _provider_config(kind)
    client = get_http_client()
    response = await client.post(
        f"{base_url}/chat/completions",
        headers=_headers(api_key),
        json=payload,
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    response.raise_for_status()
    return response.json()


async def _chat_completion_sse(kind: str, payload: dict) -> str:
    base_url, api_key, _model = _provider_config(kind)
    client = get_http_client()
    response = await client.post(
        f"{base_url}/chat/completions",
        headers=_headers(api_key),
        json=payload,
        timeout=None,
    )
    response.raise_for_status()
    return response.text


def _message_text(response: dict) -> str:
    content = response.get("choices", [{}])[0].get("message", {}).get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
    return ""


async def _run_llm(user_text: str, financial_context: dict | None = None, prompt_name: str = "llm_text") -> tuple[str, dict]:
    _base_url, _api_key, model = _provider_config("llm")
    system_prompt = _build_system_prompt(financial_context, prompt_name)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }
    response = await _chat_completion("llm", payload)
    return _message_text(response), response.get("usage") or {}


async def _run_stt(audio_data: str, audio_format: str, prompt: str | None = None) -> tuple[str, dict]:
    _base_url, _api_key, model = _provider_config("stt")
    stt_prompt = _read_prompt("stt_system.txt")
    if prompt:
        stt_prompt = f"{stt_prompt}\n\nAdditional user instruction: {prompt}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": stt_prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_data,
                            "format": audio_format,
                        },
                    },
                ],
            }
        ],
    }
    response = await _chat_completion("stt", payload)
    return _message_text(response), response.get("usage") or {}


def _wav_from_pcm16(pcm: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    header = bytearray()
    header.extend(b"RIFF")
    header.extend((36 + len(pcm)).to_bytes(4, "little"))
    header.extend(b"WAVEfmt ")
    header.extend((16).to_bytes(4, "little"))
    header.extend((1).to_bytes(2, "little"))
    header.extend((channels).to_bytes(2, "little"))
    header.extend((sample_rate).to_bytes(4, "little"))
    header.extend((sample_rate * channels * 2).to_bytes(4, "little"))
    header.extend((channels * 2).to_bytes(2, "little"))
    header.extend((16).to_bytes(2, "little"))
    header.extend(b"data")
    header.extend(len(pcm).to_bytes(4, "little"))
    return bytes(header) + pcm


async def _run_tts(text: str, voice: str | None = None, response_format: str | None = None) -> dict | None:
    _base_url, _api_key, model = _provider_config("tts")
    audio_format = response_format or "pcm16"
    payload = {
        "model": model,
        "modalities": ["text", "audio"],
        "messages": [
            {"role": "system", "content": _read_prompt("tts_system.txt")},
            {"role": "user", "content": f"Voice over this exact text:\n\n{text}"},
        ],
        "audio": {
            "voice": voice or settings.tts_voice,
            "format": audio_format,
        },
        "stream": True,
    }
    sse = await _chat_completion_sse("tts", payload)
    chunks: list[bytes] = []
    for line in sse.splitlines():
        if not line.startswith("data: "):
            continue
        data = line.removeprefix("data: ")
        if data == "[DONE]":
            break
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        audio_data = event.get("choices", [{}])[0].get("delta", {}).get("audio", {}).get("data")
        if audio_data:
            chunks.append(base64.b64decode(audio_data))
    if not chunks:
        return None
    audio_bytes = b"".join(chunks)
    content_type = "audio/wav"
    if audio_format == "pcm16":
        audio_bytes = _wav_from_pcm16(audio_bytes)
        returned_format = "wav"
    else:
        returned_format = audio_format
    return {
        "content_type": content_type,
        "format": returned_format,
        "base64": base64.b64encode(audio_bytes).decode("ascii"),
        "url": None,
        "duration_ms": None,
    }


def _text_from_input_parts(input_parts: list[dict]) -> str:
    return "\n".join(part.get("text") or "" for part in input_parts if part.get("type") == "text").strip()


async def create_conversation(
    conn: AsyncConnection, user_id: str, title: str | None = None
) -> dict:
    """Создание нового диалога."""
    return await chat_repo.insert_conversation(conn, user_id, title)


async def get_conversation(
    conn: AsyncConnection, user_id: str, conversation_id: str
) -> dict:
    """Получение диалога с сообщениями."""
    conversation = await chat_repo.find_conversation(conn, conversation_id)
    if conversation is None or conversation["user_id"] != user_id:
        raise NotFoundError("Диалог не найден")
    return conversation


async def delete_conversation(
    conn: AsyncConnection, user_id: str, conversation_id: str
) -> None:
    """Удаление диалога."""
    conversation = await chat_repo.find_conversation(conn, conversation_id)
    if conversation is None or conversation["user_id"] != user_id:
        raise NotFoundError("Диалог не найден")
    await chat_repo.delete_conversation(conn, conversation_id)


async def send_message(
    conn: AsyncConnection,
    user_id: str,
    conversation_id: str | None,
    input_parts: list[dict],
    title: str | None = None,
    response_modalities: list[str] | None = None,
    audio_response: dict | None = None,
    financial_context: dict | None = None,
) -> dict:
    """
    Отправка сообщения AI-ассистенту и сохранение ответа.

    Если conversation_id не указан — создаётся новый диалог.
    """
    if conversation_id is None:
        conversation = await chat_repo.insert_conversation(conn, user_id, title)
        conversation_id = conversation["id"]
    else:
        conversation = await chat_repo.find_conversation(conn, conversation_id)
        if conversation is None or conversation["user_id"] != user_id:
            raise NotFoundError("Диалог не найден")

    # Сохраняем сообщение пользователя
    user_msg = await chat_repo.insert_message(
        conn, conversation_id, "user", input_parts
    )

    user_text = _text_from_input_parts(input_parts)
    transcript = None
    audio_part = next((part for part in input_parts if part.get("type") == "audio" and part.get("audio")), None)
    if audio_part:
        audio = audio_part["audio"]
        audio_data = audio.get("base64") or audio.get("data")
        audio_format = audio.get("format") or audio.get("content_type") or "wav"
        transcript, _stt_usage = await _run_stt(audio_data, audio_format, audio_part.get("text"))
        user_text = "\n".join(part for part in [user_text, transcript] if part).strip()

    assistant_text, llm_usage = await _run_llm(user_text, financial_context)
    audio_payload = None
    if "audio" in (response_modalities or []):
        audio_payload = await _run_tts(
            _truncate_for_tts(assistant_text),
            voice=(audio_response or {}).get("voice"),
            response_format=(audio_response or {}).get("format"),
        )

    # Сохраняем ответ ассистента
    assistant_parts = [{"type": "text", "text": assistant_text, "audio": audio_payload}]
    assistant_msg = await chat_repo.insert_message(
        conn, conversation_id, "assistant", assistant_parts
    )

    return {
        "conversation_id": conversation_id,
        "user_message_id": user_msg["id"],
        "assistant_message_id": assistant_msg["id"],
        "request_text": transcript or user_text,
        "output": {
            "text": assistant_text,
            "audio": audio_payload,
            "transcript": transcript,
            "request_text": transcript or user_text,
        },
        "tool_results": [],
        "usage": {
            "input_tokens": llm_usage.get("prompt_tokens"),
            "output_tokens": llm_usage.get("completion_tokens"),
            "audio_input_seconds": None,
            "audio_output_seconds": None,
        },
    }


async def send_voice_message(
    conn: AsyncConnection,
    user_id: str,
    audio_data: str,
    audio_format: str,
    conversation_id: str | None = None,
    title: str | None = None,
    prompt: str | None = None,
    response_modalities: list[str] | None = None,
    voice: str | None = None,
    response_format: str | None = None,
    delivery: str = "temporary_url",
) -> dict:
    """
    Отправка голосового сообщения AI-ассистенту.

    Параметры:
        audio_data: base64-кодированные аудиоданные.
        audio_format: формат аудио (wav, mp3, opus, webm, m4a, flac, pcm16).
        conversation_id: существующий диалог (опционально).
        title: заголовок нового диалога (если conversation_id не указан).
        prompt: текстовый промпт к аудио.
        response_modalities: список ["text", "audio"].
        voice: голос для озвучки ответа (alloy, sage, ash, coral, echo).
        response_format: формат аудио-ответа.
        delivery: способ доставки аудио (inline_base64 / temporary_url).
    """
    if conversation_id is None:
        conversation = await chat_repo.insert_conversation(conn, user_id, title)
        conversation_id = conversation["id"]
    else:
        conversation = await chat_repo.find_conversation(conn, conversation_id)
        if conversation is None or conversation["user_id"] != user_id:
            raise NotFoundError("Диалог не найден")

    input_parts = [{"type": "audio", "text": prompt, "audio": {"contentType": audio_format, "base64": audio_data}}]

    user_msg = await chat_repo.insert_message(conn, conversation_id, "user", input_parts)

    transcript, _stt_usage = await _run_stt(audio_data, audio_format, prompt)
    assistant_text, llm_usage = await _run_llm(transcript, prompt_name="llm_voice")
    audio_payload = None
    if "audio" in (response_modalities or ["audio", "text"]):
        audio_payload = await _run_tts(_truncate_for_tts(assistant_text), voice=voice, response_format=response_format)
    assistant_parts = [{"type": "text", "text": assistant_text, "audio": audio_payload}]
    assistant_msg = await chat_repo.insert_message(
        conn, conversation_id, "assistant", assistant_parts
    )

    return {
        "conversation_id": conversation_id,
        "user_message_id": user_msg["id"],
        "assistant_message_id": assistant_msg["id"],
        "request_text": transcript,
        "output": {
            "text": assistant_text,
            "audio": audio_payload,
            "transcript": transcript,
            "request_text": transcript,
        },
        "tool_results": [],
        "usage": {
            "input_tokens": llm_usage.get("prompt_tokens"),
            "output_tokens": llm_usage.get("completion_tokens"),
            "audio_input_seconds": None,
            "audio_output_seconds": None,
        },
    }


async def list_conversations_export(
    conn: AsyncConnection, user_id: str, page: int = 1, page_size: int = 50
) -> tuple[list[dict], int]:
    """Экспорт списка диалогов для API."""
    return await chat_repo.list_conversations(conn, user_id, page, page_size)


def _truncate_for_tts(text: str) -> str:
    max_chars = settings.tts_max_chars
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(".", 1)[0].rstrip() + "."


def _build_system_prompt(context: dict | None, prompt_name: str = "llm_text") -> str:
    """Строит системный промпт с финансовым контекстом пользователя."""
    if context is None:
        return _read_prompt(f"{prompt_name}.txt")
    return (
        f"{_read_prompt(f'{prompt_name}.txt')}\n\n"
        "Financial context flags requested by the client:\n"
        f"{context}"
    )
