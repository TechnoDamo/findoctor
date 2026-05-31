#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

echo "Ждем SearXNG на $SEARXNG_BASE_URL ..."

for _ in {1..60}; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' "$SEARXNG_BASE_URL" || true)"
  if [[ "$code" =~ ^(200|302)$ ]]; then
    echo "SearXNG доступен: HTTP $code"
    exit 0
  fi
  sleep 1
done

echo "SearXNG недоступен на $SEARXNG_BASE_URL"
exit 1
