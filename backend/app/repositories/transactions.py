"""Репозиторий для финансовых транзакций."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("transactions.sql")


async def list_transactions(
    conn: AsyncConnection,
    user_id: str,
    page: int = 1,
    page_size: int = 50,
    **filters,
) -> tuple[list[dict], int]:
    """Список транзакций с пагинацией. Возвращает (items, total_count)."""
    params = {
        "user_id": user_id,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
        **filters,
    }
    rows = await conn.fetch(_queries["list_transactions"], params)
    total_row = await conn.fetchrow(_queries["count_transactions"], params)
    return list(rows), total_row["total"] if total_row else 0


async def find_transaction(conn: AsyncConnection, user_id: str, transaction_id: str) -> dict | None:
    """Получение транзакции по id с тегами."""
    return await conn.fetchrow(
        _queries["find_transaction"], {"user_id": user_id, "transaction_id": transaction_id}
    )


async def insert_transaction(conn: AsyncConnection, data: dict) -> dict:
    """Создание транзакции."""
    return await conn.fetchrow(_queries["insert_transaction"], data)


async def update_transaction(
    conn: AsyncConnection, user_id: str, transaction_id: str, data: dict
) -> dict | None:
    """Обновление транзакции."""
    params = {"user_id": user_id, "transaction_id": transaction_id, **data}
    return await conn.fetchrow(_queries["update_transaction"], params)


async def delete_transaction(conn: AsyncConnection, user_id: str, transaction_id: str) -> bool:
    """Удаление транзакции."""
    cursor = await conn.execute(
        _queries["delete_transaction"], {"user_id": user_id, "transaction_id": transaction_id}
    )
    return cursor.rowcount > 0
