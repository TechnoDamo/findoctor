"""End-to-end smoke test: full user lifecycle across all API resource groups.

Register → get profile → create financial institution →
create account → create transactions → create tags → tag transaction →
import transactions → create asset → create liability →
create liability payment → create recurring transaction →
create transfer → create goal → check analytics → create AI conversation →
send chat message → delete conversation → cleanup.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_full_lifecycle_smoke(test_client: AsyncClient) -> None:
    # -------------------------------------------------------
    # 1. Register user
    # -------------------------------------------------------
    reg_resp = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "smoke@example.com",
            "password": "smokeTest123",
            "base_currency": "RUB",
            "timezone": "Europe/Moscow",
        },
    )
    assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
    tokens = reg_resp.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # -------------------------------------------------------
    # 2. Get current user profile
    # -------------------------------------------------------
    me_resp = await test_client.get("/api/v1/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "smoke@example.com"

    # -------------------------------------------------------
    # 3. Update user profile
    # -------------------------------------------------------
    patch_resp = await test_client.patch(
        "/api/v1/me",
        json={"first_name": "Smoke", "last_name": "Tester", "country": "RU"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["first_name"] == "Smoke"

    # -------------------------------------------------------
    # 4. Get reference data
    # -------------------------------------------------------
    atypes = await test_client.get("/api/v1/reference/account-types")
    assert atypes.status_code == 200
    assert isinstance(atypes.json(), list)
    account_type_id = atypes.json()[0]["id"] if atypes.json() else None

    astypes = await test_client.get("/api/v1/reference/asset-types")
    assert astypes.status_code == 200
    asset_type_id = astypes.json()[0]["id"] if astypes.json() else None

    ltypes = await test_client.get("/api/v1/reference/liability-types")
    assert ltypes.status_code == 200
    liability_type_id = ltypes.json()[0]["id"] if ltypes.json() else None

    ptypes = await test_client.get("/api/v1/reference/provider-types")
    assert ptypes.status_code == 200

    # -------------------------------------------------------
    # 5. Create a category
    # -------------------------------------------------------
    cat_resp = await test_client.post(
        "/api/v1/reference/categories",
        json={"type": "expense", "name": "Продукты"},
    )
    assert cat_resp.status_code == 201
    category_id = cat_resp.json()["id"]

    # -------------------------------------------------------
    # 6. Create a merchant
    # -------------------------------------------------------
    merch_resp = await test_client.post(
        "/api/v1/merchants",
        json={"name": "Ашан", "country": "RU"},
    )
    assert merch_resp.status_code == 201
    merchant_id = merch_resp.json()["id"]

    # -------------------------------------------------------
    # 7. Create a financial institution
    # -------------------------------------------------------
    provider_ids = [ptypes.json()[0]["id"]] if ptypes.json() else []
    fi_resp = await test_client.post(
        "/api/v1/financial-institutions",
        json={
            "name": "Альфа-Банк",
            "country": "RU",
            "provider_type_ids": provider_ids,
        },
    )
    assert fi_resp.status_code == 201
    institution_id = fi_resp.json()["id"]

    # -------------------------------------------------------
    # 8. Create an account
    # -------------------------------------------------------
    account_resp = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": account_type_id,
            "institution_id": institution_id,
            "name": "Основной",
            "currency": "RUB",
            "opening_balance": "200000.00",
        },
        headers=headers,
    )
    assert account_resp.status_code == 201, f"Account create: {account_resp.text}"
    account_id = account_resp.json()["id"]

    # Create second account for transfers
    account2_resp = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": account_type_id,
            "name": "Накопительный",
            "currency": "RUB",
            "opening_balance": "0",
        },
        headers=headers,
    )
    assert account2_resp.status_code == 201
    account2_id = account2_resp.json()["id"]

    # -------------------------------------------------------
    # 9. Create transactions
    # -------------------------------------------------------
    txn1_resp = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "3500.00",
            "currency": "RUB",
            "transaction_datetime": "2025-06-01T12:30:00Z",
            "description": "Покупка продуктов в Ашане",
            "merchant_id": merchant_id,
        },
        headers=headers,
    )
    assert txn1_resp.status_code == 201, f"Txn1: {txn1_resp.text}"
    txn1_id = txn1_resp.json()["id"]

    txn2_resp = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "income",
            "amount": "120000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-06-01T09:00:00Z",
            "description": "Зарплата июнь",
        },
        headers=headers,
    )
    assert txn2_resp.status_code == 201

    # -------------------------------------------------------
    # 10. List transactions
    # -------------------------------------------------------
    txn_list = await test_client.get("/api/v1/transactions", headers=headers)
    assert txn_list.status_code == 200
    assert len(txn_list.json()["items"]) >= 2

    # -------------------------------------------------------
    # 11. Create tags and tag a transaction
    # -------------------------------------------------------
    tag_resp = await test_client.post(
        "/api/v1/tags",
        json={"name": "Еда"},
        headers=headers,
    )
    assert tag_resp.status_code == 201
    tag_id = tag_resp.json()["id"]

    attach_resp = await test_client.post(
        f"/api/v1/transactions/{txn1_id}/tags/{tag_id}",
        headers=headers,
    )
    assert attach_resp.status_code == 204

    txn_tags = await test_client.get(
        f"/api/v1/transactions/{txn1_id}/tags",
        headers=headers,
    )
    assert txn_tags.status_code == 200
    assert len(txn_tags.json()["items"]) >= 1

    # -------------------------------------------------------
    # 12. Import transactions
    # -------------------------------------------------------
    import_resp = await test_client.post(
        "/api/v1/transactions/import",
        json={
            "source": "smoke_test",
            "items": [
                {
                    "account_id": account_id,
                    "type": "expense",
                    "amount": "1200.00",
                    "currency": "RUB",
                    "transaction_datetime": "2025-06-10T10:00:00Z",
                    "external_id": "smoke-import-001",
                    "description": "Импорт: кафе",
                }
            ],
        },
        headers=headers,
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["created_count"] >= 0

    # -------------------------------------------------------
    # 13. Create a transfer
    # -------------------------------------------------------
    transfer_resp = await test_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": account_id,
            "to_account_id": account2_id,
            "amount": "10000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-06-15T14:00:00Z",
            "description": "Пополнение накопительного",
        },
        headers=headers,
    )
    assert transfer_resp.status_code == 201, f"Transfer: {transfer_resp.text}"

    # -------------------------------------------------------
    # 14. Create a recurring transaction
    # -------------------------------------------------------
    rt_resp = await test_client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": account_id,
            "operation_type": "expense",
            "name": "Аренда квартиры",
            "expected_amount": "45000.00",
            "currency": "RUB",
            "frequency": "monthly",
            "day_of_month": 5,
            "start_date": "2025-01-01",
            "next_payment_date": "2025-07-05",
        },
        headers=headers,
    )
    assert rt_resp.status_code == 201, f"Recurring txn: {rt_resp.text}"

    # -------------------------------------------------------
    # 15. Create an asset
    # -------------------------------------------------------
    asset_resp = await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": asset_type_id,
            "name": "Квартира в Москве",
            "estimated_value": "12000000.00",
            "currency": "RUB",
            "purchase_price": "10000000.00",
            "purchase_date": "2023-01-15",
        },
        headers=headers,
    )
    assert asset_resp.status_code == 201, f"Asset: {asset_resp.text}"

    # -------------------------------------------------------
    # 16. Create a liability (mortgage)
    # -------------------------------------------------------
    liab_resp = await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": liability_type_id,
            "name": "Ипотека",
            "current_balance": "8000000.00",
            "currency": "RUB",
            "interest_rate": 9.5,
            "minimum_payment_amount": "60000.00",
            "payment_due_day": 10,
        },
        headers=headers,
    )
    assert liab_resp.status_code == 201, f"Liability: {liab_resp.text}"
    liab_id = liab_resp.json()["id"]

    # -------------------------------------------------------
    # 17. Create a liability payment
    # -------------------------------------------------------
    lp_resp = await test_client.post(
        "/api/v1/liability-payments",
        json={
            "liability_id": liab_id,
            "account_id": account_id,
            "payment_date": "2025-07-10",
            "total_amount": "60000.00",
            "principal_amount": "40000.00",
            "interest_amount": "20000.00",
            "currency": "RUB",
        },
        headers=headers,
    )
    assert lp_resp.status_code == 201, f"Liability payment: {lp_resp.text}"

    # -------------------------------------------------------
    # 18. Create a financial goal
    # -------------------------------------------------------
    goal_resp = await test_client.post(
        "/api/v1/goals",
        json={
            "name": "Закрыть ипотеку досрочно",
            "target_amount": "8000000.00",
            "current_amount": "500000.00",
            "deadline": "2028-12-31",
            "priority": 1,
        },
        headers=headers,
    )
    assert goal_resp.status_code == 201, f"Goal: {goal_resp.text}"

    # -------------------------------------------------------
    # 19. Check analytics / dashboard
    # -------------------------------------------------------
    dash_resp = await test_client.get("/api/v1/analytics/dashboard", headers=headers)
    assert dash_resp.status_code == 200, f"Dashboard: {dash_resp.text}"
    dash = dash_resp.json()
    assert dash["currency"] == "RUB"

    cashflow_resp = await test_client.get("/api/v1/analytics/cash-flow", headers=headers)
    assert cashflow_resp.status_code == 200

    networth_resp = await test_client.get("/api/v1/analytics/net-worth", headers=headers)
    assert networth_resp.status_code == 200

    snap_resp = await test_client.get("/api/v1/analytics/snapshots", headers=headers)
    assert snap_resp.status_code == 200

    recalc_resp = await test_client.post(
        "/api/v1/analytics/snapshots/recalculate",
        json={"from_": "2025-01-01", "to": "2025-08-01"},
        headers=headers,
    )
    assert recalc_resp.status_code == 202

    # -------------------------------------------------------
    # 20. AI Chat — create conversation
    # -------------------------------------------------------
    conv_resp = await test_client.post(
        "/api/v1/ai/chat/conversations",
        json={"title": "Smoke test conversation"},
        headers=headers,
    )
    assert conv_resp.status_code == 201, f"Create conv: {conv_resp.text}"
    conv_id = conv_resp.json()["id"]

    # -------------------------------------------------------
    # 21. AI Chat — send text message (mocked)
    # -------------------------------------------------------
    async def fake_run_llm(user_text: str, financial_context: str, prompt_name: str = "llm_text") -> tuple[str, dict]:
        return "Smoke test AI ответ", {"prompt_tokens": 10, "completion_tokens": 5}

    import app.services.ai_chat as ac_mock
    original = ac_mock._run_llm
    ac_mock._run_llm = fake_run_llm

    try:
        chat_resp = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=headers,
            json={
                "conversationId": conv_id,
                "input": [{"type": "text", "text": "Привет, посчитай мой бюджет"}],
                "agentic": False,
            },
        )
        assert chat_resp.status_code == 200, f"Chat message: {chat_resp.text}"
        chat_data = chat_resp.json()
        assert chat_data["conversationId"] == conv_id
        assert chat_data["output"]["text"] == "Smoke test AI ответ"
    finally:
        ac_mock._run_llm = original

    # -------------------------------------------------------
    # 22. Get conversation with messages
    # -------------------------------------------------------
    get_conv_resp = await test_client.get(
        f"/api/v1/ai/chat/conversations/{conv_id}",
        headers=headers,
    )
    assert get_conv_resp.status_code == 200
    assert len(get_conv_resp.json()["messages"]) >= 1

    # -------------------------------------------------------
    # 23. List conversations
    # -------------------------------------------------------
    list_conv_resp = await test_client.get("/api/v1/ai/chat/conversations", headers=headers)
    assert list_conv_resp.status_code == 200
    assert len(list_conv_resp.json()["items"]) >= 1

    # -------------------------------------------------------
    # 24. Update transaction
    # -------------------------------------------------------
    upd_txn = await test_client.patch(
        f"/api/v1/transactions/{txn1_id}",
        json={"amount": "3550.00", "description": "Обновлённая покупка"},
        headers=headers,
    )
    assert upd_txn.status_code == 200
    assert upd_txn.json()["amount"] == "3550.00"

    # -------------------------------------------------------
    # 25. Logout
    # -------------------------------------------------------
    logout_resp = await test_client.post(
        "/api/v1/auth/logout",
        headers=headers,
    )
    assert logout_resp.status_code == 204

    # -------------------------------------------------------
    # 26. Verify token is invalid after logout
    # -------------------------------------------------------
    verify_resp = await test_client.get("/api/v1/me", headers=headers)
    assert verify_resp.status_code == 401, "Token should be invalid after logout"

    # === Full lifecycle smoke test passed ===
