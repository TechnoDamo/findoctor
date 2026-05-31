#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

"$SCRIPT_DIR/wait_for_tei.sh" >/dev/null

echo "Проверяем TEI /similarity..."
curl -sS \
  -X POST "$TEI_BASE_URL/similarity" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "source_sentence": "Should I take a new loan?",
      "sentences": [
        "Check monthly cash flow and debt load before taking new debt.",
        "Сегодня солнечная погода."
      ]
    }
  }' | json_pretty
