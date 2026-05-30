"""Репозиторий для счетов пользователя."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("accounts.sql")


async def list_accounts(
    conn: AsyncConnection,
    user_id: str,
    is_active: bool | None = None,
    account_type_id: str | None = None,
    institution_id: str | None = None,
    currency: str | None = None,
) -> list[dict]:
    """Список счетов с фильтрацией."""
    rows = await conn.fetch(
        _queries["list_accounts"],
        {
            "user_id": user_id,
            "is_active": is_active,
            "account_type_id": account_type_id,
            "institution_id": institution_id,
            "currency": currency,
        },
    )
    return list(rows)


async def find_account(conn: AsyncConnection, account_id: str) -> dict | None:
    """Получение счёта по id."""
    return await conn.fetchrow(_queries["find_account"], {"account_id": account_id})


async def insert_account(conn: AsyncConnection, data: dict) -> dict:
    """Создание счёта."""
    data.setdefault("opening_balance", "0")
    return await conn.fetchrow(_queries["insert_account"], data)


async def update_account(conn: AsyncConnection, account_id: str, data: dict) -> dict:
    """Обновление счёта."""
    params = {"account_id": account_id, **data}
    return await conn.fetchrow(_queries["update_account"], params)


async def archive_account(conn: AsyncConnection, account_id: str) -> dict:
    """Архивация счёта."""
    return await conn.fetchrow(_queries["archive_account"], {"account_id": account_id})
