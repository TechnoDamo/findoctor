#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEARXNG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$SEARXNG_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$SEARXNG_DIR/.env"
  set +a
fi

SEARXNG_BASE_URL="${SEARXNG_BASE_URL:-http://localhost:8201}"
SEARXNG_TEST_QUERY="${SEARXNG_TEST_QUERY:-site:cbr.ru key rate}"

json_pretty() {
  python3 -m json.tool 2>/dev/null || cat
}

