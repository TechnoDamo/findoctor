"""Тесты управления финансовыми организациями."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_provider_type_id(test_client: AsyncClient) -> str:
    resp = await test_client.get("/api/v1/reference/provider-types")
    types_list = resp.json()
    if types_list:
        return types_list[0]["id"]
    return "00000000-0000-0000-0000-000000000001"


async def test_create_institution(test_client: AsyncClient) -> None:
    provider_id = await _get_provider_type_id(test_client)
    resp = await test_client.post(
        "/api/v1/financial-institutions",
        json={
            "name": "Сбербанк",
            "country": "RU",
            "provider_type_ids": [provider_id] if provider_id != "00000000-0000-0000-0000-000000000001" else [],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Сбербанк"
    assert "id" in data


async def test_list_institutions(test_client: AsyncClient) -> None:
    provider_id = await _get_provider_type_id(test_client)
    await test_client.post(
        "/api/v1/financial-institutions",
        json={
            "name": "ВТБ",
            "country": "RU",
            "provider_type_ids": [provider_id] if provider_id != "00000000-0000-0000-0000-000000000001" else [],
        },
    )
    resp = await test_client.get("/api/v1/financial-institutions")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_institution(test_client: AsyncClient) -> None:
    r = await test_client.post(
        "/api/v1/financial-institutions",
        json={"name": "Тинькофф", "country": "RU"},
    )
    inst_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/financial-institutions/{inst_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Тинькофф"


async def test_update_institution(test_client: AsyncClient) -> None:
    r = await test_client.post(
        "/api/v1/financial-institutions",
        json={"name": "Старое имя", "country": "RU"},
    )
    inst_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/financial-institutions/{inst_id}",
        json={"name": "Новое имя банка"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Новое имя банка"


async def test_get_institution_not_found(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/financial-institutions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
