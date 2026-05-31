#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

template="$SEARXNG_DIR/config/settings.yml.example"
target="$SEARXNG_DIR/config/settings.yml"
export SEARXNG_DIR

if [[ ! -f "$template" ]]; then
  echo "Нет $template"
  exit 1
fi

python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["SEARXNG_DIR"])
template = root / "config" / "settings.yml.example"
target = root / "config" / "settings.yml"

text = template.read_text(encoding="utf-8")
text = text.replace("__SEARXNG_SECRET_KEY__", os.environ.get("SEARXNG_SECRET_KEY", ""))
text = text.replace("__SEARXNG_REQUEST_TIMEOUT__", os.environ.get("SEARXNG_REQUEST_TIMEOUT", "10"))
target.write_text(text, encoding="utf-8")
PY

echo "config/settings.yml сгенерирован"
