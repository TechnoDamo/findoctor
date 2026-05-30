"""Схемы для обязательств (долгов и кредитов)."""

from pydantic import BaseModel, Field

from app.schemas.common import CurrencyCode, MoneyAmount


class LiabilityCreate(BaseModel):
    """Запрос на создание обязательства."""
    liability_type_id: str
    linked_account_id: str | None = None
    collateral_asset_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    creditor_institution_id: str | None = None
    creditor_name: str | None = None
    original_amount: MoneyAmount | None = None
    current_balance: MoneyAmount
    currency: CurrencyCode
    interest_rate: float | None = None
    interest_type: str | None = None
    minimum_payment_amount: MoneyAmount | None = None
    regular_payment_amount: MoneyAmount | None = None
    payment_due_day: int | None = Field(None, ge=1, le=31)
    start_date: str | None = None
    maturity_date: str | None = None


class LiabilityUpdate(BaseModel):
    """Запрос на обновление обязательства."""
    liability_type_id: str | None = None
    linked_account_id: str | None = None
    collateral_asset_id: str | None = None
    name: str | None = None
    creditor_institution_id: str | None = None
    creditor_name: str | None = None
    original_amount: MoneyAmount | None = None
    current_balance: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    interest_rate: float | None = None
    interest_type: str | None = None
    minimum_payment_amount: MoneyAmount | None = None
    regular_payment_amount: MoneyAmount | None = None
    payment_due_day: int | None = None
    start_date: str | None = None
    maturity_date: str | None = None
    status: str | None = None


class Liability(BaseModel):
    """Обязательство."""
    id: str
    user_id: str
    liability_type_id: str
    linked_account_id: str | None = None
    collateral_asset_id: str | None = None
    name: str
    creditor_institution_id: str | None = None
    creditor_name: str | None = None
    original_amount: str | None = None
    current_balance: str
    currency: str
    interest_rate: float | None = None
    interest_type: str | None = None
    minimum_payment_amount: str | None = None
    regular_payment_amount: str | None = None
    payment_due_day: int | None = None
    start_date: str | None = None
    maturity_date: str | None = None
    status: str
    created_at: str
    updated_at: str


class LiabilityList(BaseModel):
    """Список обязательств."""
    items: list[Liability]
