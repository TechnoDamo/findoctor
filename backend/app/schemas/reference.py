"""Схемы для справочных данных: типы, категории, продавцы."""

from uuid import UUID

from pydantic import BaseModel, Field


class ReferenceCode(BaseModel):
    """Базовый справочник: id, code, name, description."""
    id: UUID
    code: str
    name: str
    description: str | None = None


class AccountType(ReferenceCode):
    """Тип счёта."""
    pass


class AssetType(ReferenceCode):
    """Тип актива."""
    pass


class LiabilityType(ReferenceCode):
    """Тип обязательства."""
    is_secured: bool = False


class ProviderType(ReferenceCode):
    """Тип финансового провайдера."""
    pass


class CategoryBase(BaseModel):
    """Базовые поля категории."""
    parent_id: str | None = None
    type: str = Field(description="Тип: income или expense")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class CategoryCreate(CategoryBase):
    """Запрос на создание категории."""
    pass


class CategoryUpdate(BaseModel):
    """Запрос на обновление категории (все поля опциональны)."""
    parent_id: str | None = None
    type: str | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class Category(CategoryBase):
    """Категория с id и вложенными подкатегориями."""
    id: str
    children: list["Category"] = []


class CategoryList(BaseModel):
    """Список категорий."""
    items: list[Category]


class MerchantBase(BaseModel):
    """Базовые поля продавца."""
    name: str = Field(min_length=1, max_length=200)
    category: str | None = None
    country: str | None = Field(None, min_length=2, max_length=2)
    risk_level: str | None = "unknown"


class MerchantCreate(MerchantBase):
    """Запрос на создание продавца."""
    pass


class MerchantUpdate(BaseModel):
    """Запрос на обновление продавца."""
    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = None
    country: str | None = None
    risk_level: str | None = None


class Merchant(MerchantBase):
    """Продавец."""
    id: str


class MerchantList(BaseModel):
    """Список продавцов."""
    items: list[Merchant]
