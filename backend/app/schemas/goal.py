"""Схемы для финансовых целей."""

from pydantic import BaseModel, Field

from app.schemas.common import MoneyAmount


class FinancialGoalCreate(BaseModel):
    """Запрос на создание финансовой цели."""
    name: str = Field(min_length=1, max_length=200)
    target_amount: MoneyAmount
    current_amount: MoneyAmount = "0"
    deadline: str | None = None
    priority: int | None = None


class FinancialGoalUpdate(BaseModel):
    """Запрос на обновление финансовой цели."""
    name: str | None = None
    target_amount: MoneyAmount | None = None
    current_amount: MoneyAmount | None = None
    deadline: str | None = None
    priority: int | None = None


class FinancialGoal(BaseModel):
    """Финансовая цель."""
    id: str
    user_id: str
    name: str
    target_amount: str
    current_amount: str
    deadline: str | None = None
    priority: int | None = None
    created_at: str
    updated_at: str


class FinancialGoalList(BaseModel):
    """Список целей."""
    items: list[FinancialGoal]
