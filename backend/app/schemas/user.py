"""Схемы для профиля текущего пользователя."""

from pydantic import BaseModel

from app.schemas.common import CurrencyCode


class UserResponse(BaseModel):
    """Полный профиль пользователя."""
    id: str
    email: str
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    country: str | None = None
    base_currency: str
    timezone: str
    created_at: str
    updated_at: str


class UserUpdate(BaseModel):
    """Поля для обновления профиля (все опциональны)."""
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    country: str | None = None
    base_currency: CurrencyCode | None = None
    timezone: str | None = None
