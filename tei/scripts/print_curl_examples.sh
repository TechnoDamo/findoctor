#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

cat <<EOF
# API-примеры TEI для ФинДоктора

export TEI_BASE_URL="${TEI_BASE_URL}"
export TEI_MODEL_ID="${TEI_MODEL_ID}"

# 1. Health
curl -i "\$TEI_BASE_URL/health"

# 2. Info
curl -sS "\$TEI_BASE_URL/info" | python3 -m json.tool

# 3. Native embeddings endpoint
curl -sS \\
  -X POST "\$TEI_BASE_URL/embed" \\
  -H "Content-Type: application/json" \\
  -d '{"inputs":["FinDoctor checks cash flow before recommendations.","Debt burden matters for loan advice."]}' \\
  | python3 -m json.tool

# 4. OpenAI-compatible embeddings endpoint
curl -sS \\
  -X POST "\$TEI_BASE_URL/v1/embeddings" \\
  -H "Content-Type: application/json" \\
  -d "{\\"model\\":\\"\$TEI_MODEL_ID\\",\\"input\\":[\\"FinDoctor embedding smoke test.\\"]}" \\
  | python3 -m json.tool

# 5. Similarity helper
curl -sS \\
  -X POST "\$TEI_BASE_URL/similarity" \\
  -H "Content-Type: application/json" \\
  -d '{"inputs":{"source_sentence":"Should I take a new loan?","sentences":["Check monthly cash flow and debt load first.","Unrelated text."]}}' \\
  | python3 -m json.tool
EOF
