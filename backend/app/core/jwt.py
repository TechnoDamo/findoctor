"""
Создание и проверка JWT-токенов.

Использует python-jose (реализация JOSE для Python).
Access-токен — короткоживущий, содержит user_id.
Refresh-токен — долгоживущий, содержит уникальный идентификатор сессии.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.settings import settings


def create_access_token(user_id: str, session_id: str) -> str:
    """Создаёт access-токен для аутентификации API-запросов."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(session_id: str) -> str:
    """Создаёт refresh-токен для обновления сессии."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(session_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=settings.refresh_token_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """
    Декодирует access-токен и возвращает payload.

    Возвращает None, если токен истёк, невалиден или имеет неверный тип.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def decode_refresh_token(token: str) -> dict | None:
    """
    Декодирует refresh-токен и возвращает payload.

    Возвращает None, если токен истёк, невалиден или имеет неверный тип.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None

    if payload.get("type") != "refresh":
        return None

    return payload
