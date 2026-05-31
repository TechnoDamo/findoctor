"""Маршруты для управления тегами и привязкой тегов к транзакциям."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import tags as tag_repo
from app.schemas.tag import Tag, TagCreate, TagList, TagUpdate

router = APIRouter()


@router.get("", response_model=TagList)
async def list_tags(user: CurrentUser, conn: DbConnection) -> dict:
    """Список тегов пользователя."""
    items = await tag_repo.list_tags(conn, user["id"])
    return {"items": items}


@router.post("", response_model=Tag, status_code=201)
async def create_tag(data: TagCreate, user: CurrentUser, conn: DbConnection) -> dict:
    """Создание тега."""
    return await tag_repo.insert_tag(conn, user["id"], data.name)


@router.get("/{tag_id}", response_model=Tag)
async def get_tag(tag_id: str, user: CurrentUser, conn: DbConnection) -> dict:
    """Получение тега по id."""
    tag = await tag_repo.find_tag(conn, user["id"], tag_id)
    if tag is None:
        raise NotFoundError("Тег не найден")
    return tag


@router.patch("/{tag_id}", response_model=Tag)
async def update_tag(tag_id: str, data: TagUpdate, user: CurrentUser, conn: DbConnection) -> dict:
    """Обновление тега."""
    tag = await tag_repo.update_tag(conn, user["id"], tag_id, data.name)
    if tag is None:
        raise NotFoundError("Тег не найден")
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: str, user: CurrentUser, conn: DbConnection) -> None:
    """Удаление тега."""
    deleted = await tag_repo.delete_tag(conn, user["id"], tag_id)
    if not deleted:
        raise NotFoundError("Тег не найден")
