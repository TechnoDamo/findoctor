#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

allowed_file="$SEARXNG_DIR/../ragflow/allowed_resources.txt"
if [[ ! -f "$allowed_file" ]]; then
  echo "Файл allowed resources не найден: $allowed_file"
  exit 1
fi

first_host="$(python3 - <<'PY'
from pathlib import Path
from urllib.parse import urlparse

path = Path("../ragflow/allowed_resources.txt")
for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    host = urlparse(line if "://" in line else f"https://{line}").netloc
    if host.startswith("www."):
        host = host[4:]
    if host:
        print(host)
        break
PY
)"

if [[ -z "$first_host" ]]; then
  echo "No allowed host found in $allowed_file"
  exit 1
fi

query="site:$first_host finance"
echo "Запускаем allowed-domain search smoke test: $query"
curl -sS -G "$SEARXNG_BASE_URL/search" \
  --data-urlencode "q=$query" \
  --data-urlencode "format=json" \
  --data-urlencode "language=all" \
  | json_pretty
