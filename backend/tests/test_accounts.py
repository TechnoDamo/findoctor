"""Тесты для управления счетами."""

import pytest
from httpx import AsyncClient


async def _get_account_type_id(test_client: AsyncClient) -> str:
    """Получает ID реального типа счёта из справочника."""
    resp = await test_client.get("/api/v1/reference/account-types")
    types_list = resp.json()
    if types_list:
        return types_list[0]["id"]
    return "00000000-0000-0000-0000-000000000001"


@pytest.mark.anyio
async def test_create_account(
    test_client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Создание счёта должно вернуть 201."""
    account_type_id = await _get_account_type_id(test_client)
    resp = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": account_type_id,
            "name": "Основной счёт",
            "currency": "RUB",
            "opening_balance": "10000.00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Основной счёт"
    assert data["currency"] == "RUB"


@pytest.mark.anyio
async def test_list_accounts(
    test_client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Список счетов должен вернуть созданный счёт."""
    account_type_id = await _get_account_type_id(test_client)
    await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": account_type_id,
            "name": "Счёт",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/accounts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_list_accounts_unauthorized(test_client: AsyncClient) -> None:
    """Список счетов без токена должен вернуть 401."""
    resp = await test_client.get("/api/v1/accounts")
    assert resp.status_code == 401
