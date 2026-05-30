"""Тесты импорта транзакций."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_account_id(test_client: AsyncClient, auth_headers: dict) -> str:
    resp = await test_client.get("/api/v1/reference/account-types")
    types_list = resp.json()
    atype_id = types_list[0]["id"] if types_list else "00000000-0000-0000-0000-000000000001"
    r = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": atype_id,
            "name": "Счёт для импорта",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    return r.json()["id"]


async def test_import_transactions(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    resp = await test_client.post(
        "/api/v1/transactions/import",
        json={
            "source": "bank_csv",
            "items": [
                {
                    "account_id": account_id,
                    "type": "expense",
                    "amount": "500.00",
                    "currency": "RUB",
                    "transaction_datetime": "2025-03-01T10:00:00Z",
                    "external_id": "ext-001",
                    "description": "Импортированная покупка",
                },
                {
                    "account_id": account_id,
                    "type": "income",
                    "amount": "20000.00",
                    "currency": "RUB",
                    "transaction_datetime": "2025-03-02T09:00:00Z",
                    "external_id": "ext-002",
                    "description": "Импортированный доход",
                },
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "created_count" in data
    assert "items" in data
    assert len(data["items"]) == 2


async def test_import_transactions_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/v1/transactions/import",
        json={
            "source": "test",
            "items": [
                {
                    "account_id": "00000000-0000-0000-0000-000000000001",
                    "type": "expense",
                    "amount": "100.00",
                    "currency": "RUB",
                    "transaction_datetime": "2025-01-01T00:00:00Z",
                    "external_id": "e1",
                }
            ],
        },
    )
    assert resp.status_code == 401
