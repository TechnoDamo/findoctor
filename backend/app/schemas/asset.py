"""Схемы для активов."""

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
    id: str
    user_id: str
    asset_type_id: str
    name: str
    estimated_value: str
    currency: str
    purchase_price: str | None = None
    purchase_date: str | None = None
    monthly_cost: str | None = None
    created_at: str
    updated_at: str


class AssetList(BaseModel):
    """Список активов."""
    items: list[Asset]
