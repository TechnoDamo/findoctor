"""Product recommendation endpoint service."""

from __future__ import annotations

import re
from typing import Any

from psycopg import AsyncConnection

from app.schemas.ai_chat import AiUsage
from app.schemas.recommendation import (
    CreditDecisionInput,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationSection,
    RecommendationType,
)
from app.services.recommendations.orchestrator import run_recommendation_flow


TITLES = {
    RecommendationType.income: "Рекомендации по доходам",
    RecommendationType.expenses: "Рекомендации по расходам",
    RecommendationType.savings_goal: "Копилка",
    RecommendationType.debt_traffic_light: "Кредитный светофор",
    RecommendationType.credit_decision: "Расчет целесообразности кредита",
    RecommendationType.about_me: "Обо мне",
}


async def build_recommendation(
    *,
    conn: AsyncConnection,
    user: dict,
    recommendation_type: RecommendationType,
    request: RecommendationRequest,
) -> RecommendationResponse:
    """Run the AI recommendation pipeline and normalize a product response."""
    user_text = _build_user_text(recommendation_type, request)
    context_defaults = _context_defaults(user, recommendation_type, request)

    output_text, usage, tool_results = await run_recommendation_flow(
        conn=conn,
        user_id=user["id"],
        user_text=user_text,
        financial_context=_financial_context(user, recommendation_type, request),
        prompt_name="recommendation_endpoint",
        conversation_id=str(request.conversation_id) if request.conversation_id else None,
        context_defaults=context_defaults,
    )
    parsed = _parse_output(output_text)

    return RecommendationResponse(
        type=recommendation_type,
        title=TITLES[recommendation_type],
        analysis=parsed.get("analysis") or output_text,
        advice=parsed.get("advice") or output_text,
        status=parsed.get("status"),
        facts=parsed.get("facts", []),
        credit_rating_impact=parsed.get("credit_rating_impact"),
        free_cash_after_credit=parsed.get("free_cash_after_credit"),
        recommended_credit=parsed.get("recommended_credit"),
        not_before_months=_parse_months(parsed.get("not_before_months")),
        sections=_sections(parsed),
        output_text=output_text,
        tool_results=[
            {"name": r.get("name", r.get("type", "unknown")), "result": r.get("result", r)}
            for r in tool_results
        ],
        usage=AiUsage(
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        ),
    )


def _build_user_text(
    recommendation_type: RecommendationType,
    request: RecommendationRequest,
) -> str:
    base = {
        RecommendationType.income: (
            "Сделай продуктовый анализ доходов пользователя. "
            "Сначала дай аналитику текущих доходов, затем советы по улучшению."
        ),
        RecommendationType.expenses: (
            "Сделай продуктовый анализ расходов пользователя. "
            "Сначала дай аналитику текущих расходов, затем советы по снижению и оптимизации."
        ),
        RecommendationType.savings_goal: (
            "Пользователь запросил блок Копилка. Сейчас endpoint не активирует этот блок: "
            "объясни, что нужна выбранная финансовая цель."
        ),
        RecommendationType.debt_traffic_light: (
            "Сделай кредитный светофор: проанализируй долговую ситуацию, историю платежей, "
            "долговую нагрузку и скажи, можно ли брать кредиты сейчас."
        ),
        RecommendationType.credit_decision: (
            "Оцени целесообразность конкретного кредита по переданным параметрам. "
            "Дай статус, факты, влияние на кредитный рейтинг, свободные средства после кредита "
            "и рекомендацию, какой кредит можно брать или почему пока нельзя."
        ),
        RecommendationType.about_me: (
            "Сделай общий финансовый портрет пользователя: аналитика текущей ситуации и отчет, "
            "как улучшить финансовое положение."
        ),
    }[recommendation_type]
    parts = [base]
    if request.credit:
        parts.append("Параметры кредита:\n" + _credit_text(request.credit))
    if request.question:
        parts.append("Дополнительный вопрос пользователя:\n" + request.question)
    return "\n\n".join(parts)


def _credit_text(credit: CreditDecisionInput) -> str:
    return "\n".join(
        [
            f"- сумма: {credit.amount}",
            f"- срок в месяцах: {credit.term_months}",
            f"- ежемесячный платеж: {credit.monthly_payment}",
            f"- процентная ставка: {credit.interest_rate}",
            f"- цель: {credit.purpose}",
            f"- устойчивость дохода: {credit.income_stability}",
        ]
    )


def _financial_context(
    user: dict,
    recommendation_type: RecommendationType,
    request: RecommendationRequest,
) -> str:
    payload: dict[str, Any] = {
        "endpoint": "product_recommendations",
        "recommendation_type": recommendation_type.value,
        "user": {
            "id": str(user["id"]),
            "base_currency": user.get("base_currency"),
            "timezone": user.get("timezone"),
        },
        "response_language": "ru",
        "expected_sections": [
            "Статус",
            "Аналитика",
            "Совет",
            "Факты",
            "Влияние на кредитный рейтинг",
            "Свободные средства после кредита",
            "Рекомендуемый кредит",
            "Срок до нового кредита",
        ],
    }
    if request.credit:
        payload["credit"] = request.credit.model_dump(mode="json")
    return str(payload)


def _context_defaults(
    user: dict,
    recommendation_type: RecommendationType,
    request: RecommendationRequest,
) -> dict:
    defaults = {
        "base_currency": user.get("base_currency"),
        "recommendation_type": recommendation_type.value,
    }
    if request.credit:
        defaults["credit"] = request.credit.model_dump(mode="json")
    return defaults


def _parse_output(text: str) -> dict[str, Any]:
    keys = {
        "Статус": "status",
        "Аналитика": "analysis",
        "Совет": "advice",
        "Факты": "facts",
        "Влияние на кредитный рейтинг": "credit_rating_impact",
        "Свободные средства после кредита": "free_cash_after_credit",
        "Рекомендуемый кредит": "recommended_credit",
        "Срок до нового кредита": "not_before_months",
    }
    pattern = re.compile(
        r"^(Статус|Аналитика|Совет|Факты|Влияние на кредитный рейтинг|"
        r"Свободные средства после кредита|Рекомендуемый кредит|Срок до нового кредита):\s*",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    parsed: dict[str, Any] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        key = keys[match.group(1)]
        value = text[start:end].strip()
        if key == "facts":
            parsed[key] = [
                line.strip().lstrip("-").strip()
                for line in value.splitlines()
                if line.strip().lstrip("-").strip()
            ]
        else:
            parsed[key] = value
    return parsed


def _parse_months(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def _sections(parsed: dict[str, Any]) -> list[RecommendationSection]:
    titles = [
        ("status", "Статус"),
        ("analysis", "Аналитика"),
        ("advice", "Совет"),
        ("credit_rating_impact", "Влияние на кредитный рейтинг"),
        ("free_cash_after_credit", "Свободные средства после кредита"),
        ("recommended_credit", "Рекомендуемый кредит"),
        ("not_before_months", "Срок до нового кредита"),
    ]
    return [
        RecommendationSection(title=title, text=str(parsed[key]))
        for key, title in titles
        if parsed.get(key)
    ]
