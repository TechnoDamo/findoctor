"""Тесты управления финансовыми целями."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_create_goal(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.post(
        "/api/v1/goals",
        json={"name": "Накопить на отпуск", "target_amount": "200000.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Накопить на отпуск"
    assert data["target_amount"] == "200000.00"
    assert data["current_amount"] == "0"
    assert "id" in data


async def test_list_goals(test_client: AsyncClient, auth_headers: dict) -> None:
    await test_client.post(
        "/api/v1/goals",
        json={"name": "Купить машину", "target_amount": "1000000.00", "priority": 1},
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/goals", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_get_goal(test_client: AsyncClient, auth_headers: dict) -> None:
    r = await test_client.post(
        "/api/v1/goals",
        json={"name": "Подушка безопасности", "target_amount": "300000.00"},
        headers=auth_headers,
    )
    goal_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Подушка безопасности"


async def test_update_goal(test_client: AsyncClient, auth_headers: dict) -> None:
    r = await test_client.post(
        "/api/v1/goals",
        json={"name": "Старая цель", "target_amount": "50000.00"},
        headers=auth_headers,
    )
    goal_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/goals/{goal_id}",
        json={"name": "Обновлённая цель", "current_amount": "10000.00", "priority": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Обновлённая цель"
    assert data["current_amount"] == "10000.00"


async def test_delete_goal(test_client: AsyncClient, auth_headers: dict) -> None:
    r = await test_client.post(
        "/api/v1/goals",
        json={"name": "Цель для удаления", "target_amount": "1000.00"},
        headers=auth_headers,
    )
    goal_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_goals_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/goals")
    assert resp.status_code == 401
