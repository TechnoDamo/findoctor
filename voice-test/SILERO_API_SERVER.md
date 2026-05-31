# Local Silero API Server

This project can call a local Silero server when the UI provider is set to `Silero API`.

Default URL:

```text
http://localhost:8790
```

Override it for the Node UI server with:

```bash
export SILERO_BASE_URL="http://localhost:8790"
```

## Recommended Models

TTS:

- `ru/v5_5_ru` - best public Russian Silero voiceover default, but `CC-BY-NC`.
- `ru/v5_cis_base_nostress` - best license-conscious public option, `MIT`.
- `ru/v5_cis_base` - also `MIT`, but expects stress marks more often.

STT:

- `en/latest/jit_q` - best CPU default for English.
- `en/latest/jit` - better quality, larger/slower.
- `de/v4/jit_large` - best public German option.
- `es/latest/jit` - public Spanish option.
- `ua/latest/jit_q` - best CPU default for Ukrainian.

There is no strong current public Silero Russian STT choice in the official model registry, so Russian STT should stay on RouterAI/OpenAI-compatible models for now.

## Install

Create a separate Python environment:

```bash
cd /Users/damir/Documents/ПрофИИт/voice-test
python3 -m venv .venv-silero
source .venv-silero/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn soundfile numpy torch torchaudio silero
```

## Start

```bash
cd /Users/damir/Documents/ПрофИИт/voice-test
source .venv-silero/bin/activate
uvicorn silero_api_server:app --host 127.0.0.1 --port 8790
```

Then start or restart the main UI server:

```bash
export ROUTERAI_API_KEY="sk-..."
export SILERO_BASE_URL="http://localhost:8790"
node routerai_recorder_server.js
```

## API Contract

The main UI server expects these local endpoints.

### TTS

```http
POST /tts
Content-Type: application/json
```

Request:

```json
{
  "model": "ru/v5_5_ru",
  "speaker": "xenia",
  "text": "Привет.",
  "sample_rate": 48000,
  "ssml": false
}
```

Response:

```text
audio/wav
```

### STT

```http
POST /stt
Content-Type: application/json
```

Request:

```json
{
  "model": "en/latest/jit_q",
  "language": "en",
  "version": "latest",
  "format": "jit_q",
  "audio": "BASE64_WAV",
  "audio_format": "wav"
}
```

Response:

```json
{
  "transcript": "recognized text"
}
```

