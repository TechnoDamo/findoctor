"""Маршруты аутентификации: регистрация, логин, обновление токенов, выход."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbConnection
from app.schemas.auth import (
    AuthSession,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", response_model=AuthSession, status_code=201)
async def register_user(data: RegisterRequest, conn: DbConnection) -> dict:
    """Регистрация нового пользователя."""
    return await auth_service.register_user(
        conn=conn,
        email=data.email,
        password=data.password,
        base_currency=data.base_currency,
        timezone=data.timezone,
        phone=data.phone,
        first_name=data.first_name,
        last_name=data.last_name,
        country=data.country,
    )


@router.post("/login", response_model=AuthSession)
async def login_user(data: LoginRequest, conn: DbConnection) -> dict:
    """Вход в систему по email и паролю."""
    return await auth_service.login_user(conn=conn, email=data.email, password=data.password)


@router.post("/refresh", response_model=AuthSession)
async def refresh_session(data: RefreshRequest, conn: DbConnection) -> dict:
    """Обновление access- и refresh-токенов."""
    return await auth_service.refresh_session(conn=conn, refresh_token=data.refresh_token)


@router.post("/logout", status_code=204)
async def logout_user(conn: DbConnection, current_user: CurrentUser) -> None:
    """Выход из системы — отзыв текущей bearer-сессии."""
    await auth_service.logout_current_session(conn=conn, current_user=current_user)
