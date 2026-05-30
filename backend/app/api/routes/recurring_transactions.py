"""Маршруты для управления регулярными операциями."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import recurring_transactions as rt_repo
from app.schemas.recurring_transaction import (
    RecurringTransaction,
    RecurringTransactionCreate,
    RecurringTransactionList,
    RecurringTransactionUpdate,
)

router = APIRouter()


@router.get("", response_model=RecurringTransactionList)
async def list_recurring_transactions(
    user: CurrentUser,
    conn: DbConnection,
    is_active: bool | None = Query(None),
    account_id: str | None = Query(None),
    liability_id: str | None = Query(None),
    next_payment_before: str | None = Query(None),
) -> dict:
    """Список регулярных операций с фильтрацией."""
    items = await rt_repo.list_recurring_transactions(
        conn,
        user["id"],
        is_active=is_active,
        account_id=account_id,
        liability_id=liability_id,
        next_payment_before=next_payment_before,
    )
    return {"items": items}


@router.post("", response_model=RecurringTransaction, status_code=201)
async def create_recurring_transaction(
    data: RecurringTransactionCreate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Создание регулярной операции."""
    params = data.model_dump()
    params["user_id"] = user["id"]
    return await rt_repo.insert_recurring_transaction(conn, params)


@router.get("/{recurring_transaction_id}", response_model=RecurringTransaction)
async def get_recurring_transaction(
    recurring_transaction_id: str, conn: DbConnection
) -> dict:
    """Получение регулярной операции по id."""
    item = await rt_repo.find_recurring_transaction(conn, recurring_transaction_id)
    if item is None:
        raise NotFoundError("Регулярная операция не найдена")
    return item


@router.patch("/{recurring_transaction_id}", response_model=RecurringTransaction)
async def update_recurring_transaction(
    recurring_transaction_id: str,
    data: RecurringTransactionUpdate,
    conn: DbConnection,
) -> dict:
    """Обновление регулярной операции."""
    return await rt_repo.update_recurring_transaction(
        conn, recurring_transaction_id, data.model_dump(exclude_none=True)
    )


@router.delete("/{recurring_transaction_id}", status_code=204)
async def deactivate_recurring_transaction(
    recurring_transaction_id: str, conn: DbConnection
) -> None:
    """Деактивация регулярной операции."""
    await rt_repo.deactivate_recurring_transaction(conn, recurring_transaction_id)
