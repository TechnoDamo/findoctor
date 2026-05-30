#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

set -a && source "$ENV_FILE" && set +a

require() {
    local var=$1
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var is not set in .env"
        exit 1
    fi
}

require RAGFLOW_BASE_URL
require RAGFLOW_DATASET_ID
require RAGFLOW_ADMIN_EMAIL
require RAGFLOW_ADMIN_PASSWORD

encrypt_password() {
    docker exec docker-ragflow-cpu-1 python3 -c \
        "import sys; sys.path.insert(0,'/ragflow'); from api.utils.crypt import crypt; print(crypt('${1}'))" 2>/dev/null
}

echo "=== Clearing all documents from dataset $RAGFLOW_DATASET_ID ==="

enc_pwd=$(encrypt_password "$RAGFLOW_ADMIN_PASSWORD")
if [ -z "$enc_pwd" ]; then
    echo "ERROR: Failed to encrypt password. Is the RAGFlow container running?"
    exit 1
fi

COOKIE_FILE=$(mktemp)
trap 'rm -f "$COOKIE_FILE"' EXIT

echo "[1/3] Logging in..."
curl -s -c "$COOKIE_FILE" -X POST "$RAGFLOW_BASE_URL/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${RAGFLOW_ADMIN_EMAIL}\",\"password\":\"${enc_pwd}\"}" \
    -o /dev/null || { echo "ERROR: Login failed"; exit 1; }

echo "[2/3] Fetching document list..."
docs_json=$(curl -s -b "$COOKIE_FILE" \
    "${RAGFLOW_BASE_URL}/api/v1/datasets/${RAGFLOW_DATASET_ID}/documents?page=1&page_size=1000")

doc_ids=$(echo "$docs_json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
ids = [d['id'] for d in data.get('data',{}).get('docs', [])]
print(json.dumps(ids))
" 2>/dev/null || echo "[]")

doc_count=$(echo "$doc_ids" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$doc_count" = "0" ]; then
    echo "No documents found. Dataset is already empty."
    exit 0
fi

echo "[3/3] Deleting $doc_count documents..."
delete_resp=$(curl -s -b "$COOKIE_FILE" -X DELETE \
    "${RAGFLOW_BASE_URL}/api/v1/datasets/${RAGFLOW_DATASET_ID}/documents" \
    -H 'Content-Type: application/json' \
    -d "{\"ids\": $doc_ids}" 2>/dev/null)

echo "Delete response: $delete_resp"
echo ""
echo "=== Done: $doc_count documents deleted ==="
