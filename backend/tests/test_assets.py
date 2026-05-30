"""Тесты управления активами."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_asset_type_id(test_client: AsyncClient) -> str:
    resp = await test_client.get("/api/v1/reference/asset-types")
    types_list = resp.json()
    if types_list:
        return types_list[0]["id"]
    return "00000000-0000-0000-0000-000000000001"


async def test_create_asset(test_client: AsyncClient, auth_headers: dict) -> None:
    asset_type_id = await _get_asset_type_id(test_client)
    resp = await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": asset_type_id,
            "name": "Квартира",
            "estimated_value": "5000000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Квартира"
    assert data["estimated_value"] == "5000000.00"


async def test_list_assets(test_client: AsyncClient, auth_headers: dict) -> None:
    asset_type_id = await _get_asset_type_id(test_client)
    await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": asset_type_id,
            "name": "Машина",
            "estimated_value": "1500000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/assets", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_asset(test_client: AsyncClient, auth_headers: dict) -> None:
    asset_type_id = await _get_asset_type_id(test_client)
    r = await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": asset_type_id,
            "name": "Гараж",
            "estimated_value": "500000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    asset_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Гараж"


async def test_update_asset(test_client: AsyncClient, auth_headers: dict) -> None:
    asset_type_id = await _get_asset_type_id(test_client)
    r = await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": asset_type_id,
            "name": "Старый актив",
            "estimated_value": "100000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    asset_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/assets/{asset_id}",
        json={"name": "Обновлённый актив", "estimated_value": "200000.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Обновлённый актив"
    assert data["estimated_value"] == "200000.00"


async def test_delete_asset(test_client: AsyncClient, auth_headers: dict) -> None:
    asset_type_id = await _get_asset_type_id(test_client)
    r = await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": asset_type_id,
            "name": "Для удаления",
            "estimated_value": "1000.00",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    asset_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_assets_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/assets")
    assert resp.status_code == 401
