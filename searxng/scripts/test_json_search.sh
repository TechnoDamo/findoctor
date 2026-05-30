#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

"$SCRIPT_DIR/wait_for_searxng.sh" >/dev/null

echo "Запускаем JSON search smoke test..."
curl -sS -G "$SEARXNG_BASE_URL/search" \
  --data-urlencode "q=$SEARXNG_TEST_QUERY" \
  --data-urlencode "format=json" \
  --data-urlencode "language=all" \
  | tee /tmp/findoctor-searxng-test.json \
  | json_pretty

python3 - <<'PY'
import json

with open("/tmp/findoctor-searxng-test.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if "results" not in data:
    raise SystemExit("SearXNG JSON response did not contain results")

print(f"JSON response OK; results={len(data.get('results') or [])}")
PY
