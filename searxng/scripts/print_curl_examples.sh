#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

cat <<EOF
# API-примеры SearXNG для ФинДоктора

export SEARXNG_BASE_URL="${SEARXNG_BASE_URL}"

# 1. UI / проверка доступности
curl -i "\$SEARXNG_BASE_URL"

# 2. JSON search
curl -sS -G "\$SEARXNG_BASE_URL/search" \\
  --data-urlencode "q=site:cbr.ru key rate" \\
  --data-urlencode "format=json" \\
  --data-urlencode "language=all" \\
  | python3 -m json.tool

# 3. Напоминание о backend policy:
# SearXNG находит URL. Backend ФинДоктора все равно обязан отклонить каждый result,
# если его host отсутствует в ragflow/allowed_resources.txt.
EOF
