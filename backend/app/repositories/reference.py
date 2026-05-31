"""Репозиторий для справочных данных: типы, категории, продавцы."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("reference.sql")


async def list_account_types(conn: AsyncConnection) -> list[dict]:
    """Список всех типов счетов."""
    rows = await conn.fetch(_queries["list_account_types"])
    return list(rows)


async def list_asset_types(conn: AsyncConnection) -> list[dict]:
    """Список всех типов активов."""
    rows = await conn.fetch(_queries["list_asset_types"])
    return list(rows)


async def list_liability_types(conn: AsyncConnection) -> list[dict]:
    """Список всех типов обязательств."""
    rows = await conn.fetch(_queries["list_liability_types"])
    return list(rows)


async def list_provider_types(conn: AsyncConnection) -> list[dict]:
    """Список всех типов финансовых провайдеров."""
    rows = await conn.fetch(_queries["list_provider_types"])
    return list(rows)


async def list_categories(
    conn: AsyncConnection, type_: str | None = None, parent_id: str | None = None
) -> list[dict]:
    """Список категорий с фильтрацией по типу и родителю."""
    rows = await conn.fetch(
        _queries["list_categories"],
        {"type": type_, "parent_id": parent_id},
    )
    return list(rows)


async def find_category(conn: AsyncConnection, category_id: str) -> dict | None:
    """Поиск категории по id."""
    return await conn.fetchrow(_queries["find_category"], {"category_id": category_id})


async def insert_category(conn: AsyncConnection, data: dict) -> dict:
    """Создание категории."""
    return await conn.fetchrow(_queries["insert_category"], data)


async def update_category(conn: AsyncConnection, category_id: str, data: dict) -> dict:
    """Обновление категории."""
    params = {"category_id": category_id, **data}
    return await conn.fetchrow(_queries["update_category"], params)


async def delete_category(conn: AsyncConnection, category_id: str) -> None:
    """Удаление категории."""
    await conn.execute(_queries["delete_category"], {"category_id": category_id})


async def list_merchants(
    conn: AsyncConnection,
    q: str | None = None,
    country: str | None = None,
    risk_level: str | None = None,
) -> list[dict]:
    """Поиск продавцов."""
    rows = await conn.fetch(
        _queries["list_merchants"],
        {
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "country": country,
            "risk_level": risk_level,
        },
    )
    return list(rows)


async def find_merchant(conn: AsyncConnection, merchant_id: str) -> dict | None:
    """Поиск продавца по id."""
    return await conn.fetchrow(_queries["find_merchant"], {"merchant_id": merchant_id})


async def insert_merchant(conn: AsyncConnection, data: dict) -> dict:
    """Создание продавца."""
    return await conn.fetchrow(_queries["insert_merchant"], data)


async def update_merchant(conn: AsyncConnection, merchant_id: str, data: dict) -> dict:
    """Обновление продавца."""
    params = {"merchant_id": merchant_id, **data}
    return await conn.fetchrow(_queries["update_merchant"], params)


async def delete_merchant(conn: AsyncConnection, merchant_id: str) -> None:
    """Удаление продавца."""
    await conn.execute(_queries["delete_merchant"], {"merchant_id": merchant_id})
