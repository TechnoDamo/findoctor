"""Тесты управления тегами."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_create_tag(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.post(
        "/api/v1/tags",
        json={"name": "Важное"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Важное"
    assert "id" in data


async def test_list_tags(test_client: AsyncClient, auth_headers: dict) -> None:
    await test_client.post(
        "/api/v1/tags",
        json={"name": "Работа"},
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/tags", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_tag(test_client: AsyncClient, auth_headers: dict) -> None:
    r = await test_client.post(
        "/api/v1/tags",
        json={"name": "Дом"},
        headers=auth_headers,
    )
    tag_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Дом"


async def test_update_tag(test_client: AsyncClient, auth_headers: dict) -> None:
    r = await test_client.post(
        "/api/v1/tags",
        json={"name": "Старый тег"},
        headers=auth_headers,
    )
    tag_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Обновлённый тег"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Обновлённый тег"


async def test_delete_tag(test_client: AsyncClient, auth_headers: dict) -> None:
    r = await test_client.post(
        "/api/v1/tags",
        json={"name": "Удаляемый"},
        headers=auth_headers,
    )
    tag_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_tags_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/tags")
    assert resp.status_code == 401
