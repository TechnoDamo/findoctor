"""Схемы для платежей по обязательствам."""

from pydantic import BaseModel, Field

from app.schemas.common import CurrencyCode, MoneyAmount


class LiabilityPaymentCreate(BaseModel):
    """Запрос на создание платежа по обязательству."""
    liability_id: str
    account_id: str = Field(description="Счёт для создания транзакции, если transaction_id не указан")
    transaction_id: str | None = None
    recurring_transaction_id: str | None = None
    payment_date: str
    total_amount: MoneyAmount
    principal_amount: MoneyAmount | None = None
    interest_amount: MoneyAmount | None = None
    fee_amount: MoneyAmount | None = None
    currency: CurrencyCode
    balance_after_payment: MoneyAmount | None = None


class LiabilityPaymentUpdate(BaseModel):
    """Запрос на обновление платежа."""
    recurring_transaction_id: str | None = None
    payment_date: str | None = None
    total_amount: MoneyAmount | None = None
    principal_amount: MoneyAmount | None = None
    interest_amount: MoneyAmount | None = None
    fee_amount: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    balance_after_payment: MoneyAmount | None = None


class LiabilityPayment(BaseModel):
    """Платёж по обязательству."""
    id: str
    user_id: str
    liability_id: str
    transaction_id: str
    recurring_transaction_id: str | None = None
    payment_date: str
    total_amount: str
    principal_amount: str | None = None
    interest_amount: str | None = None
    fee_amount: str | None = None
    currency: str
    balance_after_payment: str | None = None
    created_at: str


class LiabilityPaymentList(BaseModel):
    """Список платежей."""
    items: list[LiabilityPayment]
