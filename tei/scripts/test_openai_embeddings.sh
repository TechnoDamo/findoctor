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
    "model": os.environ.get("TEI_MODEL_ID", "BAAI/bge-m3"),
    "input": [
        "FinDoctor OpenAI-compatible embedding smoke test.",
        "Recommendations should use grounded evidence."
    ]
}, ensure_ascii=False))
PY
)"

echo "Проверяем TEI /v1/embeddings..."
curl -sS \
  -X POST "$TEI_BASE_URL/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  | tee /tmp/findoctor-tei-openai.json \
  | json_pretty

python3 - <<'PY'
import json

with open("/tmp/findoctor-tei-openai.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data.get("data") or []
if not items:
    raise SystemExit("Ожидался OpenAI-compatible data array")

vec = items[0].get("embedding") or []
print({"object": data.get("object"), "vectors": len(items), "dimensions": len(vec), "model": data.get("model")})
PY
