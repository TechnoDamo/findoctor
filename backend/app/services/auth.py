"""
Сервис аутентификации: регистрация, логин, обновление токенов, выход.

Управляет полным жизненным циклом сессии:
  - При регистрации/логине: хеширует пароль, создаёт пользователя/сессию, выпускает токены.
  - При обновлении: проверяет refresh-токен в БД, выпускает новую пару.
  - При выходе: удаляет сессию из БД.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from psycopg import AsyncConnection

from app.core.errors import ConflictError, UnauthorizedError
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.security import hash_password, verify_password
from app.repositories import auth as auth_repo


def _hash_token(token: str) -> str:
    """Хеширует refresh-токен для хранения в БД (SHA-256)."""
    return hashlib.sha256(token.encode()).hexdigest()


async def _issue_session_tokens(conn: AsyncConnection, user: dict) -> dict:
    """Создаёт сессию, выпускает пару токенов и возвращает AuthSession."""
    from app.settings import settings

    session = await auth_repo.insert_session(
        conn,
        {
            "user_id": user["id"],
            "refresh_token_hash": "",
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=settings.refresh_token_ttl_seconds),
        },
    )

    access_token = create_access_token(user["id"], session["id"])
    refresh_token = create_refresh_token(session["id"])
    token_hash = _hash_token(refresh_token)

    await conn.execute(
        "UPDATE auth_sessions SET refresh_token_hash = %(hash)s WHERE id = %(id)s",
        {"hash": token_hash, "id": session["id"]},
    )

    return _build_auth_response(user, access_token, refresh_token)


async def register_user(
    conn: AsyncConnection,
    email: str,
    password: str,
    base_currency: str,
    timezone: str,
    phone: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    country: str | None = None,
) -> dict:
    """
    Регистрация нового пользователя.

    Создаёт запись в users, сессию в auth_sessions и возвращает профиль + токены.

    Raises:
        ConflictError: если email уже занят.
    """
    existing = await auth_repo.find_user_by_email(conn, email)
    if existing is not None:
        raise ConflictError("Пользователь с таким email уже существует")

    password_hash_value = hash_password(password)
    user = await auth_repo.insert_user(
        conn,
        {
            "email": email,
            "password_hash": password_hash_value,
            "phone": phone,
            "first_name": first_name,
            "last_name": last_name,
            "country": country,
            "base_currency": base_currency,
            "timezone": timezone,
        },
    )

    return await _issue_session_tokens(conn, user)


async def login_user(conn: AsyncConnection, email: str, password: str) -> dict:
    """
    Вход в систему по email и паролю.

    Проверяет учётные данные, создаёт новую сессию и возвращает токены.

    Raises:
        UnauthorizedError: если email или пароль неверны.
    """
    user = await auth_repo.find_user_by_email(conn, email)
    if user is None or not verify_password(password, user["password_hash"]):
        raise UnauthorizedError("Неверный email или пароль")

    return await _issue_session_tokens(conn, user)


async def refresh_session(conn: AsyncConnection, refresh_token: str) -> dict:
    """
    Обновление сессии по refresh-токену.

    Удаляет старую сессию, создаёт новую, выпускает новую пару токенов.

    Raises:
        UnauthorizedError: если токен невалиден или сессия истекла/отозвана.
    """
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise UnauthorizedError("Токен истёк или недействителен")

    token_hash = _hash_token(refresh_token)
    session = await auth_repo.find_session_by_hash(conn, token_hash)
    if session is None:
        raise UnauthorizedError("Сессия не найдена или отозвана")

    await auth_repo.delete_session(conn, token_hash)

    user = await auth_repo.find_user_by_id(conn, session["user_id"])
    if user is None:
        raise UnauthorizedError("Пользователь не найден")

    return await _issue_session_tokens(conn, user)


async def logout_user(conn: AsyncConnection, refresh_token: str) -> None:
    """
    Выход из системы — удаление сессии.

    Не выбрасывает ошибку, если токен уже невалиден (idempotent).
    """
    token_hash = _hash_token(refresh_token)
    await auth_repo.delete_session(conn, token_hash)


async def logout_current_session(conn: AsyncConnection, current_user: dict) -> None:
    """Выход из текущей bearer-сессии."""
    session_id = current_user.get("_session_id")
    if session_id is not None:
        await auth_repo.delete_session_by_id(conn, session_id)


def _build_auth_response(user: dict, access_token: str, refresh_token: str) -> dict:
    """Формирует объект ответа по контракту AuthSession."""
    from app.settings import settings

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.access_token_ttl_seconds,
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "phone": user.get("phone"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "country": user.get("country"),
            "base_currency": user["base_currency"],
            "timezone": user["timezone"],
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "updated_at": user["updated_at"].isoformat() if user.get("updated_at") else None,
        },
    }
