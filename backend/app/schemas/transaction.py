"""Схемы для транзакций."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CurrencyCode, MoneyAmount, PageMeta


class TagBrief(BaseModel):
    """Краткая информация о теге в составе транзакции."""
    id: UUID
    user_id: UUID
    name: str


class TransactionCreate(BaseModel):
    """Запрос на создание транзакции."""
    account_id: str
    category_id: str | None = None
    type: str = Field(description="income, expense или transfer")
    amount: MoneyAmount
    currency: CurrencyCode
    transaction_datetime: str = Field(description="ISO 8601 дата-время")
    description: str | None = None
    merchant_id: str | None = None
    merchant_name: str | None = None
    geo_location: str | None = None
    recurring_transaction_id: str | None = None
    external_id: str | None = None
    tag_ids: list[str] | None = None


class TransactionUpdate(BaseModel):
    """Запрос на обновление транзакции (все поля опциональны)."""
    account_id: str | None = None
    category_id: str | None = None
    type: str | None = None
    amount: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    transaction_datetime: str | None = None
    description: str | None = None
    merchant_id: str | None = None
    merchant_name: str | None = None
    geo_location: str | None = None
    recurring_transaction_id: str | None = None
    external_id: str | None = None


class Transaction(BaseModel):
    """Транзакция."""
    id: UUID
    user_id: UUID
    account_id: UUID
    category_id: UUID | None = None
    type: str
    amount: Decimal
    currency: str
    transaction_datetime: datetime
    description: str | None = None
    merchant_id: UUID | None = None
    merchant_name: str | None = None
    geo_location: str | None = None
    recurring_transaction_id: UUID | None = None
    external_id: str | None = None
    transfer_id: UUID | None = None
    transfer_leg: str | None = None
    created_at: datetime
    tags: list[TagBrief] = []


class TransactionPage(BaseModel):
    """Страница транзакций."""
    items: list[Transaction]
    meta: PageMeta
