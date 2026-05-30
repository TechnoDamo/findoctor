#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
SAMPLE_DIR="${SCRIPT_DIR}/../samples/test-docs"

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
require RAGFLOW_API_KEY
require RAGFLOW_DATASET_ID
require RAGFLOW_ADMIN_EMAIL
require RAGFLOW_ADMIN_PASSWORD

encrypt_password() {
    docker exec docker-ragflow-cpu-1 python3 -c \
        "import sys; sys.path.insert(0,'/ragflow'); from api.utils.crypt import crypt; print(crypt('${1}'))" 2>/dev/null
}

echo "=== Loading test documents into dataset $RAGFLOW_DATASET_ID ==="
echo "Files directory: $SAMPLE_DIR"
echo ""

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

echo "[2/3] Uploading documents..."

COUNT=0
for file in "$SAMPLE_DIR"/*.txt; do
    if [ ! -f "$file" ]; then
        echo "No .txt files found in $SAMPLE_DIR"
        exit 1
    fi
    fname=$(basename "$file")
    resp=$(curl -s -b "$COOKIE_FILE" -X POST "${RAGFLOW_BASE_URL}/api/v1/datasets/${RAGFLOW_DATASET_ID}/documents" \
        -F "file=@${file};filename=${fname}")
    code=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('code','?'))" 2>/dev/null || echo "parse_error")
    if [ "$code" = "0" ]; then
        COUNT=$((COUNT + 1))
        echo "  OK: $fname"
    else
        echo "  FAIL: $fname — $resp"
    fi
done

echo ""
echo "[3/3] Triggering document parsing..."
# List all documents to get their IDs
docs_json=$(curl -s -b "$COOKIE_FILE" \
    "${RAGFLOW_BASE_URL}/api/v1/datasets/${RAGFLOW_DATASET_ID}/documents?page=1&page_size=100")

doc_ids=$(echo "$docs_json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
ids = [d['id'] for d in data.get('data',{}).get('docs', [])]
print(json.dumps(ids))
" 2>/dev/null || echo "[]")

doc_count=$(echo "$doc_ids" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$doc_count" = "0" ]; then
    echo "WARNING: No documents found to parse."
    exit 0
fi

parse_resp=$(curl -s -b "$COOKIE_FILE" -X POST \
    "${RAGFLOW_BASE_URL}/api/v1/datasets/${RAGFLOW_DATASET_ID}/documents/parse" \
    -H 'Content-Type: application/json' \
    -d "{\"document_ids\": $doc_ids}" 2>/dev/null)

echo ""
echo "=== Done: uploaded $COUNT files, parsing $doc_count documents ==="
echo "Parse status: $parse_resp"
echo ""
echo "Documents are now being indexed. Track progress:"
echo "  curl -b <cookies> '$RAGFLOW_BASE_URL/api/v1/datasets/$RAGFLOW_DATASET_ID/documents' | python3 -c \"import json,sys; [print(f'{d[\\\"run\\\"]:8s} {d[\\\"name\\\"]}') for d in json.load(sys.stdin)['data']['docs']]\""
echo ""
echo "To verify after indexing completes (~1-3 min):"
echo "  make test"
