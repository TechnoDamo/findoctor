"""Схемы продуктового endpoint рекомендаций."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ai_chat import AiToolResult, AiUsage, to_camel


class RecommendationBaseModel(BaseModel):
    """Base schema with lower camelCase public aliases."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RecommendationType(StrEnum):
    """Тип продуктового анализа."""

    income = "income"
    expenses = "expenses"
    savings_goal = "savings_goal"
    debt_traffic_light = "debt_traffic_light"
    credit_decision = "credit_decision"
    about_me = "about_me"


class CreditDecisionInput(RecommendationBaseModel):
    """Параметры конкретного кредита для анализа целесообразности."""

    amount: str = Field(description="Сумма кредита")
    term_months: int = Field(gt=0, description="Срок кредита в месяцах")
    monthly_payment: str = Field(description="Ежемесячный платеж")
    interest_rate: str = Field(description="Процентная ставка")
    purpose: str = Field(min_length=1, max_length=500, description="Цель кредита")
    income_stability: str = Field(
        min_length=1,
        max_length=500,
        description="Описание устойчивости дохода свободным текстом",
    )


class RecommendationRequest(RecommendationBaseModel):
    """Запрос продуктовой рекомендации."""

    credit: CreditDecisionInput | None = None
    question: str | None = Field(
        None,
        max_length=1000,
        description="Дополнительный вопрос или уточнение пользователя",
    )
    conversation_id: UUID | None = None


class RecommendationSection(RecommendationBaseModel):
    """Один раздел ответа."""

    title: str
    text: str


class RecommendationResponse(RecommendationBaseModel):
    """Продуктовый ответ рекомендации."""

    type: RecommendationType
    title: str
    analysis: str
    advice: str
    status: str | None = None
    facts: list[str] = Field(default_factory=list)
    credit_rating_impact: str | None = None
    free_cash_after_credit: str | None = None
    recommended_credit: str | None = None
    not_before_months: int | None = None
    sections: list[RecommendationSection] = Field(default_factory=list)
    output_text: str
    tool_results: list[AiToolResult] = Field(default_factory=list)
    usage: AiUsage | None = None
