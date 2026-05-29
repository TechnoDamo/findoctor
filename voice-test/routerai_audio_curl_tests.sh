#!/usr/bin/env bash
set -euo pipefail

# RouterAI audio model smoke tests.
#
# Usage:
#   export ROUTERAI_API_KEY="sk-..."
#   ./routerai_audio_curl_tests.sh all
#   ./routerai_audio_curl_tests.sh tts
#   ./routerai_audio_curl_tests.sh stt
#
# The web recorder saves:
#   ./request_audio/test-audio.wav  - audio used by STT tests
#   ./test-text.txt   - text used by TTS tests

BASE_URL="${ROUTERAI_BASE_URL:-https://routerai.ru/api/v1}"
API_KEY="${ROUTERAI_API_KEY:-}"
TEST_AUDIO="${TEST_AUDIO:-request_audio/test-audio.wav}"
TEST_TEXT="${TEST_TEXT:-test-text.txt}"
OUT_DIR="${OUT_DIR:-routerai-test-results}"
MODEL_FILE="${MODEL_FILE:-routerai_models.json}"
MODE="${1:-all}"

if [[ ! -f "$MODEL_FILE" ]]; then
  echo "Missing model file: $MODEL_FILE"
  exit 1
fi

TTS_MODELS=()
while IFS= read -r model_id; do
  TTS_MODELS+=("$model_id")
done < <(node -e 'const fs=require("fs"); const m=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); for (const x of m.tts) console.log(x.id)' "$MODEL_FILE")

STT_MODELS=()
while IFS= read -r model_id; do
  STT_MODELS+=("$model_id")
done < <(node -e 'const fs=require("fs"); const m=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); for (const x of m.stt) console.log(x.id)' "$MODEL_FILE")

VOICES=()
while IFS= read -r voice_id; do
  VOICES+=("$voice_id")
done < <(node -e 'const fs=require("fs"); const m=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); for (const x of m.voices) console.log(x)' "$MODEL_FILE")

require_api_key() {
  if [[ -z "$API_KEY" ]]; then
    echo "ROUTERAI_API_KEY is not set."
    echo "Run: export ROUTERAI_API_KEY='sk-...'"
    exit 1
  fi
}

slug() {
  printf "%s" "$1" | tr '/:' '__'
}

json_escape_file() {
  node -e '
    const fs = require("fs");
    const path = process.argv[1];
    const fallback = process.argv[2];
    const text = fs.existsSync(path) ? fs.readFileSync(path, "utf8").trim() : fallback;
    process.stdout.write(JSON.stringify(text || fallback));
  ' "$1" "$2"
}

audio_format() {
  case "${TEST_AUDIO##*.}" in
    wav|WAV) printf "wav" ;;
    mp3|MP3) printf "mp3" ;;
    flac|FLAC) printf "flac" ;;
    m4a|M4A) printf "m4a" ;;
    ogg|OGG) printf "ogg" ;;
    aac|AAC) printf "aac" ;;
    aiff|AIFF) printf "aiff" ;;
    *) printf "wav" ;;
  esac
}

base64_audio() {
  if [[ ! -f "$TEST_AUDIO" ]]; then
    echo "Missing $TEST_AUDIO. Start the recorder with: node routerai_recorder_server.js" >&2
    exit 1
  fi
  base64 < "$TEST_AUDIO" | tr -d '\n'
}

run_tts_model() {
  local model="$1"
  local voice="${2:-alloy}"
  local model_slug
  model_slug="$(slug "$model")"
  local out="$OUT_DIR/tts_${model_slug}_${voice}.sse.jsonl"
  local prompt_json
  prompt_json="$(json_escape_file "$TEST_TEXT" "Скажите коротко: тест синтеза речи RouterAI.")"

  echo "TTS: $model voice=$voice -> $out"
  node - "$model" "$voice" "$prompt_json" <<'NODE' | \
    curl --silent --show-error --no-buffer \
      -X POST "$BASE_URL/chat/completions" \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      --data @- | tee "$out" >/dev/null
const model = process.argv[2];
const voice = process.argv[3];
const prompt = JSON.parse(process.argv[4]);
process.stdout.write(JSON.stringify({
  model,
  modalities: ["text", "audio"],
  messages: [
    {
      role: "system",
      content: "You are a text-to-speech voiceover engine. Speak exactly the user's text verbatim. Do not answer, rewrite, summarize, translate, add introductions, or add closing remarks."
    },
    {
      role: "user",
      content: `Voice over this exact text:\n\n${prompt}`
    }
  ],
  audio: {
    voice,
    format: "pcm16"
  },
  stream: true
}));
NODE
}

run_stt_model() {
  local model="$1"
  local model_slug
  model_slug="$(slug "$model")"
  local out="$OUT_DIR/stt_${model_slug}.json"
  local audio_b64
  local fmt
  audio_b64="$(base64_audio)"
  fmt="$(audio_format)"

  echo "STT: $model -> $out"
  node - "$model" "$fmt" "$audio_b64" <<'NODE' | \
    curl --silent --show-error \
      -X POST "$BASE_URL/chat/completions" \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      --data @- > "$out"
const model = process.argv[2];
const format = process.argv[3];
const audio = process.argv[4];
process.stdout.write(JSON.stringify({
  model,
  messages: [
    {
      role: "user",
      content: [
        {
          type: "text",
          text: "Transcribe this audio exactly. Return only the transcript text."
        },
        {
          type: "input_audio",
          input_audio: {
            data: audio,
            format
          }
        }
      ]
    }
  ]
}));
NODE
}

run_tts() {
  mkdir -p "$OUT_DIR"
  for model in "${TTS_MODELS[@]}"; do
    run_tts_model "$model" "alloy"
  done
}

run_stt() {
  mkdir -p "$OUT_DIR"
  for model in "${STT_MODELS[@]}"; do
    run_stt_model "$model"
  done
}

list_models() {
  echo "TTS models:"
  printf "  %s\n" "${TTS_MODELS[@]}"
  echo
  echo "STT models:"
  printf "  %s\n" "${STT_MODELS[@]}"
  echo
  echo "TTS voices:"
  printf "  %s\n" "${VOICES[@]}"
}

case "$MODE" in
  all)
    require_api_key
    run_tts
    run_stt
    ;;
  tts)
    require_api_key
    run_tts
    ;;
  stt)
    require_api_key
    run_stt
    ;;
  list)
    list_models
    ;;
  *)
    echo "Unknown mode: $MODE"
    echo "Use: all, tts, stt, list"
    exit 1
    ;;
esac
