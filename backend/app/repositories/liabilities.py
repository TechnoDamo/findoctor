"""Репозиторий для обязательств (долгов и кредитов)."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("liabilities.sql")


async def list_liabilities(
    conn: AsyncConnection,
    user_id: str,
    status: str | None = None,
    liability_type_id: str | None = None,
) -> list[dict]:
    """Список обязательств с фильтрацией."""
    rows = await conn.fetch(
        _queries["list_liabilities"],
        {
            "user_id": user_id,
            "status": status,
            "liability_type_id": liability_type_id,
        },
    )
    return list(rows)


async def find_liability(conn: AsyncConnection, liability_id: str) -> dict | None:
    """Получение обязательства по id."""
    return await conn.fetchrow(
        _queries["find_liability"], {"liability_id": liability_id}
    )


async def insert_liability(conn: AsyncConnection, data: dict) -> dict:
    """Создание обязательства."""
    return await conn.fetchrow(_queries["insert_liability"], data)


async def update_liability(
    conn: AsyncConnection, liability_id: str, data: dict
) -> dict:
    """Обновление обязательства."""
    return await conn.fetchrow(
        _queries["update_liability"], {"liability_id": liability_id, **data}
    )


async def close_liability(conn: AsyncConnection, liability_id: str) -> dict:
    """Закрытие обязательства."""
    return await conn.fetchrow(
        _queries["close_liability"], {"liability_id": liability_id}
    )
