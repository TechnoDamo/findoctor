import base64
import json
import os
import re
import time
import uuid
import wave
from pathlib import Path
from typing import Any

import httpx
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

MODEL_CONFIG_PATH = ROOT / os.getenv("MODEL_CONFIG_PATH", "config.models.yaml")
LLM_CONTEXT_PATH = ROOT / os.getenv("LLM_CONTEXT_PATH", "contexts/llm_system.txt")
STT_CONTEXT_PATH = ROOT / os.getenv("STT_CONTEXT_PATH", "contexts/stt_system.txt")
TTS_CONTEXT_PATH = ROOT / os.getenv("TTS_CONTEXT_PATH", "contexts/tts_system.txt")
AUDIO_DIR = ROOT / "storage" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL", "https://routerai.ru/api/v1").rstrip("/")
API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "")

app = FastAPI(title="OpenAI-Compatible Voice Chat")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class TextInputPart(BaseModel):
    type: str
    text: str | None = None
    audio: dict[str, Any] | None = None


class AiChatRequest(BaseModel):
    conversationId: str | None = None
    title: str | None = None
    input: list[TextInputPart]
    responseModalities: list[str] = ["text"]
    audioResponse: dict[str, Any] | None = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_models() -> dict[str, Any]:
    return yaml.safe_load(MODEL_CONFIG_PATH.read_text(encoding="utf-8"))


def defaults() -> dict[str, Any]:
    return load_models().get("defaults", {})


def auth_headers() -> dict[str, str]:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_COMPAT_API_KEY is not set")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def wav_from_pcm16(pcm: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    out = bytearray()
    out.extend(b"RIFF")
    out.extend((36 + len(pcm)).to_bytes(4, "little"))
    out.extend(b"WAVEfmt ")
    out.extend((16).to_bytes(4, "little"))
    out.extend((1).to_bytes(2, "little"))
    out.extend((channels).to_bytes(2, "little"))
    out.extend((sample_rate).to_bytes(4, "little"))
    out.extend((sample_rate * channels * 2).to_bytes(4, "little"))
    out.extend((channels * 2).to_bytes(2, "little"))
    out.extend((16).to_bytes(2, "little"))
    out.extend(b"data")
    out.extend(len(pcm).to_bytes(4, "little"))
    out.extend(pcm)
    return bytes(out)


def audio_seconds(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as wav:
            return wav.getnframes() / float(wav.getframerate())
    except Exception:
        return None


def user_text_from_parts(parts: list[TextInputPart]) -> str:
    return "\n".join(part.text or "" for part in parts if part.type == "text").strip()


async def chat_completion(payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(f"{BASE_URL}/chat/completions", headers=auth_headers(), json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def stream_chat_completion(payload: dict[str, Any]):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{BASE_URL}/chat/completions", headers=auth_headers(), json=payload) as response:
            if response.status_code >= 400:
                detail = await response.aread()
                raise HTTPException(status_code=response.status_code, detail=detail.decode("utf-8", errors="replace"))
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line.removeprefix("data: ")
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                    delta = event.get("choices", [{}])[0].get("delta", {})
                    text = delta.get("content")
                    if text:
                        yield text
                except json.JSONDecodeError:
                    continue


async def transcribe_audio(audio_b64: str, audio_format: str) -> str:
    config = defaults()
    payload = {
        "model": config.get("stt"),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": read_text(STT_CONTEXT_PATH)},
                    {"type": "input_audio", "input_audio": {"data": audio_b64, "format": audio_format}},
                ],
            }
        ],
    }
    response = await chat_completion(payload)
    return response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


async def complete_llm(text: str, stream: bool = False):
    payload = {
        "model": defaults().get("llm"),
        "messages": [
            {"role": "system", "content": read_text(LLM_CONTEXT_PATH)},
            {"role": "user", "content": text},
        ],
        "stream": stream,
    }
    if stream:
        return stream_chat_completion(payload)
    response = await chat_completion(payload)
    return response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


async def synthesize_tts(text: str, voice: str | None = None) -> dict[str, Any]:
    config = defaults()
    payload = {
        "model": config.get("tts"),
        "modalities": ["text", "audio"],
        "messages": [
            {"role": "system", "content": read_text(TTS_CONTEXT_PATH)},
            {"role": "user", "content": f"Voice over this exact text:\n\n{text}"},
        ],
        "audio": {"voice": voice or config.get("voice", "echo"), "format": "pcm16"},
        "stream": True,
    }
    pcm_chunks: list[bytes] = []
    echoed_text: list[str] = []
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{BASE_URL}/chat/completions", headers=auth_headers(), json=payload) as response:
            if response.status_code >= 400:
                detail = await response.aread()
                raise HTTPException(status_code=response.status_code, detail=detail.decode("utf-8", errors="replace"))
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line.removeprefix("data: ")
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = event.get("choices", [{}])[0].get("delta", {})
                audio_data = delta.get("audio", {}).get("data")
                if audio_data:
                    pcm_chunks.append(base64.b64decode(audio_data))
                if isinstance(delta.get("content"), str):
                    echoed_text.append(delta["content"])
    wav = wav_from_pcm16(b"".join(pcm_chunks))
    name = f"{int(time.time())}_{uuid.uuid4().hex}.wav"
    path = AUDIO_DIR / name
    path.write_bytes(wav)
    return {
        "url": f"/audio/{name}",
        "format": "wav",
        "bytes": len(wav),
        "seconds": audio_seconds(path),
        "text": "".join(echoed_text),
    }


def response_ids(conversation_id: str | None = None) -> tuple[str, str, str]:
    return (
        conversation_id or str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/config")
async def config():
    data = load_models()
    data["contexts"] = {
        "llm": read_text(LLM_CONTEXT_PATH),
        "stt": read_text(STT_CONTEXT_PATH),
        "tts": read_text(TTS_CONTEXT_PATH),
    }
    data["hasApiKey"] = bool(API_KEY)
    return data


@app.get("/audio/{name}")
async def audio(name: str):
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "", name)
    path = AUDIO_DIR / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/wav")


@app.post("/ai/chat/messages")
async def create_ai_chat_message(request: AiChatRequest):
    text = user_text_from_parts(request.input)
    audio_part = next((part for part in request.input if part.type == "audio" and part.audio), None)
    transcript = None

    if audio_part and audio_part.audio:
        transcript = await transcribe_audio(audio_part.audio["data"], audio_part.audio.get("format", "wav"))
        text = "\n".join(item for item in [text, transcript] if item).strip()

    if "audio" not in request.responseModalities:
        async def stream():
            async for chunk in await complete_llm(text, stream=True):
                yield chunk

        return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")

    assistant_text = await complete_llm(text, stream=False)
    audio_payload = await synthesize_tts(assistant_text, (request.audioResponse or {}).get("voice"))
    conversation_id, user_message_id, assistant_message_id = response_ids(request.conversationId)
    return {
        "conversationId": conversation_id,
        "userMessageId": user_message_id,
        "assistantMessageId": assistant_message_id,
        "output": {
            "text": assistant_text,
            "audio": audio_payload,
            "transcript": transcript,
        },
        "usage": {},
    }


@app.post("/ai/chat/audio")
async def create_ai_voice_chat_message(
    audio: UploadFile = File(...),
    conversationId: str | None = Form(None),
    prompt: str | None = Form(None),
    audioFormat: str = Form("wav"),
    audioResponseVoice: str | None = Form(None),
):
    audio_b64 = base64.b64encode(await audio.read()).decode("ascii")
    transcript = await transcribe_audio(audio_b64, audioFormat)
    user_text = "\n".join(item for item in [prompt, transcript] if item).strip()
    assistant_text = await complete_llm(user_text, stream=False)
    audio_payload = await synthesize_tts(assistant_text, audioResponseVoice)
    conversation_id, user_message_id, assistant_message_id = response_ids(conversationId)
    return JSONResponse(
        {
            "conversationId": conversation_id,
            "userMessageId": user_message_id,
            "assistantMessageId": assistant_message_id,
            "output": {
                "text": assistant_text,
                "audio": audio_payload,
                "transcript": transcript,
            },
            "usage": {},
        }
    )

