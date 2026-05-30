"""Маршруты для управления счетами."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import accounts as account_repo
from app.schemas.account import Account, AccountCreate, AccountList, AccountUpdate

router = APIRouter()


@router.get("", response_model=AccountList)
async def list_accounts(
    user: CurrentUser,
    conn: DbConnection,
    is_active: bool | None = Query(None),
    account_type_id: str | None = Query(None),
    institution_id: str | None = Query(None),
    currency: str | None = Query(None),
) -> dict:
    """Список счетов с фильтрацией."""
    items = await account_repo.list_accounts(
        conn,
        user["id"],
        is_active=is_active,
        account_type_id=account_type_id,
        institution_id=institution_id,
        currency=currency,
    )
    return {"items": items}


@router.post("", response_model=Account, status_code=201)
async def create_account(data: AccountCreate, user: CurrentUser, conn: DbConnection) -> dict:
    """Создание нового счёта."""
    params = data.model_dump()
    params["user_id"] = user["id"]
    return await account_repo.insert_account(conn, params)


@router.get("/{account_id}", response_model=Account)
async def get_account(account_id: str, conn: DbConnection) -> dict:
    """Получение счёта по id."""
    account = await account_repo.find_account(conn, account_id)
    if account is None:
        raise NotFoundError("Счёт не найден")
    return account


@router.patch("/{account_id}", response_model=Account)
async def update_account(
    account_id: str, data: AccountUpdate, conn: DbConnection
) -> dict:
    """Обновление счёта."""
    return await account_repo.update_account(conn, account_id, data.model_dump())


@router.delete("/{account_id}", status_code=204)
async def archive_account(account_id: str, conn: DbConnection) -> None:
    """Архивация счёта."""
    await account_repo.archive_account(conn, account_id)
