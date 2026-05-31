"""Маршруты для управления переводами между счетами."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import transfers as transfer_repo
from app.schemas.transfer import Transfer, TransferCreate, TransferPage, TransferUpdate
from app.services import transfers as transfer_service

router = APIRouter()


@router.get("", response_model=TransferPage)
async def list_transfers(
    user: CurrentUser,
    conn: DbConnection,
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None, alias="to"),
    account_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=250),
) -> dict:
    """Список переводов с пагинацией."""
    items, total = await transfer_repo.list_transfers(
        conn,
        user["id"],
        page=page,
        page_size=page_size,
        **{
            "from": from_,
            "to": to,
            "account_id": account_id,
        },
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        },
    }


@router.post("", response_model=Transfer, status_code=201)
async def create_transfer(
    data: TransferCreate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Создание перевода и связанных транзакций."""
    return await transfer_service.create_transfer(conn, user["id"], data.model_dump())


@router.get("/{transfer_id}", response_model=Transfer)
async def get_transfer(transfer_id: str, user: CurrentUser, conn: DbConnection) -> dict:
    """Получение перевода по id."""
    transfer = await transfer_repo.find_transfer(conn, user["id"], transfer_id)
    if transfer is None:
        raise NotFoundError("Перевод не найден")
    return transfer


@router.patch("/{transfer_id}", response_model=Transfer)
async def update_transfer(
    transfer_id: str, data: TransferUpdate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Обновление перевода и синхронизация транзакций."""
    return await transfer_service.update_transfer(
        conn, user["id"], transfer_id, data.model_dump()
    )


@router.delete("/{transfer_id}", status_code=204)
async def delete_transfer(
    transfer_id: str, user: CurrentUser, conn: DbConnection
) -> None:
    """Удаление перевода и связанных транзакций."""
    await transfer_service.delete_transfer(conn, user["id"], transfer_id)
