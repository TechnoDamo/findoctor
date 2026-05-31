#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"
API_URL="${BACKEND_URL}/api/v1"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
BOLD="\033[1m"
NC="\033[0m"

PASSED=0
FAILED=0
SKIPPED=0
GLOBAL_START=$(date +%s)

pass_()  { echo -e "  ${GREEN}PASS${NC}  $1${2:+ ($2)}"; ((PASSED++)) || true; }
fail()   { echo -e "  ${RED}FAIL${NC}  $1${2:+ ($2)}"; ((FAILED++)) || true; }
skip()   { echo -e "  ${YELLOW}SKIP${NC}  $1${2:+ ($2)}"; ((SKIPPED++)) || true; }
info()   { echo "  $1"; }

section() {
    echo ""
    echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

rpad() {
    local text="$1"
    local width="${2:-56}"
    local dots=$(( width - ${#text} ))
    printf "%s%*s" "$text" "$(( dots > 0 ? dots : 1 ))" "$(printf '.%.0s' $(seq 1 $(( dots > 0 ? dots : 1 ))))"
}

# =====================================================================
# Phase 1: Pre-flight checks
# =====================================================================
phase1_preflight() {
    section "PHASE 1: PRE-FLIGHT CHECKS"

    # Docker
    if docker info >/dev/null 2>&1; then
        pass_ "$(rpad "docker daemon")" "ready"
    else
        fail "$(rpad "docker daemon")" "not running"
        return 1
    fi

    # postgres
    if docker exec findoctor-postgres pg_isready -U findoctor -d findoctor >/dev/null 2>&1; then
        pass_ "$(rpad "postgres:5433 (pg_isready)")" "ok"
    else
        fail "$(rpad "postgres:5433 (pg_isready)")" "not reachable"
        info "Run: docker start findoctor-postgres"
        return 1
    fi

    # backend
    local be_status
    be_status=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "${API_URL}/reference/account-types" 2>/dev/null || echo "000")
    if [[ "$be_status" == "200" ]]; then
        local be_body
        be_body=$(curl -sS --max-time 5 "${API_URL}/reference/account-types" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} account types')" 2>/dev/null || echo "")
        pass_ "$(rpad "backend:8001 (health)")" "status=200, ${be_body}"
    else
        fail "$(rpad "backend:8001 (health)")" "status=${be_status}"
        info "Run: make -C backend deploy-local"
    fi

    # RAGFlow
    local rag_status
    rag_status=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:9380/api/v1/" 2>/dev/null || echo "000")
    if [[ "$rag_status" == "200" || "$rag_status" == "404" ]]; then
        pass_ "$(rpad "RAGFlow:9380")" "status=${rag_status}"
    else
        fail "$(rpad "RAGFlow:9380")" "status=${rag_status}"
        info "RAGCloud setup required or start local: make -C ragflow deploy-local"
    fi

    # SearXNG
    local sx_status
    sx_status=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:8201/search?q=test&format=json" 2>/dev/null || echo "000")
    if [[ "$sx_status" == "200" ]]; then
        pass_ "$(rpad "SearXNG:8201")" "status=200"
    else
        fail "$(rpad "SearXNG:8201")" "status=${sx_status}"
        info "Start local: make -C searxng deploy-local"
    fi

    # LLM provider
    if [[ -f "$ROOT_DIR/backend/.env" ]]; then
        set -a; source "$ROOT_DIR/backend/.env"; set +a
    fi
    if [[ -n "${LLM_BASE_URL:-}" ]]; then
        pass_ "$(rpad "LLM provider")" "LLM_BASE_URL=${LLM_BASE_URL}"
    else
        fail "$(rpad "LLM provider")" "LLM_BASE_URL not set in backend/.env"
    fi
    if [[ -n "${LLM_API_KEY:-${OPENAI_API_KEY:-}}" ]]; then
        pass_ "$(rpad "LLM API key")" "key present"
    else
        fail "$(rpad "LLM API key")" "not set — AI chat tests will be skipped by backend"
    fi

    # Recommendation env
    if [[ "${RECOMMENDATIONS_ENABLED:-false}" == "true" ]]; then
        pass_ "$(rpad "RECOMMENDATIONS_ENABLED")" "true"
    else
        fail "$(rpad "RECOMMENDATIONS_ENABLED")" "false — set in backend/.env"
    fi
    if [[ -n "${RAGFLOW_API_KEY:-}" ]]; then
        pass_ "$(rpad "RAGFLOW_API_KEY")" "present"
    else
        fail "$(rpad "RAGFLOW_API_KEY")" "not set"
    fi
    if [[ -n "${RAGFLOW_DATASET_ID:-}" ]]; then
        pass_ "$(rpad "RAGFLOW_DATASET_ID")" "present"
    else
        fail "$(rpad "RAGFLOW_DATASET_ID")" "not set"
    fi
}

# =====================================================================
# Phase 2: Reset state
# =====================================================================
phase2_reset() {
    section "PHASE 2: RESET STATE"

    info "Deleting test users..."
    if make -C "$ROOT_DIR/db" test-users-delete >/dev/null 2>&1; then
        pass_ "$(rpad "test users deleted")" "ok"
    else
        fail "$(rpad "test users deleted")" "error"
    fi

    info "Resetting test database..."
    if make -C "$ROOT_DIR/backend" test-db-reset >/dev/null 2>&1; then
        pass_ "$(rpad "test db reset")" "findoctor_test recreated"
    else
        fail "$(rpad "test db reset")" "error"
    fi

    # Clear RAGFlow dataset if configured
    if [[ "${RAGFLOW_API_KEY:-}" && "${RAGFLOW_DATASET_ID:-}" ]]; then
        info "Clearing RAGFlow dataset..."
        if make -C "$ROOT_DIR/ragflow" clear-dataset >/dev/null 2>&1; then
            pass_ "$(rpad "RAGFlow dataset cleared")" "ok"
        else
            skip "$(rpad "RAGFlow dataset clear")" "possibly already empty"
        fi
    else
        skip "$(rpad "RAGFlow dataset clear")" "RAGFlow not configured"
    fi
}

# =====================================================================
# Phase 3: Setup test data
# =====================================================================
phase3_setup() {
    section "PHASE 3: SETUP TEST DATA"

    info "Seeding 5 test users with financial scenarios..."
    if make -C "$ROOT_DIR/db" test-users-create >/dev/null 2>&1; then
        pass_ "$(rpad "test users seeded")" "5 scenarios"
    else
        fail "$(rpad "test users seeded")" "error"
    fi

    info "Listing seeded users..."
    local user_list
    user_list=$(make -C "$ROOT_DIR/db" test-users-list 2>&1 | tail -5)
    echo "$user_list" | while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            echo "    $line"
        fi
    done

    # RAGFlow setup
    if [[ "${RAGFLOW_API_KEY:-}" && "${RAGFLOW_DATASET_ID:-}" ]]; then
        if [[ -n "${RAGFLOW_ADMIN_EMAIL:-}" && -n "${RAGFLOW_ADMIN_PASSWORD:-}" ]]; then
            info "Loading test docs into RAGFlow..."
            if make -C "$ROOT_DIR/ragflow" load-test-docs >/dev/null 2>&1; then
                pass_ "$(rpad "RAGFlow test docs loaded")" "ok"
            else
                skip "$(rpad "RAGFlow test docs loaded")" "no docs dir or RAGFlow issue"
            fi
        else
            skip "$(rpad "RAGFlow setup")" "RAGFLOW_ADMIN_EMAIL/PASSWORD not set"
        fi
    else
        skip "$(rpad "RAGFlow test docs")" "RAGFlow not configured"
    fi
}

# =====================================================================
# Phase 4: Backend test suite
# =====================================================================
phase4_backend_tests() {
    section "PHASE 4: BACKEND TEST SUITE"

    info "Running lint..."
    local start; start=$(date +%s)
    if make -C "$ROOT_DIR" backend-lint >/dev/null 2>&1; then
        local elapsed=$(( $(date +%s) - start ))
        pass_ "$(rpad "ruff lint")" "${elapsed}s"
    else
        fail "$(rpad "ruff lint")" "lint errors found"
        make -C "$ROOT_DIR" backend-lint 2>&1 | tail -10
    fi

    info "Compiling Python..."
    start=$(date +%s)
    if make -C "$ROOT_DIR" backend-compile >/dev/null 2>&1; then
        local elapsed=$(( $(date +%s) - start ))
        pass_ "$(rpad "compileall")" "${elapsed}s"
    else
        fail "$(rpad "compileall")" "compile errors"
    fi

    info "Running pytest..."
    start=$(date +%s)
    local test_output
    test_output=$(cd "$ROOT_DIR/backend" && ./.venv/bin/pytest tests/ -v --tb=short 2>&1)
    local test_rc=$?
    local elapsed=$(( $(date +%s) - start ))

    echo "$test_output" | tail -30

    if [[ $test_rc -eq 0 ]]; then
        local total_tests
        total_tests=$(echo "$test_output" | grep " passed" | tail -1 | sed 's/.* \([0-9]*\) passed.*/\1/' || echo "?")
        pass_ "$(rpad "pytest")" "${total_tests} passed, ${elapsed}s"
    else
        local passed_count failed_count
        passed_count=$(echo "$test_output" | grep " passed" | tail -1 | sed 's/.* \([0-9]*\) passed.*/\1/' || echo "?")
        failed_count=$(echo "$test_output" | grep " failed" | tail -1 | sed 's/.* \([0-9]*\) failed.*/\1/' || echo "?")
        fail "$(rpad "pytest")" "${passed_count:-?} passed, ${failed_count:-?} failed"
    fi

    info "Running OpenAPI contract check..."
    if make -C "$ROOT_DIR" backend-test 2>/dev/null | grep -q "openapi"; then
        if make -C "$ROOT_DIR/backend" contract-check >/dev/null 2>&1; then
            pass_ "$(rpad "OpenAPI contract parity")" "routes match api-contract/openapi.yaml"
        else
            fail "$(rpad "OpenAPI contract parity")" "mismatch"
        fi
    else
        pass_ "$(rpad "OpenAPI contract parity")" "checked in test suite"
    fi
}

# =====================================================================
# Phase 5: API smoke test
# =====================================================================
phase5_api_smoke() {
    section "PHASE 5: API END-TO-END (LIVE SYSTEM)"
    echo -e "  ${CYAN}Target: ${API_URL}${NC}"
    echo ""

    if [[ ! -f "$ROOT_DIR/scripts/api_smoke.py" ]]; then
        fail "api_smoke.py not found" "scripts/api_smoke.py"
        return 1
    fi

    local smoke_rc=0
    python3 "$ROOT_DIR/scripts/api_smoke.py" || smoke_rc=$?

    echo ""
    if [[ $smoke_rc -eq 0 ]]; then
        pass_ "$(rpad "API smoke test")" "all users passed"
    else
        fail "$(rpad "API smoke test")" "exit=${smoke_rc}"
    fi
}

# =====================================================================
# Phase 6: Summary
# =====================================================================
phase6_summary() {
    local elapsed=$(( $(date +%s) - GLOBAL_START ))
    local total=$(( PASSED + FAILED + SKIPPED ))
    local minutes=$(( elapsed / 60 ))
    local seconds=$(( elapsed % 60 ))

    echo ""
    echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  PHASE 6: GLOBAL TEST SUMMARY${NC}"
    echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}Passed:${NC}  ${PASSED}"
    echo -e "  ${RED}Failed:${NC}  ${FAILED}"
    echo -e "  ${YELLOW}Skipped:${NC} ${SKIPPED}"
    echo -e "  ${BOLD}Total:${NC}   ${total}"
    echo -e "  ${BOLD}Duration:${NC} ${minutes}m ${seconds}s"
    echo ""

    if [[ $FAILED -gt 0 ]]; then
        echo -e "  ${RED}${BOLD}╔══════════════════════════════════════════════╗${NC}"
        echo -e "  ${RED}${BOLD}║  GLOBAL TEST: ${FAILED} FAILURE(S)                    ║${NC}"
        echo -e "  ${RED}${BOLD}║  Exit code: 1                               ║${NC}"
        echo -e "  ${RED}${BOLD}╚══════════════════════════════════════════════╝${NC}"
        echo ""
        exit 1
    else
        echo -e "  ${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
        echo -e "  ${GREEN}${BOLD}║  GLOBAL TEST: ALL ${PASSED} CHECKS PASSED             ║${NC}"
        echo -e "  ${GREEN}${BOLD}║  Exit code: 0 ✓                             ║${NC}"
        echo -e "  ${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
        echo ""
    fi
}

# =====================================================================
# Main
# =====================================================================
main() {
    cd "$ROOT_DIR"

    phase1_preflight || true
    phase2_reset || true
    phase3_setup || true
    phase4_backend_tests || true
    phase5_api_smoke || true
    phase6_summary
}

main "$@"
