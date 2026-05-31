"""Маршруты для управления финансовыми организациями."""

from fastapi import APIRouter, Query

from app.api.dependencies import DbConnection
from app.core.errors import NotFoundError
from app.repositories import financial_institutions as fi_repo
from app.schemas.financial_institution import (
    FinancialInstitution,
    FinancialInstitutionCreate,
    FinancialInstitutionList,
    FinancialInstitutionUpdate,
)

router = APIRouter()


@router.get("", response_model=FinancialInstitutionList)
async def list_financial_institutions(
    conn: DbConnection,
    q: str | None = Query(None),
    country: str | None = Query(None),
    provider_type_code: str | None = Query(None),
    active_only: bool = Query(True),
) -> dict:
    """Поиск финансовых организаций."""
    items = await fi_repo.list_institutions(
        conn, q=q, country=country, provider_type_code=provider_type_code, active_only=active_only
    )
    return {"items": items}


@router.post("", response_model=FinancialInstitution, status_code=201)
async def create_financial_institution(
    data: FinancialInstitutionCreate, conn: DbConnection
) -> dict:
    """Создание финансовой организации."""
    provider_type_ids = data.provider_type_ids
    params = data.model_dump(exclude={"provider_type_ids"})
    institution = await fi_repo.insert_institution(conn, params)
    if provider_type_ids:
        await fi_repo.insert_institution_provider_types(conn, institution["id"], provider_type_ids)
    institution["provider_type_ids"] = provider_type_ids
    return institution


@router.get("/{institution_id}", response_model=FinancialInstitution)
async def get_financial_institution(institution_id: str, conn: DbConnection) -> dict:
    """Получение финансовой организации."""
    inst = await fi_repo.find_institution(conn, institution_id)
    if inst is None:
        raise NotFoundError("Финансовая организация не найдена")
    return inst


@router.patch("/{institution_id}", response_model=FinancialInstitution)
async def update_financial_institution(
    institution_id: str, data: FinancialInstitutionUpdate, conn: DbConnection
) -> dict:
    """Обновление финансовой организации."""
    provider_type_ids = data.provider_type_ids
    params = data.model_dump(exclude={"provider_type_ids"})
    if params:
        institution = await fi_repo.update_institution(conn, institution_id, params)
    else:
        institution = await fi_repo.find_institution(conn, institution_id)
        if institution is None:
            raise NotFoundError("Финансовая организация не найдена")

    if provider_type_ids is not None:
        await fi_repo.replace_institution_provider_types(conn, institution_id, provider_type_ids)
        institution["provider_type_ids"] = provider_type_ids

    return institution
