import base64
import io
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

try:
    from silero import silero_tts, silero_stt
except Exception:  # pragma: no cover - import error is reported by endpoint.
    silero_tts = None
    silero_stt = None


app = FastAPI(title="Local Silero Audio API")
torch.set_num_threads(4)


class TtsRequest(BaseModel):
    model: str = "ru/v5_5_ru"
    speaker: str = "xenia"
    text: str
    sample_rate: int = 48000
    ssml: bool = False


class SttRequest(BaseModel):
    model: str = "en/latest/jit_q"
    language: str = "en"
    version: str = "latest"
    format: str = "jit_q"
    audio: str
    audio_format: str = "wav"


def parse_tts_model(model_id: str) -> tuple[str, str]:
    if "/" in model_id:
      language, model = model_id.split("/", 1)
      return language, model
    return "ru", model_id


@lru_cache(maxsize=8)
def load_tts(language: str, model_id: str):
    if silero_tts is None:
        raise RuntimeError("silero package is not installed or failed to import")
    model, _example_text = silero_tts(language=language, speaker=model_id)
    model.to(torch.device("cpu"))
    return model


@lru_cache(maxsize=8)
def load_stt(language: str, version: str, model_format: str):
    if silero_stt is None:
        raise RuntimeError("silero_stt is not available in the installed silero package")
    device = torch.device("cpu")
    model, decoder, utils = silero_stt(
        language=language,
        version=version,
        jit_model=model_format,
        device=device,
    )
    return model, decoder, utils, device


def wav_response(audio, sample_rate: int) -> Response:
    if isinstance(audio, torch.Tensor):
        audio = audio.detach().cpu().numpy()
    audio = np.asarray(audio, dtype=np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV")
    return Response(content=buffer.getvalue(), media_type="audio/wav")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/tts")
def tts(request: TtsRequest):
    try:
        language, model_id = parse_tts_model(request.model)
        model = load_tts(language, model_id)
        kwargs = {
            "speaker": request.speaker,
            "sample_rate": request.sample_rate,
        }
        if request.ssml:
            audio = model.apply_tts(ssml_text=request.text, **kwargs)
        else:
            audio = model.apply_tts(text=request.text, **kwargs)
        return wav_response(audio, request.sample_rate)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/stt")
def stt(request: SttRequest):
    try:
        model, decoder, utils, device = load_stt(request.language, request.version, request.format)
        read_batch, split_into_batches, _read_audio, prepare_model_input = utils
        suffix = "." + request.audio_format.lstrip(".")
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(base64.b64decode(request.audio))
            tmp_path = Path(tmp.name)
        try:
            batches = split_into_batches([str(tmp_path)], batch_size=1)
            prepared = prepare_model_input(read_batch(batches[0]), device=device)
            output = model(prepared)
            transcript = " ".join(decoder(example.cpu()) for example in output)
            return {"transcript": transcript}
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

