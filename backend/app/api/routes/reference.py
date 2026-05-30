"""Маршруты справочных данных: типы, категории, продавцы."""

from fastapi import APIRouter, Query

from app.api.dependencies import DbConnection
from app.core.errors import NotFoundError
from app.repositories import reference as ref_repo
from app.schemas.reference import (
    AccountType,
    AssetType,
    Category,
    CategoryCreate,
    CategoryUpdate,
    LiabilityType,
    Merchant,
    MerchantCreate,
    MerchantList,
    MerchantUpdate,
    ProviderType,
)

router = APIRouter()
merchants_router = APIRouter()


# ---------------------------------------------------------------------------
# Типы счетов
# ---------------------------------------------------------------------------
@router.get("/account-types", response_model=list[AccountType])
async def list_account_types(conn: DbConnection) -> list[dict]:
    """Список всех типов счетов."""
    return await ref_repo.list_account_types(conn)


# ---------------------------------------------------------------------------
# Типы активов
# ---------------------------------------------------------------------------
@router.get("/asset-types", response_model=list[AssetType])
async def list_asset_types(conn: DbConnection) -> list[dict]:
    """Список всех типов активов."""
    return await ref_repo.list_asset_types(conn)


# ---------------------------------------------------------------------------
# Типы обязательств
# ---------------------------------------------------------------------------
@router.get("/liability-types", response_model=list[LiabilityType])
async def list_liability_types(conn: DbConnection) -> list[dict]:
    """Список всех типов обязательств."""
    return await ref_repo.list_liability_types(conn)


# ---------------------------------------------------------------------------
# Типы провайдеров
# ---------------------------------------------------------------------------
@router.get("/provider-types", response_model=list[ProviderType])
async def list_provider_types(conn: DbConnection) -> list[dict]:
    """Список всех типов финансовых провайдеров."""
    return await ref_repo.list_provider_types(conn)


# ---------------------------------------------------------------------------
# Категории
# ---------------------------------------------------------------------------
@router.get("/categories", response_model=list[Category])
async def list_categories(
    conn: DbConnection,
    type_: str | None = Query(None, alias="type", description="Тип: income или expense"),
    parent_id: str | None = Query(None),
) -> list[dict]:
    """Список категорий с фильтрацией по типу и родителю."""
    return await ref_repo.list_categories(conn, type_=type_, parent_id=parent_id)


@router.post("/categories", response_model=Category, status_code=201)
async def create_category(data: CategoryCreate, conn: DbConnection) -> dict:
    """Создание новой категории."""
    return await ref_repo.insert_category(conn, data.model_dump())


@router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str, conn: DbConnection) -> dict:
    """Получение категории по id."""
    cat = await ref_repo.find_category(conn, category_id)
    if cat is None:
        raise NotFoundError("Категория не найдена")
    return cat


@router.patch("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, data: CategoryUpdate, conn: DbConnection) -> dict:
    """Обновление категории."""
    updated = await ref_repo.update_category(conn, category_id, data.model_dump())
    if updated is None:
        raise NotFoundError("Категория не найдена")
    return updated


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: str, conn: DbConnection) -> None:
    """Удаление категории."""
    await ref_repo.delete_category(conn, category_id)


# ---------------------------------------------------------------------------
# Продавцы
# ---------------------------------------------------------------------------
@merchants_router.get("", response_model=MerchantList)
async def list_merchants(
    conn: DbConnection,
    q: str | None = Query(None),
    country: str | None = Query(None),
    risk_level: str | None = Query(None),
) -> dict:
    """Поиск продавцов."""
    items = await ref_repo.list_merchants(conn, q=q, country=country, risk_level=risk_level)
    return {"items": items}


@merchants_router.post("", response_model=Merchant, status_code=201)
async def create_merchant(data: MerchantCreate, conn: DbConnection) -> dict:
    """Создание продавца."""
    return await ref_repo.insert_merchant(conn, data.model_dump())


@merchants_router.get("/{merchant_id}", response_model=Merchant)
async def get_merchant(merchant_id: str, conn: DbConnection) -> dict:
    """Получение продавца."""
    m = await ref_repo.find_merchant(conn, merchant_id)
    if m is None:
        raise NotFoundError("Продавец не найден")
    return m


@merchants_router.patch("/{merchant_id}", response_model=Merchant)
async def update_merchant(merchant_id: str, data: MerchantUpdate, conn: DbConnection) -> dict:
    """Обновление продавца."""
    return await ref_repo.update_merchant(conn, merchant_id, data.model_dump())


@merchants_router.delete("/{merchant_id}", status_code=204)
async def delete_merchant(merchant_id: str, conn: DbConnection) -> None:
    """Удаление продавца."""
    await ref_repo.delete_merchant(conn, merchant_id)
