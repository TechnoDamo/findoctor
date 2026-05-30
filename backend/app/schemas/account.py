"""Схемы для счетов."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CurrencyCode, MoneyAmount


class AccountCreate(BaseModel):
    """Запрос на создание счёта."""
    account_type_id: UUID
    institution_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    institution_name: str | None = None
    currency: CurrencyCode
    opening_balance: MoneyAmount = "0"


class AccountUpdate(BaseModel):
    """Запрос на обновление счёта (все поля опциональны)."""
    account_type_id: UUID | None = None
    institution_id: UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    institution_name: str | None = None
    currency: CurrencyCode | None = None
    balance: MoneyAmount | None = None
    is_active: bool | None = None


class Account(BaseModel):
    """Счёт."""
    id: UUID
    user_id: UUID
    account_type_id: UUID
    institution_id: UUID | None = None
    name: str
    institution_name: str | None = None
    currency: str
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AccountList(BaseModel):
    """Список счетов."""
    items: list[Account]
