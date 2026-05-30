"""Репозиторий для тегов и связей тег-транзакция."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("tags.sql")


async def list_tags(conn: AsyncConnection, user_id: str) -> list[dict]:
    """Список тегов пользователя."""
    rows = await conn.fetch(_queries["list_tags"], {"user_id": user_id})
    return list(rows)


async def find_tag(conn: AsyncConnection, tag_id: str) -> dict | None:
    """Поиск тега по id."""
    return await conn.fetchrow(_queries["find_tag"], {"tag_id": tag_id})


async def insert_tag(conn: AsyncConnection, user_id: str, name: str) -> dict:
    """Создание тега."""
    return await conn.fetchrow(
        _queries["insert_tag"], {"user_id": user_id, "name": name}
    )


async def update_tag(conn: AsyncConnection, tag_id: str, name: str) -> dict:
    """Обновление тега."""
    return await conn.fetchrow(_queries["update_tag"], {"tag_id": tag_id, "name": name})


async def delete_tag(conn: AsyncConnection, tag_id: str) -> None:
    """Удаление тега."""
    await conn.execute(_queries["delete_tag"], {"tag_id": tag_id})


async def list_transaction_tags(
    conn: AsyncConnection, transaction_id: str
) -> list[dict]:
    """Получение списка тегов транзакции."""
    rows = await conn.fetch(
        _queries["list_transaction_tags"], {"transaction_id": transaction_id}
    )
    return list(rows)


async def replace_transaction_tags(
    conn: AsyncConnection, transaction_id: str, tag_ids: list[str]
) -> list[dict]:
    """Полная замена тегов транзакции."""
    await conn.execute(
        _queries["delete_transaction_tags"], {"transaction_id": transaction_id}
    )
    for tag_id in tag_ids:
        await conn.execute(
            _queries["insert_transaction_tag"],
            {"transaction_id": transaction_id, "tag_id": tag_id},
        )
    return await list_transaction_tags(conn, transaction_id)


async def attach_tag(conn: AsyncConnection, transaction_id: str, tag_id: str) -> None:
    """Прикрепление тега к транзакции."""
    await conn.execute(
        _queries["insert_transaction_tag"],
        {"transaction_id": transaction_id, "tag_id": tag_id},
    )


async def detach_tag(conn: AsyncConnection, transaction_id: str, tag_id: str) -> None:
    """Открепление тега от транзакции."""
    await conn.execute(
        _queries["delete_transaction_tag"],
        {"transaction_id": transaction_id, "tag_id": tag_id},
    )
