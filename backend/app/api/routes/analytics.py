"""Маршруты аналитики: дашборд, снимки, денежный поток, капитал."""

from uuid import uuid4

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DbConnection
from app.repositories import analytics as analytics_repo
from app.schemas.analytics import (
    CashFlowSeries,
    DailyFinancialSnapshotList,
    DashboardSummary,
    JobAccepted,
    NetWorthSeries,
    SnapshotRecalculateRequest,
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(user: CurrentUser, conn: DbConnection) -> dict:
    """Сводка финансового состояния."""
    summary = await analytics_repo.get_dashboard_summary(
        conn, user["id"], user["base_currency"]
    )
    defaults = {
        "currency": user["base_currency"],
        "total_cash": "0",
        "total_assets": "0",
        "total_liabilities": "0",
        "net_worth": "0",
        "monthly_income": "0",
        "monthly_expenses": "0",
        "savings_rate": None,
        "upcoming_recurring_transactions": [],
    }
    if summary is None:
        return defaults
    return {**defaults, **summary}


@router.get("/snapshots", response_model=DailyFinancialSnapshotList)
async def list_daily_snapshots(
    user: CurrentUser,
    conn: DbConnection,
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None, alias="to"),
) -> dict:
    """Список ежедневных финансовых снимков."""
    items = await analytics_repo.list_snapshots(conn, user["id"], from_, to)
    return {"items": items}


@router.post("/snapshots/recalculate", response_model=JobAccepted, status_code=202)
async def recalculate_snapshots(
    data: SnapshotRecalculateRequest,
    user: CurrentUser,
    conn: DbConnection,
) -> dict:
    """Постановка задачи на перерасчёт снимков."""
    job_id = str(uuid4())
    return {"job_id": job_id, "status": "queued"}


@router.get("/cash-flow", response_model=CashFlowSeries)
async def get_cash_flow(
    user: CurrentUser,
    conn: DbConnection,
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None, alias="to"),
    group_by: str = Query("month", pattern=r"^(day|week|month)$"),
) -> dict:
    """Денежный поток за период."""
    items = await analytics_repo.get_cash_flow(conn, user["id"], from_, to, group_by)
    return {"currency": user["base_currency"], "items": items}


@router.get("/net-worth", response_model=NetWorthSeries)
async def get_net_worth(
    user: CurrentUser,
    conn: DbConnection,
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None, alias="to"),
) -> dict:
    """Динамика чистого капитала."""
    items = await analytics_repo.get_net_worth(conn, user["id"], from_, to)
    return {"currency": user["base_currency"], "items": items}
