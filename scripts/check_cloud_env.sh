#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT_DIR/backend/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/backend/.env"
  set +a
fi

missing=0

check_optional_endpoint() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "$value" ]]; then
    echo "WARN: $name пустой"
  else
    echo "OK:   $name=$value"
  fi
}

echo "Проверка cloud/external LLM endpoint"
echo ""
check_optional_endpoint "LLM_BASE_URL"
check_optional_endpoint "LLM_MODEL"
check_optional_endpoint "STT_BASE_URL"
check_optional_endpoint "STT_MODEL"
check_optional_endpoint "TTS_BASE_URL"
check_optional_endpoint "TTS_MODEL"

if [[ -z "${LLM_API_KEY:-${OPENAI_API_KEY:-}}" ]]; then
  echo "WARN: не задан LLM_API_KEY или OPENAI_API_KEY"
else
  echo "OK:   LLM/OpenAI API key задан"
fi

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi
