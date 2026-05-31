"""Репозиторий для финансовых целей."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("goals.sql")


async def list_goals(conn: AsyncConnection, user_id: str) -> list[dict]:
    """Список финансовых целей пользователя."""
    rows = await conn.fetch(_queries["list_goals"], {"user_id": user_id})
    return list(rows)


async def find_goal(conn: AsyncConnection, user_id: str, goal_id: str) -> dict | None:
    """Получение цели по id."""
    return await conn.fetchrow(_queries["find_goal"], {"user_id": user_id, "goal_id": goal_id})


async def insert_goal(conn: AsyncConnection, data: dict) -> dict:
    """Создание цели."""
    return await conn.fetchrow(_queries["insert_goal"], data)


async def update_goal(conn: AsyncConnection, user_id: str, goal_id: str, data: dict) -> dict | None:
    """Обновление цели."""
    return await conn.fetchrow(
        _queries["update_goal"], {"user_id": user_id, "goal_id": goal_id, **data}
    )


async def delete_goal(conn: AsyncConnection, user_id: str, goal_id: str) -> bool:
    """Удаление цели."""
    cursor = await conn.execute(_queries["delete_goal"], {"user_id": user_id, "goal_id": goal_id})
    return cursor.rowcount > 0
