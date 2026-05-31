"""Схемы для тегов."""

from uuid import UUID

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """Запрос на создание тега."""
    name: str = Field(min_length=1, max_length=100)


class TagUpdate(TagCreate):
    """Запрос на обновление тега."""
    pass


class Tag(BaseModel):
    """Тег."""
    id: UUID
    user_id: UUID
    name: str


class TagList(BaseModel):
    """Список тегов."""
    items: list[Tag]


class TransactionTagsReplace(BaseModel):
    """Запрос на замену тегов транзакции."""
    tag_ids: list[str]
