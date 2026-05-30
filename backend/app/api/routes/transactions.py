"""Маршруты для управления транзакциями."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import tags as tag_repo
from app.repositories import transactions as txn_repo
from app.schemas.tag import TagList, TransactionTagsReplace
from app.schemas.transaction import (
    Transaction,
    TransactionCreate,
    TransactionPage,
    TransactionUpdate,
)

router = APIRouter()


@router.get("", response_model=TransactionPage)
async def list_transactions(
    user: CurrentUser,
    conn: DbConnection,
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None, alias="to"),
    account_id: str | None = Query(None),
    category_id: str | None = Query(None),
    type_: str | None = Query(None, alias="type"),
    merchant_id: str | None = Query(None),
    recurring_transaction_id: str | None = Query(None),
    tag_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=250),
) -> dict:
    """Список транзакций с пагинацией и фильтрацией."""
    items, total = await txn_repo.list_transactions(
        conn,
        user["id"],
        page=page,
        page_size=page_size,
        **{
            "from": from_,
            "to": to,
            "type": type_,
            "account_id": account_id,
            "category_id": category_id,
            "merchant_id": merchant_id,
            "recurring_transaction_id": recurring_transaction_id,
            "tag_id": tag_id,
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


@router.post("", response_model=Transaction, status_code=201)
async def create_transaction(
    data: TransactionCreate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Создание новой транзакции."""
    params = data.model_dump(exclude={"tag_ids"})
    params["user_id"] = user["id"]
    params.setdefault("transfer_id", None)
    params.setdefault("transfer_leg", None)
    return await txn_repo.insert_transaction(conn, params)


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, user: CurrentUser, conn: DbConnection) -> dict:
    """Получение транзакции по id."""
    txn = await txn_repo.find_transaction(conn, user["id"], transaction_id)
    if txn is None:
        raise NotFoundError("Транзакция не найдена")
    return txn


@router.patch("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str, data: TransactionUpdate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Обновление транзакции."""
    txn = await txn_repo.update_transaction(conn, user["id"], transaction_id, data.model_dump())
    if txn is None:
        raise NotFoundError("Транзакция не найдена")
    return txn


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: str, user: CurrentUser, conn: DbConnection) -> None:
    """Удаление транзакции."""
    deleted = await txn_repo.delete_transaction(conn, user["id"], transaction_id)
    if not deleted:
        raise NotFoundError("Транзакция не найдена")


@router.get("/{transaction_id}/tags", response_model=TagList)
async def list_transaction_tags(transaction_id: str, user: CurrentUser, conn: DbConnection) -> dict:
    """Список тегов транзакции."""
    txn = await txn_repo.find_transaction(conn, user["id"], transaction_id)
    if txn is None:
        raise NotFoundError("Транзакция не найдена")
    tags = await tag_repo.list_transaction_tags(conn, user["id"], transaction_id)
    return {"items": tags}


@router.put("/{transaction_id}/tags", response_model=TagList)
async def replace_transaction_tags(
    transaction_id: str,
    data: TransactionTagsReplace,
    user: CurrentUser,
    conn: DbConnection,
) -> dict:
    """Полная замена тегов транзакции."""
    txn = await txn_repo.find_transaction(conn, user["id"], transaction_id)
    if txn is None:
        raise NotFoundError("Транзакция не найдена")
    items = await tag_repo.replace_transaction_tags(
        conn, user["id"], transaction_id, data.tag_ids
    )
    return {"items": items}


@router.post("/{transaction_id}/tags/{tag_id}", status_code=204)
async def attach_transaction_tag(
    transaction_id: str,
    tag_id: str,
    user: CurrentUser,
    conn: DbConnection,
) -> None:
    """Прикрепление тега к транзакции."""
    attached = await tag_repo.attach_tag(conn, user["id"], transaction_id, tag_id)
    if not attached:
        raise NotFoundError("Транзакция или тег не найден")


@router.delete("/{transaction_id}/tags/{tag_id}", status_code=204)
async def detach_transaction_tag(
    transaction_id: str,
    tag_id: str,
    user: CurrentUser,
    conn: DbConnection,
) -> None:
    """Открепление тега от транзакции."""
    detached = await tag_repo.detach_tag(conn, user["id"], transaction_id, tag_id)
    if not detached:
        raise NotFoundError("Транзакция или тег не найден")
