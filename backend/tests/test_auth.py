"""Тесты аутентификации: регистрация, логин, обновление токенов, выход."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_register_user(test_client: AsyncClient, register_data: dict) -> None:
    """Регистрация нового пользователя должна вернуть 201 и токены."""
    resp = await test_client.post("/api/v1/auth/register", json=register_data)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == register_data["email"]


@pytest.mark.anyio
async def test_register_duplicate_returns_409(
    test_client: AsyncClient, register_data: dict
) -> None:
    """Повторная регистрация с тем же email должна вернуть 409."""
    await test_client.post("/api/v1/auth/register", json=register_data)
    resp = await test_client.post("/api/v1/auth/register", json=register_data)
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_login_user(test_client: AsyncClient, register_data: dict) -> None:
    """Вход с правильными учётными данными должен вернуть 200 и токены."""
    await test_client.post("/api/v1/auth/register", json=register_data)
    resp = await test_client.post("/api/v1/auth/login", json={
        "email": register_data["email"],
        "password": register_data["password"],
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data


@pytest.mark.anyio
async def test_login_wrong_password_returns_401(
    test_client: AsyncClient, register_data: dict
) -> None:
    """Вход с неверным паролем должен вернуть 401."""
    await test_client.post("/api/v1/auth/register", json=register_data)
    resp = await test_client.post("/api/v1/auth/login", json={
        "email": register_data["email"],
        "password": "wrong_password",
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_current_user(test_client: AsyncClient, auth_headers: dict) -> None:
    """Получение профиля текущего пользователя должно вернуть 200 и данные."""
    resp = await test_client.get("/api/v1/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"


@pytest.mark.anyio
async def test_get_current_user_without_token_returns_401(
    test_client: AsyncClient,
) -> None:
    """Запрос к /me без токена должен вернуть 401 (Unauthorized)."""
    resp = await test_client.get("/api/v1/me")
    assert resp.status_code == 401
