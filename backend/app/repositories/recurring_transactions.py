"""Репозиторий для регулярных операций."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("recurring_transactions.sql")


async def list_recurring_transactions(
    conn: AsyncConnection, user_id: str, **filters
) -> list[dict]:
    """Список регулярных операций с фильтрацией."""
    rows = await conn.fetch(
        _queries["list_recurring_transactions"],
        {"user_id": user_id, **filters},
    )
    return list(rows)


async def find_recurring_transaction(
    conn: AsyncConnection, recurring_transaction_id: str
) -> dict | None:
    """Получение регулярной операции по id."""
    return await conn.fetchrow(
        _queries["find_recurring_transaction"],
        {"recurring_transaction_id": recurring_transaction_id},
    )


async def insert_recurring_transaction(
    conn: AsyncConnection, data: dict
) -> dict:
    """Создание регулярной операции."""
    return await conn.fetchrow(
        _queries["insert_recurring_transaction"], data
    )


async def update_recurring_transaction(
    conn: AsyncConnection, recurring_transaction_id: str, data: dict
) -> dict:
    """Обновление регулярной операции."""
    return await conn.fetchrow(
        _queries["update_recurring_transaction"],
        {"recurring_transaction_id": recurring_transaction_id, **data},
    )


async def deactivate_recurring_transaction(
    conn: AsyncConnection, recurring_transaction_id: str
) -> None:
    """Деактивация регулярной операции."""
    await conn.execute(
        _queries["deactivate_recurring_transaction"],
        {"recurring_transaction_id": recurring_transaction_id},
    )
