"""OpenAI-compatible proxy for whisper.cpp server.

Translates Chat Completions API (JSON with base64 input_audio) to whisper.cpp's
multipart/form-data /inference endpoint, and converts responses back to Chat
Completions format that the FinDoctor backend expects.

The proxy manages the whisper.cpp server lifecycle internally.
"""

from __future__ import annotations

import base64
import os
import subprocess
import shutil
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Configuration (all from environment, with defaults)
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent

WHISPER_HOST = os.getenv("WHISPER_HOST", "127.0.0.1")
WHISPER_PORT = int(os.getenv("WHISPER_PORT", "8080"))
WHISPER_CPP_PORT = int(os.getenv("WHISPER_CPP_PORT", "8082"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_MODELS_DIR = os.getenv("WHISPER_MODELS_DIR", str(HERE / "whisper.cpp" / "models"))
WHISPER_THREADS = os.getenv("WHISPER_THREADS", "4")
WHISPER_PROCESSORS = os.getenv("WHISPER_PROCESSORS", "1")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "auto")
WHISPER_BEST_OF = os.getenv("WHISPER_BEST_OF", "5")
WHISPER_BEAM_SIZE = os.getenv("WHISPER_BEAM_SIZE", "-1")
WHISPER_NO_SPEECH_THOLD = os.getenv("WHISPER_NO_SPEECH_THOLD", "0.6")
WHISPER_NO_TIMESTAMPS = os.getenv("WHISPER_NO_TIMESTAMPS", "false")
WHISPER_DEBUG_MODE = os.getenv("WHISPER_DEBUG_MODE", "false")
WHISPER_NO_GPU = os.getenv("WHISPER_NO_GPU", "false")
WHISPER_FLASH_ATTN = os.getenv("WHISPER_FLASH_ATTN", "true")

WHISPER_SERVER_BIN = str(HERE / "whisper.cpp" / "build" / "bin" / "whisper-server")
MODEL_PATH = os.path.join(WHISPER_MODELS_DIR, f"ggml-{WHISPER_MODEL}.bin")
WHISPER_CPP_INTERNAL = f"http://127.0.0.1:{WHISPER_CPP_PORT}"

server_process: subprocess.Popen | None = None


# ---------------------------------------------------------------------------
# whisper.cpp process management
# ---------------------------------------------------------------------------

def _start_whisper_cpp() -> None:
    global server_process

    if not os.path.isfile(WHISPER_SERVER_BIN):
        print(f"ERROR: whisper-server binary not found at {WHISPER_SERVER_BIN}", file=sys.stderr)
        print("Run 'make build' first.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(MODEL_PATH):
        print(f"ERROR: model not found at {MODEL_PATH}", file=sys.stderr)
        print("Run 'make model' first.", file=sys.stderr)
        sys.exit(1)

    args = [
        WHISPER_SERVER_BIN,
        "--model", MODEL_PATH,
        "--host", "127.0.0.1",
        "--port", str(WHISPER_CPP_PORT),
        "--threads", WHISPER_THREADS,
        "--processors", WHISPER_PROCESSORS,
        "--language", WHISPER_LANGUAGE,
        "--best-of", WHISPER_BEST_OF,
        "--beam-size", WHISPER_BEAM_SIZE,
        "--no-speech-thold", WHISPER_NO_SPEECH_THOLD,
    ]

    if WHISPER_NO_TIMESTAMPS.lower() == "true":
        args.append("--no-timestamps")
    if WHISPER_DEBUG_MODE.lower() == "true":
        args.append("--debug-mode")
    if WHISPER_NO_GPU.lower() == "true":
        args.append("--no-gpu")
    if WHISPER_FLASH_ATTN.lower() != "true":
        args.append("--no-flash-attn")

    print(f"[proxy] Starting whisper.cpp on port {WHISPER_CPP_PORT}...")
    server_process = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(60):
        try:
            import urllib.request
            urllib.request.urlopen(f"{WHISPER_CPP_INTERNAL}/", timeout=1)
            print(f"[proxy] whisper.cpp ready on port {WHISPER_CPP_PORT}")
            return
        except Exception:
            time.sleep(1)
    print("ERROR: whisper.cpp server failed to start within 60s", file=sys.stderr)
    _stop_whisper_cpp()
    sys.exit(1)


def _stop_whisper_cpp() -> None:
    global server_process
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        server_process = None


# ---------------------------------------------------------------------------
# Audio conversion helpers
# ---------------------------------------------------------------------------

_ffmpeg_available: bool | None = None


def _has_ffmpeg() -> bool:
    global _ffmpeg_available
    if _ffmpeg_available is None:
        _ffmpeg_available = shutil.which("ffmpeg") is not None
    return _ffmpeg_available


_WAVEFORMATS = frozenset({"wav", "wave"})


def _decode_audio(audio_base64: str, audio_format: str) -> tuple[str, bool]:
    audio_bytes = base64.b64decode(audio_base64)

    fmt = audio_format.lower()
    if fmt in _WAVEFORMATS:
        fmt = "wav"

    suffix = f".{fmt}"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(audio_bytes)

    if fmt == "wav":
        return tmp_path, False

    if _has_ffmpeg():
        out_path = tmp_path + ".wav"
        rc = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", tmp_path, "-ar", "16000", "-ac", "1", out_path],
            capture_output=True,
        )
        os.unlink(tmp_path)
        if rc.returncode == 0:
            return out_path, True
        else:
            try:
                os.unlink(out_path)
            except OSError:
                pass
            return tmp_path, False

    return tmp_path, False


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    _start_whisper_cpp()
    yield
    print("[proxy] Shutting down...")
    _stop_whisper_cpp()


app = FastAPI(title="whisper-server-proxy", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "model": WHISPER_MODEL, "proxy": True}


@app.post("/chat/completions")
@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> dict[str, Any]:
    body = await request.json()
    model_name = body.get("model", WHISPER_MODEL)

    prompt = ""
    audio_b64: str | None = None
    audio_format = "wav"

    for msg in body.get("messages", []):
        content = msg.get("content", [])
        if isinstance(content, str):
            prompt = content
        elif isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    prompt = part.get("text", "")
                elif part.get("type") == "input_audio":
                    audio = part.get("input_audio", {})
                    audio_b64 = audio.get("data", "")
                    audio_format = audio.get("format", "wav")

    if not audio_b64:
        return JSONResponse(
            {"error": {"message": "No audio data in request", "type": "invalid_request_error"}},
            status_code=400,
        )

    try:
        audio_path, _converted = _decode_audio(audio_b64, audio_format)
    except Exception:
        return JSONResponse(
            {"error": {"message": "Invalid base64 audio data", "type": "invalid_request_error"}},
            status_code=400,
        )

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
            data: dict[str, Any] = {"response_format": "json"}
            if prompt:
                data["prompt"] = prompt

            with open(audio_path, "rb") as f:
                ext = os.path.splitext(audio_path)[1].lstrip(".")
                files = {"file": (f"audio.{ext}", f, f"audio/{ext}")}
                resp = await client.post(
                    f"{WHISPER_CPP_INTERNAL}/inference",
                    data=data,
                    files=files,
                )

            if resp.status_code != 200:
                return JSONResponse(
                    {
                        "error": {
                            "message": f"Transcription failed: {resp.text[:300]}",
                            "type": "server_error",
                        }
                    },
                    status_code=502,
                )

            result = resp.json()
    finally:
        try:
            os.unlink(audio_path)
        except OSError:
            pass

    text = result.get("text", "").strip()

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": len(text.split()),
            "total_tokens": len(text.split()),
        },
    }


# ---------------------------------------------------------------------------
# Direct proxy pass-through endpoints (optional, for debugging)
# ---------------------------------------------------------------------------

@app.post("/inference")
async def inference_proxy(request: Request):
    """Proxy multipart /inference directly to whisper.cpp (raw mode)."""
    body = await request.body()
    headers = {"content-type": request.headers.get("content-type", "")}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{WHISPER_CPP_INTERNAL}/inference",
            content=body,
            headers=headers,
        )
    return JSONResponse(resp.json(), status_code=resp.status_code)


@app.post("/load")
async def load_proxy(request: Request):
    """Proxy /load directly to whisper.cpp."""
    body = await request.body()
    headers = {"content-type": request.headers.get("content-type", "")}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{WHISPER_CPP_INTERNAL}/load",
            content=body,
            headers=headers,
        )
    return JSONResponse(resp.json(), status_code=resp.status_code)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=WHISPER_HOST,
        port=WHISPER_PORT,
        log_level="info",
    )
