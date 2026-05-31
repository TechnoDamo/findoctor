#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

"$SCRIPT_DIR/wait_for_tei.sh" >/dev/null

payload="$(python3 - <<'PY'
import json
import os

print(json.dumps({
    "inputs": [
        os.environ.get("TEI_TEST_INPUT", "FinDoctor embedding smoke test."),
        "Emergency reserve and debt load are important recommendation signals."
    ]
}, ensure_ascii=False))
PY
)"

echo "Проверяем TEI /embed..."
curl -sS \
  -X POST "$TEI_BASE_URL/embed" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  | tee /tmp/findoctor-tei-embed.json \
  | json_pretty

python3 - <<'PY'
import json

with open("/tmp/findoctor-tei-embed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list) or not data:
    raise SystemExit("Ожидался непустой список embeddings")

first = data[0]
if not isinstance(first, list) or not first:
    raise SystemExit("Ожидался embedding vector list")

print({"vectors": len(data), "dimensions": len(first), "first_values": first[:5]})
PY
