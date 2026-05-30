"""Репозиторий для активов пользователя."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("assets.sql")


async def list_assets(
    conn: AsyncConnection, user_id: str, asset_type_id: str | None = None
) -> list[dict]:
    """Список активов с фильтрацией по типу."""
    rows = await conn.fetch(
        _queries["list_assets"],
        {"user_id": user_id, "asset_type_id": asset_type_id},
    )
    return list(rows)


async def find_asset(conn: AsyncConnection, asset_id: str) -> dict | None:
    """Получение актива по id."""
    return await conn.fetchrow(_queries["find_asset"], {"asset_id": asset_id})


async def insert_asset(conn: AsyncConnection, data: dict) -> dict:
    """Создание актива."""
    return await conn.fetchrow(_queries["insert_asset"], data)


async def update_asset(conn: AsyncConnection, asset_id: str, data: dict) -> dict:
    """Обновление актива."""
    return await conn.fetchrow(
        _queries["update_asset"], {"asset_id": asset_id, **data}
    )


async def delete_asset(conn: AsyncConnection, asset_id: str) -> None:
    """Удаление актива."""
    await conn.execute(_queries["delete_asset"], {"asset_id": asset_id})
