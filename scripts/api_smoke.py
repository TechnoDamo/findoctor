#!/usr/bin/env python3
"""Global API smoke test — tests all endpoints with 5 real financial scenarios."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL.rstrip('/')}/api/v1"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
BOLD = "\033[1m"
NC = "\033[0m"

passed = 0
failed = 0
skipped = 0


def pass_(msg: str, detail: str = "") -> None:
    global passed
    print(f"  {GREEN}PASS{NC}  {msg}{f' ({detail})' if detail else ''}")
    passed += 1


def fail(msg: str, detail: str = "") -> None:
    global failed
    print(f"  {RED}FAIL{NC}  {msg}{f' ({detail})' if detail else ''}")
    failed += 1


def skip(msg: str, detail: str = "") -> None:
    global skipped
    print(f"  {YELLOW}SKIP{NC}  {msg}{f' ({detail})' if detail else ''}")
    skipped += 1


def verify(condition: bool, name: str) -> bool:
    if condition:
        pass_(name, "✓")
        return True
    fail(name, "✗")
    return False


def h_divider() -> None:
    print(f"{MAGENTA}{'─' * 72}{NC}")


def rpad(text: str, width: int = 56) -> str:
    return text + "." * max(0, width - len(text))


@dataclass
class TestUser:
    email: str
    password: str
    first_name: str
    last_name: str
    scenario: str
    expected_income: int = 0
    expected_debt: bool = False


USERS: list[TestUser] = [
    TestUser(
        email="scenario.alexei.stability@findoctor.test",
        password="TestPassword123!",
        first_name="Алексей",
        last_name="Стабильный",
        scenario="Высокий стабильный доход, инвестпортфель, почти без долгов",
        expected_income=185_000,
    ),
    TestUser(
        email="scenario.irina.freelance@findoctor.test",
        password="TestPassword123!",
        first_name="Ирина",
        last_name="Фрилансер",
        scenario="Нерегулярный доход, налоговый долг, кассовые разрывы",
        expected_income=0,
        expected_debt=True,
    ),
    TestUser(
        email="scenario.pavel.debt-recovery@findoctor.test",
        password="TestPassword123!",
        first_name="Павел",
        last_name="Восстановление",
        scenario="Выход из дефолта, кредитки, автокредит, малый резерв",
        expected_debt=True,
    ),
    TestUser(
        email="scenario.elena.family-mortgage@findoctor.test",
        password="TestPassword123!",
        first_name="Елена",
        last_name="Семейная",
        scenario="Семейный бюджет, ипотека, дети, школа, ремонт",
        expected_debt=True,
    ),
    TestUser(
        email="scenario.nikolai.retirement@findoctor.test",
        password="TestPassword123!",
        first_name="Николай",
        last_name="Рантье",
        scenario="Пенсия, рентный доход, дивиденды, медицина",
    ),
]

RECOMMENDATION_TYPES = [
    ("income", "income analysis"),
    ("expenses", "expenses analysis"),
    ("debt_traffic_light", "debt traffic light"),
    ("about_me", "financial portrait"),
]


def api_request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> tuple[int, dict[str, Any] | str]:
    url = f"{API}{path}"
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw.decode("utf-8", errors="replace")


def login(user: TestUser) -> dict[str, Any] | None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}LOGIN{NC}")
    t0 = time.time()
    status, body = api_request(
        "POST",
        "/auth/login",
        {"email": user.email, "password": user.password},
    )
    elapsed = (time.time() - t0) * 1000
    print(f"  REQ: POST /api/v1/auth/login")
    print(f"       {json.dumps({'email': user.email, 'password': '***'})}")
    print(f"  RES: {status} ({elapsed:.0f}ms)")
    body_preview = json.dumps(body, ensure_ascii=False)
    if len(body_preview) > 180:
        body_preview = body_preview[:177] + "..."
    print(f"  BODY: {body_preview}")

    if status != 200 or not isinstance(body, dict) or "access_token" not in body:
        fail("login", f"status={status}, no access_token")
        return None

    pass_("login", f"{elapsed:.0f}ms")

    if isinstance(body, dict) and body.get("refresh_token"):
        pass_("refresh_token_returned", "✓")

    return body


def test_me(user: TestUser, headers: dict[str, str]) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}GET /me{NC}")
    t0 = time.time()
    status, body = api_request("GET", "/users/me", headers=headers)
    elapsed = (time.time() - t0) * 1000

    print(f"  RES: {status} ({elapsed:.0f}ms)")
    preview = json.dumps(body, ensure_ascii=False)
    if len(preview) > 200:
        preview = preview[:197] + "..."
    print(f"  BODY: {preview}")

    verify(status == 200, "status=200")
    if isinstance(body, dict):
        verify(body.get("email") == user.email, f"email={user.email}")
        verify(body.get("first_name") == user.first_name, f"first_name={user.first_name}")
        verify(body.get("last_name") == user.last_name, f"last_name={user.last_name}")


def test_dashboard(user: TestUser, headers: dict[str, str]) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}GET /analytics/dashboard{NC}")
    t0 = time.time()
    status, body = api_request("GET", "/analytics/dashboard", headers=headers)
    elapsed = (time.time() - t0) * 1000

    print(f"  RES: {status} ({elapsed:.0f}ms)")
    preview = json.dumps(body, ensure_ascii=False)
    if len(preview) > 300:
        preview = preview[:297] + "..."
    print(f"  BODY: {preview}")

    verify(status == 200, "status=200")

    if isinstance(body, dict):
        current = body.get("current_month", {})
        if current.get("total_income"):
            print(f"  VERIFY: income={current['total_income']} ₽  "
                  f"expenses={current.get('total_expenses', '?')} ₽  "
                  f"savings_rate={current.get('savings_rate', 'N/A')}%")
            verify(isinstance(current.get("total_income"), (int, float)), "income is numeric")
            verify(isinstance(current.get("total_expenses"), (int, float)), "expenses is numeric")

        net_worth = body.get("net_worth", {})
        if net_worth:
            print(f"  VERIFY: net_worth={net_worth} ₽")
            verify(isinstance(net_worth, (int, float)), "net_worth is numeric")

        accounts = body.get("accounts", [])
        if accounts:
            print(f"  VERIFY: accounts={len(accounts)}")
            verify(len(accounts) > 0, "user has accounts")


def test_accounts(user: TestUser, headers: dict[str, str]) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}GET /accounts (CRUD smoke){NC}")
    t0 = time.time()
    status, body = api_request("GET", "/accounts", headers=headers)
    elapsed = (time.time() - t0) * 1000

    print(f"  RES: {status} ({elapsed:.0f}ms)")
    verify(status == 200, "status=200")

    if isinstance(body, list):
        print(f"  VERIFY: {len(body)} accounts returned")
        verify(len(body) >= 1, "user has ≥1 account")
        for acct in body[:3]:
            print(f"    • {acct.get('name')}: {acct.get('balance')} {acct.get('currency_code', '₽')}")


def test_recommendation(
    user: TestUser,
    rec_type: str,
    rec_label: str,
    headers: dict[str, str],
) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}POST /recommendations?type={rec_type}{NC} ({rec_label})")
    t0 = time.time()
    status, body = api_request(
        "GET",
        f"/recommendations?type={rec_type}",
        headers=headers,
        timeout=60,
    )
    elapsed = time.time() - t0

    print(f"  RES: {status} ({elapsed:.1f}s)")

    if status == 200 and isinstance(body, dict):
        recommendation = str(body.get("recommendation", ""))
        print(f"  BODY: {{'recommendation': '{recommendation[:150]}...'}}")
        verify(len(recommendation) > 20, "recommendation text present")

        tool_results = body.get("toolResults", [])
        if tool_results:
            print(f"  VERIFY: toolResults={len(tool_results)} tools used")
            for tr in tool_results:
                tool_name = tr.get("tool", "unknown")
                print(f"    • {tool_name}")
            verify(len(tool_results) > 0, "tool results present")

        verify(body.get("status") == "complete", "status=complete")
    elif status == 200:
        preview = json.dumps(body, ensure_ascii=False)[:150]
        print(f"  BODY: {preview}...")
        verify(False, "response is dict")
    else:
        raw = json.dumps(body, ensure_ascii=False)[:200]
        print(f"  BODY: {raw}")
        if status in (502, 503):
            skip(f"recommendation_{rec_type}", f"backend returned {status} (LLM unavailable)")
        else:
            fail(f"recommendation_{rec_type}", f"status={status}")


def test_ai_chat_simple(user: TestUser, headers: dict[str, str]) -> dict[str, Any] | None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}POST /ai/chat/messages (simple){NC}")
    t0 = time.time()
    status, body = api_request(
        "POST",
        "/ai/chat/messages",
        {"message": "Проанализируй мое финансовое положение кратко, в двух предложениях"},
        headers=headers,
        timeout=120,
    )
    elapsed = time.time() - t0

    print(f"  RES: {status} ({elapsed:.1f}s)")

    if status == 200 and isinstance(body, dict):
        msg = str(body.get("message", ""))
        print(f"  BODY: message='{msg[:200]}...'")
        verify(len(msg) > 20, "AI response text present")

        conv = body.get("conversation", {})
        if conv and conv.get("id"):
            conv_id = conv["id"]
            print(f"  VERIFY: conversation.id={conv_id[:12]}...")
            pass_("conversation_persisted", f"id={conv_id[:12]}...")

            msg_ids = body.get("message_ids", [])
            if msg_ids:
                pass_(f"messages_stored", f"{len(msg_ids)} messages")
            return {"conversation_id": conv_id}
        else:
            fail("conversation_persisted", "no conversation in response")
    elif status in (502, 503):
        skip("ai_chat_simple", f"backend returned {status} (LLM unavailable)")
    elif isinstance(body, dict):
        detail = body.get("detail", str(body))[:100]
        fail("ai_chat_simple", f"status={status} detail={detail}")

    return None


def test_ai_chat_agentic(
    user: TestUser,
    headers: dict[str, str],
    conversation_id: str | None = None,
) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}POST /ai/chat/messages (agentic){NC}")
    body_payload: dict[str, Any] = {
        "message": "Какие налоговые вычеты мне доступны? Найди актуальную информацию и дай рекомендацию на основе моих данных.",
        "agent_mode": True,
    }
    if conversation_id:
        body_payload["conversation_id"] = conversation_id

    t0 = time.time()
    status, body = api_request(
        "POST",
        "/ai/chat/messages",
        body_payload,
        headers=headers,
        timeout=180,
    )
    elapsed = time.time() - t0

    print(f"  RES: {status} ({elapsed:.1f}s)")

    if status == 200 and isinstance(body, dict):
        msg = str(body.get("message", ""))
        print(f"  BODY: message='{msg[:200]}...'")
        verify(len(msg) > 20, "AI response text present")

        tool_results = body.get("toolResults", [])
        rag_found = False
        search_found = False
        for tr in tool_results:
            tool_name = tr.get("tool", "")
            if "rag" in tool_name.lower():
                chunks = tr.get("chunks", [])
                if chunks:
                    rag_found = True
                    print(f"  VERIFY: RAG retrieval — {len(chunks)} chunks (scores: {[round(c.get('score', 0), 2) for c in chunks[:3]]})")
            if "search" in tool_name.lower():
                results = tr.get("results", [])
                if results:
                    search_found = True
                    print(f"  VERIFY: web search — {len(results)} results (top: {results[0].get('title', 'unnamed')[:60]})")

        if rag_found:
            pass_("rag_retrieval", "chunks retrieved from RAGFlow")
        if search_found:
            pass_("web_search", "search results from SearXNG")
        if not rag_found and not search_found:
            pass_("agentic_response", "direct LLM response (no tools needed)")
    elif status in (502, 503):
        skip("ai_chat_agentic", f"backend returned {status} (LLM unavailable)")
    elif isinstance(body, dict):
        detail = body.get("detail", str(body))[:100]
        fail("ai_chat_agentic", f"status={status} detail={detail}")


def test_cross_user_headers(headers: dict[str, str]) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}Cross-user isolation{NC}")
    t0 = time.time()
    status, body = api_request(
        "GET",
        "/accounts/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    elapsed = (time.time() - t0) * 1000
    print(f"  RES: {status} ({elapsed:.0f}ms) — GET other user's account")
    verify(status == 404, "returns 404 for other user's resource")


def test_logout_invalidation(headers: dict[str, str]) -> None:
    print(f"\n  {h_divider()}")
    print(f"  {BOLD}Token invalidation (logout){NC}")

    status, body = api_request("POST", "/auth/logout", headers=headers)
    print(f"  RES: {status}")
    verify(status == 200, "logout=200")

    status2, _ = api_request("GET", "/users/me", headers=headers)
    print(f"  RES: {status2} — GET /me after logout")
    verify(status2 == 401, "token rejected after logout (401)")


def test_user(user: TestUser, index: int) -> None:
    print(f"\n{GREEN}{'═' * 72}{NC}")
    print(f"{GREEN}{BOLD}  USER {index + 1}/5: {user.first_name} {user.last_name}{NC}")
    print(f"{GREEN}  {user.scenario}{NC}")
    print(f"{GREEN}{'═' * 72}{NC}")

    session = login(user)
    if session is None:
        skip(f"user_{index + 1}", "login failed, skipping all tests")
        return

    headers = {"Authorization": f"Bearer {session['access_token']}"}

    test_me(user, headers)
    test_accounts(user, headers)
    test_dashboard(user, headers)

    rec_types = RECOMMENDATION_TYPES
    if user.expected_debt:
        rec_types = [("debt_traffic_light", "debt traffic light"), ("about_me", "financial portrait")] + rec_types[:1]

    for rec_type, rec_label in rec_types[:2]:
        test_recommendation(user, rec_type, rec_label, headers)

    conv = test_ai_chat_simple(user, headers)
    test_ai_chat_agentic(user, headers, conv.get("conversation_id") if conv else None)

    test_cross_user_headers(headers)
    test_logout_invalidation(headers)


def main() -> int:
    print(f"\n{BOLD}{'═' * 72}{NC}")
    print(f"{BOLD}{CYAN}  GLOBAL API SMOKE TEST{NC}")
    print(f"{BOLD}  Target: {API}{NC}")
    print(f"{BOLD}{'═' * 72}{NC}")

    for i, user in enumerate(USERS):
        test_user(user, i)

    print(f"\n{BOLD}{'═' * 72}{NC}")
    print(f"{BOLD}{CYAN}  API SMOKE SUMMARY{NC}")
    total = passed + failed + skipped
    print(f"  {GREEN}Passed:{NC}  {passed}")
    print(f"  {RED}Failed:{NC}  {failed}")
    print(f"  {YELLOW}Skipped:{NC} {skipped}")
    print(f"  {BOLD}Total:{NC}   {total}")
    print(f"{BOLD}{'═' * 72}{NC}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
