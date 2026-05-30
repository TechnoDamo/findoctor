"""Схемы для платежей по обязательствам."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

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
    id: UUID
    user_id: UUID
    liability_id: UUID
    transaction_id: UUID
    recurring_transaction_id: UUID | None = None
    payment_date: date
    total_amount: Decimal
    principal_amount: Decimal | None = None
    interest_amount: Decimal | None = None
    fee_amount: Decimal | None = None
    currency: str
    balance_after_payment: Decimal | None = None
    created_at: datetime


class LiabilityPaymentList(BaseModel):
    """Список платежей."""
    items: list[LiabilityPayment]
