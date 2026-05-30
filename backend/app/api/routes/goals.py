"""Маршруты для управления финансовыми целями."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbConnection
from app.core.errors import NotFoundError
from app.repositories import goals as goal_repo
from app.schemas.goal import FinancialGoal, FinancialGoalCreate, FinancialGoalList, FinancialGoalUpdate

router = APIRouter()


@router.get("", response_model=FinancialGoalList)
async def list_goals(user: CurrentUser, conn: DbConnection) -> dict:
    """Список финансовых целей."""
    items = await goal_repo.list_goals(conn, user["id"])
    return {"items": items}


@router.post("", response_model=FinancialGoal, status_code=201)
async def create_goal(
    data: FinancialGoalCreate, user: CurrentUser, conn: DbConnection
) -> dict:
    """Создание финансовой цели."""
    params = data.model_dump()
    params["user_id"] = user["id"]
    return await goal_repo.insert_goal(conn, params)


@router.get("/{goal_id}", response_model=FinancialGoal)
async def get_goal(goal_id: str, conn: DbConnection) -> dict:
    """Получение цели."""
    goal = await goal_repo.find_goal(conn, goal_id)
    if goal is None:
        raise NotFoundError("Цель не найдена")
    return goal


@router.patch("/{goal_id}", response_model=FinancialGoal)
async def update_goal(goal_id: str, data: FinancialGoalUpdate, conn: DbConnection) -> dict:
    """Обновление цели."""
    return await goal_repo.update_goal(conn, goal_id, data.model_dump(exclude_none=True))


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: str, conn: DbConnection) -> None:
    """Удаление цели."""
    await goal_repo.delete_goal(conn, goal_id)
