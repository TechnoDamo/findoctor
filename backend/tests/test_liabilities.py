"""Тесты управления обязательствами."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_liability_type_id(test_client: AsyncClient) -> str:
    resp = await test_client.get("/api/v1/reference/liability-types")
    types_list = resp.json()
    if types_list:
        return types_list[0]["id"]
    return "00000000-0000-0000-0000-000000000001"


async def test_create_liability(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_type_id = await _get_liability_type_id(test_client)
    resp = await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": liability_type_id,
            "name": "Ипотека",
            "current_balance": "5000000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Ипотека"
    assert data["current_balance"] == "5000000.00"
    assert data["status"] == "active"


async def test_list_liabilities(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_type_id = await _get_liability_type_id(test_client)
    await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": liability_type_id,
            "name": "Кредитная карта",
            "current_balance": "50000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/liabilities", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_liability(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_type_id = await _get_liability_type_id(test_client)
    r = await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": liability_type_id,
            "name": "Автокредит",
            "current_balance": "800000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    liab_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/liabilities/{liab_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Автокредит"


async def test_update_liability(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_type_id = await _get_liability_type_id(test_client)
    r = await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": liability_type_id,
            "name": "Старый долг",
            "current_balance": "100000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    liab_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/liabilities/{liab_id}",
        json={"name": "Обновлённый долг", "current_balance": "80000.00", "interest_rate": 15.5},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Обновлённый долг"
    assert data["current_balance"] == "80000.00"


async def test_delete_liability(test_client: AsyncClient, auth_headers: dict) -> None:
    liability_type_id = await _get_liability_type_id(test_client)
    r = await test_client.post(
        "/api/v1/liabilities",
        json={
            "liability_type_id": liability_type_id,
            "name": "Для закрытия",
            "current_balance": "1000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    liab_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/liabilities/{liab_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_liabilities_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/liabilities")
    assert resp.status_code == 401
