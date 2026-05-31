"""Репозиторий для профиля пользователя."""

from psycopg import AsyncConnection

from app.db.operations import fetchrow
from app.db.query_loader import load_queries

_queries = load_queries("users.sql")


async def find_user_by_id(conn: AsyncConnection, user_id: str) -> dict | None:
    """Получение профиля пользователя по id."""
    return await fetchrow(conn, _queries["find_user_by_id"], {"user_id": user_id})


async def update_user(conn: AsyncConnection, user_id: str, data: dict) -> dict | None:
    """Обновление профиля пользователя."""
    params = {"user_id": user_id, **data}
    return await fetchrow(conn, _queries["update_user"], params)
