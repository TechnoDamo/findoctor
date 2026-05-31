"""Маршруты для управления активами."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import assets as asset_repo
from app.schemas.asset import Asset, AssetCreate, AssetList, AssetUpdate

router = APIRouter()


@router.get("", response_model=AssetList)
async def list_assets(
    user: CurrentUser,
    conn: DbConnection,
    asset_type_id: str | None = Query(None),
) -> dict:
    """Список активов с фильтрацией."""
    items = await asset_repo.list_assets(conn, user["id"], asset_type_id)
    return {"items": items}


@router.post("", response_model=Asset, status_code=201)
async def create_asset(data: AssetCreate, user: CurrentUser, conn: DbConnection) -> dict:
    """Создание актива."""
    params = data.model_dump()
    params["user_id"] = user["id"]
    return await asset_repo.insert_asset(conn, params)


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str, user: CurrentUser, conn: DbConnection) -> dict:
    """Получение актива."""
    asset = await asset_repo.find_asset(conn, user["id"], asset_id)
    if asset is None:
        raise NotFoundError("Актив не найден")
    return asset


@router.patch("/{asset_id}", response_model=Asset)
async def update_asset(asset_id: str, data: AssetUpdate, user: CurrentUser, conn: DbConnection) -> dict:
    """Обновление актива."""
    asset = await asset_repo.update_asset(conn, user["id"], asset_id, data.model_dump())
    if asset is None:
        raise NotFoundError("Актив не найден")
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: str, user: CurrentUser, conn: DbConnection) -> None:
    """Удаление актива."""
    deleted = await asset_repo.delete_asset(conn, user["id"], asset_id)
    if not deleted:
        raise NotFoundError("Актив не найден")
