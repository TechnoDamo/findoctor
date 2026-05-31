"""Тесты профиля текущего пользователя."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_update_user_profile(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.patch(
        "/api/v1/me",
        json={"first_name": "Иван", "last_name": "Петров", "country": "RU"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["first_name"] == "Иван"
    assert data["last_name"] == "Петров"
    assert data["country"] == "RU"


async def test_update_user_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.patch(
        "/api/v1/me",
        json={"first_name": "NoAuth"},
    )
    assert resp.status_code == 401
