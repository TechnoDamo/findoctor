"""Тесты AI-чата: диалоги и аудио."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


class TestConversations:
    async def test_create_conversation(self, test_client: AsyncClient, auth_headers: dict) -> None:
        resp = await test_client.post(
            "/api/v1/ai/chat/conversations",
            json={"title": "Тестовый диалог"},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "Тестовый диалог"
        assert "id" in data
        assert "messages" in data

    async def test_list_conversations(self, test_client: AsyncClient, auth_headers: dict) -> None:
        await test_client.post(
            "/api/v1/ai/chat/conversations",
            json={"title": "Диалог 1"},
            headers=auth_headers,
        )
        resp = await test_client.get("/api/v1/ai/chat/conversations", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "meta" in data
        assert len(data["items"]) >= 1

    async def test_get_conversation(self, test_client: AsyncClient, auth_headers: dict) -> None:
        r = await test_client.post(
            "/api/v1/ai/chat/conversations",
            json={"title": "Диалог для получения"},
            headers=auth_headers,
        )
        conv_id = r.json()["id"]
        resp = await test_client.get(f"/api/v1/ai/chat/conversations/{conv_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Диалог для получения"

    async def test_delete_conversation(self, test_client: AsyncClient, auth_headers: dict) -> None:
        r = await test_client.post(
            "/api/v1/ai/chat/conversations",
            json={"title": "Удаляемый диалог"},
            headers=auth_headers,
        )
        conv_id = r.json()["id"]
        resp = await test_client.delete(f"/api/v1/ai/chat/conversations/{conv_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_list_conversations_unauthorized(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/ai/chat/conversations")
        assert resp.status_code == 401


class TestAudioEndpoint:
    async def test_audio_endpoint_returns_422_without_file(self, test_client: AsyncClient, auth_headers: dict) -> None:
        resp = await test_client.post("/api/v1/ai/chat/audio", headers=auth_headers)
        assert resp.status_code == 422

    async def test_audio_endpoint_unauthorized(self, test_client: AsyncClient) -> None:
        resp = await test_client.post("/api/v1/ai/chat/audio")
        assert resp.status_code in {401, 422}
