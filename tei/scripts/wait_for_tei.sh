#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

echo "Ждем TEI на $TEI_BASE_URL ..."

for _ in {1..180}; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' "$TEI_BASE_URL/health" || true)"
  if [[ "$code" == "200" ]]; then
    echo "TEI здоров"
    exit 0
  fi
  sleep 2
done

echo "TEI не прошел health check на $TEI_BASE_URL"
exit 1
