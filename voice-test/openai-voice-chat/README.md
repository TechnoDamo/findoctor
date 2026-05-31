# OpenAI-Compatible Voice Chat

ChatGPT-style text and voice interface using OpenAI-compatible APIs, configured from YAML and `.env`.

The global contract this follows is:

- `/ai/chat/messages`
- `/ai/chat/audio`

Defined in:

```text
/Users/damir/Documents/ПрофИИт/api-contract/openapi.yaml
```

## Setup

```bash
cd /Users/damir/Documents/ПрофИИт/voice-test/openai-voice-chat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

```bash
OPENAI_COMPAT_API_KEY=sk-...
```

## Run

```bash
cd /Users/damir/Documents/ПрофИИт/voice-test/openai-voice-chat
source .venv/bin/activate
uvicorn server:app --host 127.0.0.1 --port 8788
```

Open:

```text
http://localhost:8788
```

## Configuration

- `config.models.yaml` controls LLM, STT, TTS model choices and voices.
- `contexts/llm_system.txt` controls the assistant.
- `contexts/stt_system.txt` controls transcription.
- `contexts/tts_system.txt` controls voiceover.

