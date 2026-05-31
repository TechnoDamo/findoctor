"""Recommendation planner, source policy, and chat integration tests."""

import pytest

from app.services.recommendations import orchestrator
from app.services.recommendations.schemas import RecommendationPlan
from app.services.recommendations.search import search_searxng
from app.services.recommendations.source_policy import (
    constrain_search_query,
    is_allowed_url,
    load_allowed_hosts,
)

pytestmark = pytest.mark.anyio


async def test_source_policy_loads_and_filters_allowed_hosts(tmp_path) -> None:
    allowed = tmp_path / "allowed.txt"
    allowed.write_text(
        """
        # comment
        https://www.cbr.ru/
        nalog.gov.ru
        """,
        encoding="utf-8",
    )

    hosts = load_allowed_hosts(str(allowed))

    assert hosts == {"cbr.ru", "nalog.gov.ru"}
    assert is_allowed_url("https://www.cbr.ru/press/keypr/", hosts)
    assert is_allowed_url("https://service.nalog.gov.ru/page", hosts)
    assert not is_allowed_url("https://example.com/page", hosts)


async def test_constrain_search_query_adds_allowed_sites() -> None:
    query = constrain_search_query("ключевая ставка", {"cbr.ru", "nalog.gov.ru"})

    assert "site:cbr.ru" in query
    assert "site:nalog.gov.ru" in query
    assert "ключевая ставка" in query
    assert constrain_search_query("site:cbr.ru ставка", {"nalog.gov.ru"}) == "site:cbr.ru ставка"


async def test_planner_json_normalizes_empty_tools() -> None:
    plan = RecommendationPlan.model_validate(
        {
            "response_text": "Можно ответить сразу.",
            "needed_tools": {
                "rag": {"rag_requests": []},
                "search": {"search_queries": ["   "]},
            },
        }
    ).normalized()

    assert plan.needed_tools is None


async def test_recommendation_prompts_include_context_and_safety_policy() -> None:
    planner_prompt = orchestrator._planner_system_prompt()
    finalizer_prompt = orchestrator._finalizer_system_prompt("llm_text", "test_context")

    assert "предоставленной схеме" in planner_prompt
    assert "Политика финансового контекста" in planner_prompt
    assert "Политика безопасности рекомендаций" in planner_prompt
    assert "Политика финансового контекста" in finalizer_prompt
    assert "Политика безопасности рекомендаций" in finalizer_prompt
    assert "Используй переданное evidence" in finalizer_prompt
    assert "test_context" in finalizer_prompt


async def test_search_searxng_filters_disallowed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "results": [
                    {
                        "title": "Allowed",
                        "url": "https://www.cbr.ru/press/",
                        "content": "Allowed snippet",
                        "score": 1.0,
                    },
                    {
                        "title": "Blocked",
                        "url": "https://example.com/",
                        "content": "Blocked snippet",
                    },
                ]
            }

    class FakeClient:
        async def get(self, *args, **kwargs) -> FakeResponse:
            assert kwargs["params"]["format"] == "json"
            return FakeResponse()

    monkeypatch.setattr(
        "app.services.recommendations.search.get_http_client", lambda: FakeClient()
    )

    results = await search_searxng(
        base_url="http://searxng",
        query="ставка",
        allowed_hosts={"cbr.ru"},
        timeout_seconds=1,
    )

    assert len(results) == 1
    assert results[0].title == "Allowed"
    assert results[0].url == "https://www.cbr.ru/press/"


async def test_ai_chat_uses_recommendation_flow_when_enabled(
    test_client,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import ai_chat as chat_service

    async def fake_run_llm(user_text: str, financial_context: dict | None = None, prompt_name: str = "llm_text") -> tuple[str, dict]:
        return "Готовая рекомендация", {"prompt_tokens": 10, "completion_tokens": 5}

    monkeypatch.setattr(chat_service, "_run_llm", fake_run_llm)

    response = await test_client.post(
        "/api/v1/ai/chat/messages",
        headers=auth_headers,
        json={"input": [{"type": "text", "text": "Дай рекомендацию"}], "agentic": False},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["output"]["text"] == "Готовая рекомендация"
    assert data["usage"]["inputTokens"] == 10
    assert data["usage"]["outputTokens"] == 5
