"""Тесты управления платежами по обязательствам."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_liability_and_account(test_client: AsyncClient, auth_headers: dict) -> tuple[str, str]:
    rt = await test_client.get("/api/v1/reference/liability-types")
    ltypes = rt.json()
    ltype_id = ltypes[0]["id"] if ltypes else "00000000-0000-0000-0000-000000000001"

    r = await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": ltype_id,
            "name": "Кредит для платежа",
            "current_balance": "100000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    liab_id = r.json()["id"]

    at = await test_client.get("/api/v1/reference/account-types")
    atypes = at.json()
    atype_id = atypes[0]["id"] if atypes else "00000000-0000-0000-0000-000000000001"

    a = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": atype_id,
            "name": "Счёт для платежа",
            "currency": "RUB",
            "opening_balance": "100000.00",
        },
        headers=auth_headers,
    )
    return liab_id, a.json()["id"]


async def test_create_liability_payment(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_id, account_id = await _get_liability_and_account(test_client, auth_headers)
    resp = await test_client.post(
        "/api/v1/liability-payments",
        json={
            "liability_id": liability_id,
            "account_id": account_id,
            "payment_date": "2025-05-15",
            "total_amount": "5000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["total_amount"] == "5000.00"
    assert data["liability_id"] == liability_id
    assert "transaction_id" in data


async def test_list_liability_payments(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_id, account_id = await _get_liability_and_account(test_client, auth_headers)
    await test_client.post(
        "/api/v1/liability-payments",
        json={
            "liability_id": liability_id,
            "account_id": account_id,
            "payment_date": "2025-05-01",
            "total_amount": "3000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/liability-payments", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_liability_payment(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_id, account_id = await _get_liability_and_account(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/liability-payments",
        json={
            "liability_id": liability_id,
            "account_id": account_id,
            "payment_date": "2025-05-10",
            "total_amount": "7000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    payment_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/liability-payments/{payment_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total_amount"] == "7000.00"


async def test_update_liability_payment(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_id, account_id = await _get_liability_and_account(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/liability-payments",
        json={
            "liability_id": liability_id,
            "account_id": account_id,
            "payment_date": "2025-05-20",
            "total_amount": "2000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    payment_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/liability-payments/{payment_id}",
        json={"total_amount": "2500.00", "principal_amount": "2000.00", "interest_amount": "500.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_amount"] == "2500.00"


async def test_delete_liability_payment(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_id, account_id = await _get_liability_and_account(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/liability-payments",
        json={
            "liability_id": liability_id,
            "account_id": account_id,
            "payment_date": "2025-05-25",
            "total_amount": "1000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    payment_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/liability-payments/{payment_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_liability_payments_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/liability-payments")
    assert resp.status_code == 401
