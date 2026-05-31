#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$TEI_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$TEI_DIR/.env"
  set +a
fi

TEI_BASE_URL="${TEI_BASE_URL:-http://localhost:8200}"
TEI_MODEL_ID="${TEI_MODEL_ID:-BAAI/bge-m3}"
TEI_TEST_INPUT="${TEI_TEST_INPUT:-FinDoctor checks cash flow, debts, goals, and emergency reserves before recommendations.}"

json_pretty() {
  python3 -m json.tool 2>/dev/null || cat
}

