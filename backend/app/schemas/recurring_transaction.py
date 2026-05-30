"""Схемы для регулярных операций."""

from pydantic import BaseModel, Field

from app.schemas.common import CurrencyCode, MoneyAmount


class RecurringTransactionCreate(BaseModel):
    """Запрос на создание регулярной операции."""
    account_id: str
    category_id: str | None = None
    liability_id: str | None = None
    operation_type: str = Field(description="income, expense, transfer или liability_payment")
    name: str = Field(min_length=1, max_length=200)
    expected_amount: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    frequency: str = Field(description="daily, weekly, monthly или yearly")
    interval_count: int = Field(1, ge=1)
    day_of_month: int | None = Field(None, ge=1, le=31)
    start_date: str | None = None
    end_date: str | None = None
    next_payment_date: str | None = None


class RecurringTransactionUpdate(BaseModel):
    """Запрос на обновление регулярной операции."""
    account_id: str | None = None
    category_id: str | None = None
    liability_id: str | None = None
    operation_type: str | None = None
    name: str | None = None
    expected_amount: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    frequency: str | None = None
    interval_count: int | None = None
    day_of_month: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    next_payment_date: str | None = None
    is_active: bool | None = None


class RecurringTransaction(BaseModel):
    """Регулярная операция."""
    id: str
    user_id: str
    account_id: str
    category_id: str | None = None
    liability_id: str | None = None
    operation_type: str
    name: str
    expected_amount: str | None = None
    currency: str | None = None
    frequency: str
    interval_count: int
    day_of_month: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    next_payment_date: str | None = None
    auto_generated: bool = False
    confidence_score: float | None = None
    is_active: bool = True


class RecurringTransactionList(BaseModel):
    """Список регулярных операций."""
    items: list[RecurringTransaction]
