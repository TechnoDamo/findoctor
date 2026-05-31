"""Tests for the product recommendations endpoint."""

import pytest
from httpx import AsyncClient

from app.schemas.recommendation import RecommendationType
from app.services.recommendations import orchestrator as orch

pytestmark = pytest.mark.anyio


AI_TEXT = """Статус: Зеленый
Аналитика: Доходы стабильные, долговая нагрузка умеренная.
Совет: Сохраняйте резерв и направляйте часть свободных средств на цель.
Факты:
- Доходы покрывают регулярные расходы.
- Резерв не выглядит критически низким.
Влияние на кредитный рейтинг: При аккуратных платежах влияние нейтральное или умеренно положительное.
Свободные средства после кредита: Останется ориентировочно безопасный запас.
Рекомендуемый кредит: Рассматривать только платеж, который не ломает резерв.
Срок до нового кредита: 0 месяцев"""


async def _fake_flow(**kwargs):
    return AI_TEXT, {"prompt_tokens": 11, "completion_tokens": 7}, [
        {"type": "recommendation_plan", "plan": {"needed_tools": "user_data"}},
        {"type": "user_data", "name": "user_data", "result": {"domain": "dashboard_summary"}},
    ]


@pytest.mark.parametrize(
    "recommendation_type",
    [
        RecommendationType.income,
        RecommendationType.expenses,
        RecommendationType.debt_traffic_light,
        RecommendationType.about_me,
    ],
)
async def test_recommendation_endpoint_uses_ai_pipeline_for_active_types(
    test_client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
    recommendation_type: RecommendationType,
) -> None:
    received = {}

    async def fake_flow(**kwargs):
        received.update(kwargs)
        return await _fake_flow(**kwargs)

    monkeypatch.setattr(orch, "run_recommendation_flow", fake_flow)
    monkeypatch.setattr(
        "app.services.product_recommendations.run_recommendation_flow",
        fake_flow,
    )

    response = await test_client.post(
        f"/api/v1/recommendations?type={recommendation_type.value}",
        headers=auth_headers,
        json={"question": "Сделай анализ"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["type"] == recommendation_type.value
    assert data["analysis"].startswith("Доходы стабильные")
    assert data["advice"].startswith("Сохраняйте резерв")
    assert data["usage"]["inputTokens"] == 11
    assert len(data["toolResults"]) == 2
    assert received["prompt_name"] == "recommendation_endpoint"
    assert recommendation_type.value in received["financial_context"]
    assert received["context_defaults"]["recommendation_type"] == recommendation_type.value


async def test_credit_decision_requires_credit_body(
    test_client: AsyncClient,
    auth_headers: dict,
) -> None:
    response = await test_client.post(
        "/api/v1/recommendations?type=credit_decision",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 422
    assert "credit" in response.text


async def test_credit_decision_returns_credit_fields(
    test_client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received = {}

    async def fake_flow(**kwargs):
        received.update(kwargs)
        return await _fake_flow(**kwargs)

    monkeypatch.setattr(
        "app.services.product_recommendations.run_recommendation_flow",
        fake_flow,
    )

    response = await test_client.post(
        "/api/v1/recommendations?type=credit_decision",
        headers=auth_headers,
        json={
            "credit": {
                "amount": "500000",
                "termMonths": 24,
                "monthlyPayment": "26000",
                "interestRate": "18.5",
                "purpose": "ремонт",
                "incomeStability": "доход стабильный последние 12 месяцев",
            }
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "Зеленый"
    assert data["creditRatingImpact"].startswith("При аккуратных платежах")
    assert data["freeCashAfterCredit"].startswith("Останется")
    assert data["recommendedCredit"].startswith("Рассматривать")
    assert data["notBeforeMonths"] == 0
    assert "500000" in received["financial_context"]
    assert received["context_defaults"]["credit"]["purpose"] == "ремонт"


async def test_savings_goal_is_temporarily_disabled(
    test_client: AsyncClient,
    auth_headers: dict,
) -> None:
    response = await test_client.post(
        "/api/v1/recommendations?type=savings_goal",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 422
    assert "savings_goal" in response.text
