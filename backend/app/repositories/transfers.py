"""Репозиторий для переводов между счетами."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("transfers.sql")


async def list_transfers(
    conn: AsyncConnection,
    user_id: str,
    page: int = 1,
    page_size: int = 50,
    **filters,
) -> tuple[list[dict], int]:
    """Список переводов с пагинацией."""
    params = {
        "user_id": user_id,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
        **filters,
    }
    rows = await conn.fetch(_queries["list_transfers"], params)
    total_row = await conn.fetchrow(_queries["count_transfers"], params)
    return list(rows), total_row["total"] if total_row else 0


async def find_transfer(conn: AsyncConnection, user_id: str, transfer_id: str) -> dict | None:
    """Получение перевода с полными данными связанных транзакций."""
    return await conn.fetchrow(
        _queries["find_transfer"], {"user_id": user_id, "transfer_id": transfer_id}
    )


async def insert_transfer(conn: AsyncConnection, data: dict) -> dict:
    """Создание перевода (без транзакций — они создаются в сервисе)."""
    return await conn.fetchrow(_queries["insert_transfer"], data)


async def update_transfer(
    conn: AsyncConnection, user_id: str, transfer_id: str, data: dict
) -> dict | None:
    """Обновление перевода."""
    params = {"user_id": user_id, "transfer_id": transfer_id, **data}
    return await conn.fetchrow(_queries["update_transfer"], params)


async def delete_transfer(conn: AsyncConnection, user_id: str, transfer_id: str) -> bool:
    """Удаление перевода."""
    cursor = await conn.execute(
        _queries["delete_transfer"], {"user_id": user_id, "transfer_id": transfer_id}
    )
    return cursor.rowcount > 0


async def find_transfer_linked_transactions(
    conn: AsyncConnection, user_id: str, transfer_id: str
) -> list[dict]:
    """Получение связанных транзакций."""
    rows = await conn.fetch(
        _queries["find_transfer_linked_transactions"],
        {"user_id": user_id, "transfer_id": transfer_id},
    )
    return list(rows)


async def delete_transfer_transactions(
    conn: AsyncConnection, user_id: str, transfer_id: str
) -> None:
    """Удаление связанных транзакций."""
    await conn.execute(
        _queries["delete_transfer_transactions"], {"user_id": user_id, "transfer_id": transfer_id}
    )
