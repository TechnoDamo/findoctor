"""Маршруты для управления платежами по обязательствам."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import liability_payments as lp_repo
from app.schemas.liability_payment import (
    LiabilityPayment,
    LiabilityPaymentCreate,
    LiabilityPaymentList,
    LiabilityPaymentUpdate,
)
from app.services import liability_payments as lp_service

router = APIRouter()


@router.get("", response_model=LiabilityPaymentList)
async def list_liability_payments(
    user: CurrentUser,
    conn: DbConnection,
    liability_id: str | None = Query(None),
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None, alias="to"),
) -> dict:
    """Список платежей с фильтрацией."""
    items = await lp_repo.list_liability_payments(
        conn, user["id"], **{"from": from_, "to": to, "liability_id": liability_id}
    )
    return {"items": items}


@router.post("", response_model=LiabilityPayment, status_code=201)
async def create_liability_payment(
    data: LiabilityPaymentCreate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Создание платежа по обязательству (автоматически создаёт транзакцию, если не указана)."""
    return await lp_service.create_liability_payment(conn, user["id"], data.model_dump())


@router.get("/{liability_payment_id}", response_model=LiabilityPayment)
async def get_liability_payment(liability_payment_id: str, conn: DbConnection) -> dict:
    """Получение платежа."""
    payment = await lp_repo.find_liability_payment(conn, liability_payment_id)
    if payment is None:
        raise NotFoundError("Платёж не найден")
    return payment


@router.patch("/{liability_payment_id}", response_model=LiabilityPayment)
async def update_liability_payment(
    liability_payment_id: str, data: LiabilityPaymentUpdate, conn: DbConnection
) -> dict:
    """Обновление платежа."""
    return await lp_repo.update_liability_payment(
        conn, liability_payment_id, data.model_dump()
    )


@router.delete("/{liability_payment_id}", status_code=204)
async def delete_liability_payment(liability_payment_id: str, conn: DbConnection) -> None:
    """Удаление платежа."""
    await lp_repo.delete_liability_payment(conn, liability_payment_id)
