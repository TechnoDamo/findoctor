"""Маршрут продуктовых финансовых рекомендаций."""

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import ValidationError
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationType,
)
from app.services.product_recommendations import build_recommendation

router = APIRouter()


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(
    data: RecommendationRequest,
    user: CurrentUser,
    conn: DbConnection,
    type_: RecommendationType = Query(..., alias="type"),
) -> RecommendationResponse:
    """Единый endpoint для продуктовых рекомендаций по типу анализа."""
    if type_ == RecommendationType.savings_goal:
        raise ValidationError("Тип savings_goal временно недоступен: выберите активную цель позже")
    if type_ == RecommendationType.credit_decision and data.credit is None:
        raise ValidationError("Для type=credit_decision требуется объект credit")

    return await build_recommendation(
        conn=conn,
        user=user,
        recommendation_type=type_,
        request=data,
    )
