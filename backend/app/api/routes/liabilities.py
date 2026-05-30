"""Маршруты для управления обязательствами."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import liabilities as liab_repo
from app.schemas.liability import Liability, LiabilityCreate, LiabilityList, LiabilityUpdate

router = APIRouter()


@router.get("", response_model=LiabilityList)
async def list_liabilities(
    user: CurrentUser,
    conn: DbConnection,
    status: str | None = Query(None),
    liability_type_id: str | None = Query(None),
) -> dict:
    """Список обязательств с фильтрацией."""
    items = await liab_repo.list_liabilities(conn, user["id"], status, liability_type_id)
    return {"items": items}


@router.post("", response_model=Liability, status_code=201)
async def create_liability(
    data: LiabilityCreate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Создание обязательства."""
    params = data.model_dump()
    params["user_id"] = user["id"]
    return await liab_repo.insert_liability(conn, params)


@router.get("/{liability_id}", response_model=Liability)
async def get_liability(liability_id: str, user: CurrentUser, conn: DbConnection) -> dict:
    """Получение обязательства."""
    liab = await liab_repo.find_liability(conn, user["id"], liability_id)
    if liab is None:
        raise NotFoundError("Обязательство не найдено")
    return liab


@router.patch("/{liability_id}", response_model=Liability)
async def update_liability(
    liability_id: str, data: LiabilityUpdate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Обновление обязательства."""
    liability = await liab_repo.update_liability(conn, user["id"], liability_id, data.model_dump())
    if liability is None:
        raise NotFoundError("Обязательство не найдено")
    return liability


@router.delete("/{liability_id}", status_code=204)
async def close_liability(liability_id: str, user: CurrentUser, conn: DbConnection) -> None:
    """Закрытие обязательства."""
    liability = await liab_repo.close_liability(conn, user["id"], liability_id)
    if liability is None:
        raise NotFoundError("Обязательство не найдено")
