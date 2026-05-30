"""Тесты управления регулярными операциями."""

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
            "name": "Счёт для рег.операций",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    return r.json()["id"]


async def test_create_recurring_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    resp = await test_client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": account_id,
            "operation_type": "expense",
            "name": "Аренда квартиры",
            "expected_amount": "35000.00",
            "currency": "RUB",
            "frequency": "monthly",
            "day_of_month": 1,
            "start_date": "2025-01-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Аренда квартиры"
    assert data["operation_type"] == "expense"
    assert data["frequency"] == "monthly"
    assert data["is_active"] is True


async def test_list_recurring_transactions(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    await test_client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": account_id,
            "operation_type": "income",
            "name": "Зарплата",
            "expected_amount": "100000.00",
            "currency": "RUB",
            "frequency": "monthly",
            "day_of_month": 15,
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/recurring-transactions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_recurring_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": account_id,
            "operation_type": "expense",
            "name": "Интернет",
            "expected_amount": "500.00",
            "currency": "RUB",
            "frequency": "monthly",
            "day_of_month": 10,
        },
        headers=auth_headers,
    )
    rt_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/recurring-transactions/{rt_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Интернет"


async def test_update_recurring_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": account_id,
            "operation_type": "expense",
            "name": "Старое имя",
            "expected_amount": "300.00",
            "currency": "RUB",
            "frequency": "weekly",
        },
        headers=auth_headers,
    )
    rt_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/recurring-transactions/{rt_id}",
        json={"name": "Новое имя", "expected_amount": "500.00", "frequency": "monthly"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Новое имя"
    assert data["expected_amount"] == "500.00"
    assert data["frequency"] == "monthly"


async def test_delete_recurring_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/recurring-transactions",
        json={
            "account_id": account_id,
            "operation_type": "expense",
            "name": "Для удаления",
            "expected_amount": "100.00",
            "currency": "RUB",
            "frequency": "monthly",
        },
        headers=auth_headers,
    )
    rt_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/recurring-transactions/{rt_id}", headers=auth_headers)
    assert resp.status_code == 204

    r2 = await test_client.get(f"/api/v1/recurring-transactions/{rt_id}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["is_active"] is False


async def test_list_recurring_transactions_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/recurring-transactions")
    assert resp.status_code == 401
