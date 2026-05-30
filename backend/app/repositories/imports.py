"""Репозиторий для идемпотентного импорта транзакций."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("imports.sql")


async def upsert_transaction(conn: AsyncConnection, data: dict) -> str | None:
    """Вставка транзакции через upsert. Возвращает id созданной транзакции или None если дубликат."""
    row = await conn.fetchrow(_queries["upsert_transaction"], data)
    if row is None:
        return None
    return row["id"]


async def check_external_id_exists(
    conn: AsyncConnection, account_id: str, external_id: str
) -> str | None:
    """Проверка существования транзакции по external_id."""
    row = await conn.fetchrow(
        _queries["check_external_id_exists"],
        {"account_id": account_id, "external_id": external_id},
    )
    return row["id"] if row else None
