"""Схемы для аутентификации: регистрация, логин, сессия."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import CurrencyCode


class RegisterRequest(BaseModel):
    """Запрос на регистрацию пользователя."""
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    country: str | None = None
    base_currency: CurrencyCode
    timezone: str = Field(examples=["Europe/Moscow"])


class LoginRequest(BaseModel):
    """Запрос на вход в систему."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Запрос на обновление токенов."""
    refresh_token: str


class UserProfile(BaseModel):
    """Профиль пользователя (в составе AuthSession)."""
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


class AuthSession(BaseModel):
    """Ответ с токенами и профилем пользователя."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserProfile
