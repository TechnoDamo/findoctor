"""Маршруты для импорта транзакций."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbConnection
from app.schemas.import_ import TransactionImportRequest, TransactionImportResult
from app.services import imports as import_service

router = APIRouter()


@router.post("", response_model=TransactionImportResult)
async def import_transactions(
    data: TransactionImportRequest,
    user: CurrentUser,
    conn: DbConnection,
) -> dict:
    """Идемпотентный импорт транзакций (до 1000 за раз)."""
    return await import_service.import_transactions(
        conn=conn,
        user_id=user["id"],
        items=[item.model_dump() for item in data.items],
        source=data.source,
    )
