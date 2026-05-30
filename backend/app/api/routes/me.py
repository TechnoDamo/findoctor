"""Маршруты профиля текущего пользователя."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbConnection
from app.repositories import users as user_repo
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


def _serialize_user(user: dict) -> dict:
    return {
        **user,
        "id": str(user["id"]),
        "created_at": user["created_at"].isoformat(),
        "updated_at": user["updated_at"].isoformat(),
    }


@router.get("", response_model=UserResponse)
async def get_current_user(user: CurrentUser) -> dict:
    """Получение профиля текущего пользователя."""
    return _serialize_user(user)


@router.patch("", response_model=UserResponse)
async def update_current_user(data: UserUpdate, user: CurrentUser, conn: DbConnection) -> dict:
    """Обновление профиля текущего пользователя."""
    updated = await user_repo.update_user(
        conn,
        user["id"],
        data.model_dump(exclude_none=True),
    )
    return _serialize_user(updated)
