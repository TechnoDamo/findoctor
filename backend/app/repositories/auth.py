"""Репозиторий для аутентификации — пользователи и сессии."""

from psycopg import AsyncConnection

from app.db.operations import fetchrow
from app.db.query_loader import load_queries

_queries = load_queries("auth.sql")


async def find_user_by_email(conn: AsyncConnection, email: str) -> dict | None:
    """Поиск пользователя по email (включая password_hash)."""
    return await fetchrow(conn, _queries["find_user_by_email"], {"email": email})


async def find_user_by_id(conn: AsyncConnection, user_id: str) -> dict | None:
    """Поиск пользователя по id (без password_hash)."""
    return await fetchrow(conn, _queries["find_user_by_id"], {"user_id": user_id})


async def insert_user(conn: AsyncConnection, data: dict) -> dict:
    """Создание нового пользователя."""
    return await fetchrow(conn, _queries["insert_user"], data)


async def insert_session(conn: AsyncConnection, data: dict) -> dict:
    """Создание сессии (сохраняет хеш refresh-токена)."""
    return await fetchrow(conn, _queries["insert_session"], data)


async def find_session_by_hash(
    conn: AsyncConnection, token_hash: str
) -> dict | None:
    """Поиск активной (не истёкшей) сессии по хешу refresh-токена."""
    return await fetchrow(
        conn,
        _queries["find_session_by_hash"], {"token_hash": token_hash}
    )


async def find_session_by_id(conn: AsyncConnection, session_id: str) -> dict | None:
    """Поиск активной (не истёкшей) сессии по id."""
    return await fetchrow(conn, _queries["find_session_by_id"], {"session_id": session_id})


async def delete_session(conn: AsyncConnection, token_hash: str) -> None:
    """Удаление сессии (logout)."""
    await conn.execute(_queries["delete_session"], {"token_hash": token_hash})


async def delete_session_by_id(conn: AsyncConnection, session_id: str) -> None:
    """Удаление сессии по id (logout текущей сессии)."""
    await conn.execute(_queries["delete_session_by_id"], {"session_id": session_id})


async def delete_user_sessions(conn: AsyncConnection, user_id: str) -> None:
    """Удаление всех сессий пользователя."""
    await conn.execute(_queries["delete_user_sessions"], {"user_id": user_id})
