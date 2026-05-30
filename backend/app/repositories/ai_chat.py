"""Репозиторий для AI-чата: диалоги и сообщения."""

import json

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("ai_chat.sql")


async def list_conversations(
    conn: AsyncConnection, user_id: str, page: int = 1, page_size: int = 50
) -> tuple[list[dict], int]:
    """Список диалогов с пагинацией."""
    params = {
        "user_id": user_id,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
    }
    rows = await conn.fetch(_queries["list_conversations"], params)
    total_row = await conn.fetchrow(_queries["count_conversations"], {"user_id": user_id})
    return list(rows), total_row["total"] if total_row else 0


async def find_conversation(
    conn: AsyncConnection, conversation_id: str
) -> dict | None:
    """Получение диалога по id."""
    conversation = await conn.fetchrow(
        _queries["find_conversation"], {"conversation_id": conversation_id}
    )
    if conversation is None:
        return None
    messages = await conn.fetch(
        _queries["list_messages"], {"conversation_id": conversation_id}
    )
    conversation["messages"] = list(messages)
    return conversation


async def insert_conversation(conn: AsyncConnection, user_id: str, title: str | None = None) -> dict:
    """Создание нового диалога."""
    return await conn.fetchrow(
        _queries["insert_conversation"], {"user_id": user_id, "title": title}
    )


async def update_conversation(
    conn: AsyncConnection, conversation_id: str, title: str
) -> dict:
    """Обновление заголовка диалога."""
    return await conn.fetchrow(
        _queries["update_conversation"],
        {"conversation_id": conversation_id, "title": title},
    )


async def delete_conversation(conn: AsyncConnection, conversation_id: str) -> None:
    """Удаление диалога (каскадно удаляет сообщения)."""
    await conn.execute(
        _queries["delete_conversation"], {"conversation_id": conversation_id}
    )


async def list_messages(
    conn: AsyncConnection, conversation_id: str
) -> list[dict]:
    """Список сообщений диалога."""
    rows = await conn.fetch(
        _queries["list_messages"], {"conversation_id": conversation_id}
    )
    return list(rows)


async def insert_message(
    conn: AsyncConnection,
    conversation_id: str,
    role: str,
    content: list[dict],
    metadata: dict | None = None,
) -> dict:
    """Добавление сообщения в диалог."""
    params = {
        "conversation_id": conversation_id,
        "role": role,
        "content": json.dumps(content, ensure_ascii=False),
        "metadata": json.dumps(metadata, ensure_ascii=False) if metadata else None,
    }
    message = await conn.fetchrow(_queries["insert_message"], params)
    await conn.execute(
        _queries["touch_conversation"], {"conversation_id": conversation_id}
    )
    return message
