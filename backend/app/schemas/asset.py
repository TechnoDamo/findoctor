"""Схемы для активов."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CurrencyCode, MoneyAmount


class AssetCreate(BaseModel):
    """Запрос на создание актива."""
    asset_type_id: str
    name: str = Field(min_length=1, max_length=200)
    estimated_value: MoneyAmount
    currency: CurrencyCode
    purchase_price: MoneyAmount | None = None
    purchase_date: str | None = None
    monthly_cost: MoneyAmount | None = None


class AssetUpdate(BaseModel):
    """Запрос на обновление актива."""
    asset_type_id: str | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    estimated_value: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    purchase_price: MoneyAmount | None = None
    purchase_date: str | None = None
    monthly_cost: MoneyAmount | None = None


class Asset(BaseModel):
    """Актив."""
    id: UUID
    user_id: UUID
    asset_type_id: UUID
    name: str
    estimated_value: Decimal
    currency: str
    purchase_price: Decimal | None = None
    purchase_date: date | None = None
    monthly_cost: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class AssetList(BaseModel):
    """Список активов."""
    items: list[Asset]
