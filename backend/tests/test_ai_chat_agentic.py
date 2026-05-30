"""Tests for agentic AI chat flow: planner, tools, finalizer pipeline."""

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.services import ai_chat as chat_service
from app.services.recommendations import orchestrator as orch

pytestmark = pytest.mark.anyio


class TestAgenticChatFlow:
    async def test_agentic_flow_sends_message(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Agentic message uses orchestrator instead of _run_llm."""

        async def fake_flow(**kwargs):
            return "Агентный ответ", {"prompt_tokens": 10, "completion_tokens": 5}, [
                {"type": "user_data", "name": "user_data", "result": {"domain": "accounts", "count": 3}},
            ]

        monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)

        response = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=auth_headers,
            json={
                "input": [{"type": "text", "text": "Какие у меня счета?"}],
                "agentic": True,
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["output"]["text"] == "Агентный ответ"
        assert data["usage"]["inputTokens"] == 10
        assert data["usage"]["outputTokens"] == 5
        assert len(data["toolResults"]) > 0
        assert data["toolResults"][0]["name"] == "user_data"

    async def test_non_agentic_flow_falls_back_to_direct_llm(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """agentic=false skips orchestrator and uses _run_llm directly."""

        async def fake_run_llm(user_text, financial_context=None, prompt_name="llm_text"):
            return "Прямой ответ", {"prompt_tokens": 1, "completion_tokens": 1}

        monkeypatch.setattr(chat_service, "_run_llm", fake_run_llm)

        response = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=auth_headers,
            json={
                "input": [{"type": "text", "text": "Привет"}],
                "agentic": False,
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["output"]["text"] == "Прямой ответ"
        assert data["toolResults"] == []

    async def test_agentic_default_is_true(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Omitting agentic field defaults to agentic=true."""

        called = False

        async def fake_flow(**kwargs):
            nonlocal called
            called = True
            return "Ответ", {"prompt_tokens": 1, "completion_tokens": 1}, []

        monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)

        response = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=auth_headers,
            json={
                "input": [{"type": "text", "text": "Привет"}],
            },
        )

        assert response.status_code == 200, response.text
        assert called

    async def test_tool_results_appear_in_response(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Tool results from the orchestrator are included in the API response."""

        tool_results = [
            {"type": "user_data", "name": "user_data", "result": {"domain": "transactions", "count": 12}},
            {"type": "user_data", "name": "user_data", "result": {"domain": "accounts", "count": 3}},
            {"type": "recommendation_plan", "plan": {}},
        ]

        async def fake_flow(**kwargs):
            return "Ответ с данными", {"prompt_tokens": 5, "completion_tokens": 3}, tool_results

        monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)

        response = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=auth_headers,
            json={
                "input": [{"type": "text", "text": "Сколько транзакций?"}],
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data["toolResults"]) == 3
        assert any(r["name"] == "user_data" for r in data["toolResults"])

    @pytest.mark.xfail(reason="ASGITransport protocol error with auth headers + multipart file upload")
    async def test_voice_message_uses_agentic_flow(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Voice messages now use agentic flow with llm_voice prompt."""

        agentic_called = False

        async def fake_flow(**kwargs):
            nonlocal agentic_called
            agentic_called = True
            return "Голосовой ответ", {"prompt_tokens": 2, "completion_tokens": 2}, []

        monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)

        response = await test_client.post(
            "/api/v1/ai/chat/audio",
            headers=auth_headers,
            files={"audio": ("test.wav", b"fake-audio-data", "audio/wav")},
        )

        assert response.status_code == 200, response.text
        assert agentic_called

    async def test_conversation_persistence_with_tool_results(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        db_connection: AsyncConnection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Messages and tool results are persisted across agentic turns."""

        async def fake_flow(**kwargs):
            return "Агентный ответ", {"prompt_tokens": 3, "completion_tokens": 2}, [
                {"type": "user_data", "name": "user_data", "result": {"domain": "dashboard_summary", "count": 1}},
            ]

        monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)

        resp = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=auth_headers,
            json={"input": [{"type": "text", "text": "Какое у меня состояние?"}]},
        )
        assert resp.status_code == 200, resp.text
        conv_id = resp.json()["conversationId"]

        async with db_connection.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) AS cnt FROM ai_chat_conversations WHERE id = %s",
                (conv_id,),
            )
            assert (await cur.fetchone())["cnt"] == 1

            await cur.execute(
                "SELECT role FROM ai_chat_messages WHERE conversation_id = %s ORDER BY created_at",
                (conv_id,),
            )
            rows = await cur.fetchall()
            assert [row["role"] for row in rows] == ["user", "assistant"]

    async def test_context_options_passed_to_orchestrator(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AiFinancialContextOptions are forwarded to run_recommendation_flow."""

        received_defaults = None

        async def fake_flow(**kwargs):
            nonlocal received_defaults
            received_defaults = kwargs.get("context_defaults")
            return "Ответ", {"prompt_tokens": 1, "completion_tokens": 1}, []

        monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)

        response = await test_client.post(
            "/api/v1/ai/chat/messages",
            headers=auth_headers,
            json={
                "input": [{"type": "text", "text": "Привет"}],
                "context": {
                    "baseCurrency": "USD",
                    "preferredDateFrom": "2025-01-01",
                    "preferredDateTo": "2025-06-30",
                },
            },
        )

        assert response.status_code == 200, response.text
        assert received_defaults is not None
        assert received_defaults.get("base_currency") == "USD"
