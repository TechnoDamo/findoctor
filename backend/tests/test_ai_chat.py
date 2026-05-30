"""AI chat endpoint tests."""

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.services import ai_chat as chat_service

pytestmark = pytest.mark.anyio


async def test_send_text_message_uses_contract_camel_case(
    test_client: AsyncClient,
    db_connection: AsyncConnection,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A frontend-shaped text chat request creates persisted messages."""

    async def fake_run_llm(user_text: str, financial_context: dict | None = None) -> tuple[str, dict]:
        assert user_text == "Привет"
        return "Чат работает", {"prompt_tokens": 3, "completion_tokens": 2}

    monkeypatch.setattr(chat_service, "_run_llm", fake_run_llm)

    response = await test_client.post(
        "/api/v1/ai/chat/messages",
        headers=auth_headers,
        json={
            "input": [{"type": "text", "text": "Привет"}],
            "responseModalities": ["text"],
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["conversationId"]
    assert data["userMessageId"]
    assert data["assistantMessageId"]
    assert data["requestText"] == "Привет"
    assert data["output"]["text"] == "Чат работает"
    assert data["usage"]["inputTokens"] == 3
    assert data["usage"]["outputTokens"] == 2

    async with db_connection.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) AS count FROM ai_chat_conversations WHERE id = %s",
            (data["conversationId"],),
        )
        assert (await cur.fetchone())["count"] == 1

        await cur.execute(
            "SELECT role, content FROM ai_chat_messages WHERE conversation_id = %s ORDER BY created_at",
            (data["conversationId"],),
        )
        rows = await cur.fetchall()

    assert [row["role"] for row in rows] == ["user", "assistant"]
    assert rows[0]["content"][0]["text"] == "Привет"
    assert rows[1]["content"][0]["text"] == "Чат работает"


async def test_send_text_message_continues_existing_camel_case_conversation(
    test_client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """conversationId from the frontend is respected instead of creating a new chat."""

    async def fake_run_llm(user_text: str, financial_context: dict | None = None) -> tuple[str, dict]:
        return f"Ответ на: {user_text}", {}

    monkeypatch.setattr(chat_service, "_run_llm", fake_run_llm)

    first = await test_client.post(
        "/api/v1/ai/chat/messages",
        headers=auth_headers,
        json={"input": [{"type": "text", "text": "Первое"}]},
    )
    assert first.status_code == 200, first.text
    conversation_id = first.json()["conversationId"]

    second = await test_client.post(
        "/api/v1/ai/chat/messages",
        headers=auth_headers,
        json={
            "conversationId": conversation_id,
            "input": [{"type": "text", "text": "Второе"}],
        },
    )

    assert second.status_code == 200, second.text
    assert second.json()["conversationId"] == conversation_id
