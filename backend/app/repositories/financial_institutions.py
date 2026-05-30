"""Репозиторий для финансовых организаций."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("financial_institutions.sql")


async def list_institutions(
    conn: AsyncConnection,
    q: str | None = None,
    country: str | None = None,
    provider_type_code: str | None = None,
    active_only: bool = True,
) -> list[dict]:
    """Поиск финансовых организаций."""
    rows = await conn.fetch(
        _queries["list_institutions"],
        {
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "country": country,
            "provider_type_code": provider_type_code,
            "active_only": active_only,
        },
    )
    return list(rows)


async def find_institution(conn: AsyncConnection, institution_id: str) -> dict | None:
    """Получение организации по id."""
    return await conn.fetchrow(
        _queries["find_institution"], {"institution_id": institution_id}
    )


async def insert_institution(conn: AsyncConnection, data: dict) -> dict:
    """Создание организации."""
    return await conn.fetchrow(_queries["insert_institution"], data)


async def insert_institution_provider_types(
    conn: AsyncConnection, institution_id: str, provider_type_ids: list[str]
) -> None:
    """Привязка типов провайдеров к организации."""
    for pt_id in provider_type_ids:
        await conn.execute(
            _queries["insert_institution_provider_types"],
            {"institution_id": institution_id, "provider_type_id": pt_id},
        )


async def update_institution(
    conn: AsyncConnection, institution_id: str, data: dict
) -> dict:
    """Обновление организации."""
    params = {"institution_id": institution_id, **data}
    return await conn.fetchrow(_queries["update_institution"], params)


async def replace_institution_provider_types(
    conn: AsyncConnection, institution_id: str, provider_type_ids: list[str]
) -> None:
    """Замена всех типов провайдеров организации."""
    await conn.execute(
        _queries["delete_institution_provider_types"],
        {"institution_id": institution_id},
    )
    for pt_id in provider_type_ids:
        await conn.execute(
            _queries["insert_institution_provider_types"],
            {"institution_id": institution_id, "provider_type_id": pt_id},
        )
