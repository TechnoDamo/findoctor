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

require_var() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "$value" ]]; then
    echo "НЕТ:     $name"
    missing=1
  else
    echo "OK:      $name=$value"
  fi
}

echo "Проверка recommendation endpoint"
echo ""
echo "RECOMMENDATIONS_ENABLED=${RECOMMENDATIONS_ENABLED:-false}"
require_var "RAGFLOW_BASE_URL"
require_var "RAGFLOW_API_KEY"
require_var "RAGFLOW_DATASET_ID"
require_var "SEARXNG_BASE_URL"
require_var "RECOMMENDATION_ALLOWED_RESOURCES_FILE"

if [[ "$missing" -ne 0 ]]; then
  echo ""
  echo "Заполните backend/.env перед включением рекомендаций."
  exit 1
fi
