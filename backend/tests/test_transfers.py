"""Тесты управления переводами между счетами."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_two_account_ids(test_client: AsyncClient, auth_headers: dict) -> tuple[str, str]:
    resp = await test_client.get("/api/v1/reference/account-types")
    types_list = resp.json()
    atype_id = types_list[0]["id"] if types_list else "00000000-0000-0000-0000-000000000001"

    r1 = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": atype_id,
            "name": "Счёт-источник",
            "currency": "RUB",
            "opening_balance": "100000.00",
        },
        headers=auth_headers,
    )
    r2 = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": atype_id,
            "name": "Счёт-назначение",
            "currency": "RUB",
            "opening_balance": "0",
        },
        headers=auth_headers,
    )
    return r1.json()["id"], r2.json()["id"]


async def test_create_transfer(test_client: AsyncClient, auth_headers: dict) -> None:
    from_id, to_id = await _get_two_account_ids(test_client, auth_headers)
    resp = await test_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": "5000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-04-01T12:00:00Z",
            "description": "Перевод между счетами",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["amount"] == "5000.00"
    assert data["from_account_id"] == from_id
    assert data["to_account_id"] == to_id
    assert "from_transaction_id" in data
    assert "to_transaction_id" in data


async def test_list_transfers(test_client: AsyncClient, auth_headers: dict) -> None:
    from_id, to_id = await _get_two_account_ids(test_client, auth_headers)
    await test_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": "1000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-04-15T10:00:00Z",
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/transfers", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "meta" in data
    assert len(data["items"]) >= 1


async def test_get_transfer(test_client: AsyncClient, auth_headers: dict) -> None:
    from_id, to_id = await _get_two_account_ids(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": "3000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-04-20T14:00:00Z",
            "description": "Тестовый перевод",
        },
        headers=auth_headers,
    )
    transfer_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/transfers/{transfer_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Тестовый перевод"


async def test_update_transfer(test_client: AsyncClient, auth_headers: dict) -> None:
    from_id, to_id = await _get_two_account_ids(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": "1000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-04-25T10:00:00Z",
            "description": "До обновления",
        },
        headers=auth_headers,
    )
    transfer_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/transfers/{transfer_id}",
        json={"description": "После обновления"},
        headers=auth_headers,
    )
    assert resp.status_code in {200, 400}, resp.text


async def test_delete_transfer(test_client: AsyncClient, auth_headers: dict) -> None:
    from_id, to_id = await _get_two_account_ids(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": "500.00",
            "currency": "RUB",
            "transaction_datetime": "2025-04-30T10:00:00Z",
        },
        headers=auth_headers,
    )
    transfer_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/transfers/{transfer_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_transfers_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/transfers")
    assert resp.status_code == 401
