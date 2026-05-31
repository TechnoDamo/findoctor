"""Репозиторий для платежей по обязательствам."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("liability_payments.sql")


async def list_liability_payments(
    conn: AsyncConnection, user_id: str, **filters
) -> list[dict]:
    """Список платежей с фильтрацией."""
    rows = await conn.fetch(
        _queries["list_liability_payments"],
        {"user_id": user_id, **filters},
    )
    return list(rows)


async def find_liability_payment(
    conn: AsyncConnection, user_id: str, liability_payment_id: str
) -> dict | None:
    """Получение платежа по id."""
    return await conn.fetchrow(
        _queries["find_liability_payment"],
        {"user_id": user_id, "liability_payment_id": liability_payment_id},
    )


async def insert_liability_payment(conn: AsyncConnection, data: dict) -> dict:
    """Создание платежа."""
    return await conn.fetchrow(_queries["insert_liability_payment"], data)


async def update_liability_payment(
    conn: AsyncConnection, user_id: str, liability_payment_id: str, data: dict
) -> dict | None:
    """Обновление платежа."""
    return await conn.fetchrow(
        _queries["update_liability_payment"],
        {"user_id": user_id, "liability_payment_id": liability_payment_id, **data},
    )


async def delete_liability_payment(
    conn: AsyncConnection, user_id: str, liability_payment_id: str
) -> bool:
    """Удаление платежа."""
    cursor = await conn.execute(
        _queries["delete_liability_payment"],
        {"user_id": user_id, "liability_payment_id": liability_payment_id},
    )
    return cursor.rowcount > 0
