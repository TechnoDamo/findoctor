"""Схемы для аналитики: дашборд, снимки, денежный поток, капитал."""

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Сводка финансового состояния."""
    currency: str
    total_cash: str
    total_assets: str
    total_liabilities: str
    net_worth: str
    monthly_income: str
    monthly_expenses: str
    savings_rate: float | None = None
    upcoming_recurring_transactions: list[dict] = []


class DailyFinancialSnapshot(BaseModel):
    """Ежедневный финансовый снимок."""
    id: str
    user_id: str
    snapshot_date: str
    total_cash: str
    total_assets: str
    total_liabilities: str
    net_worth: str
    monthly_income: str
    monthly_expenses: str
    savings_rate: float | None = None


class DailyFinancialSnapshotList(BaseModel):
    """Список ежедневных снимков."""
    items: list[DailyFinancialSnapshot]


class SnapshotRecalculateRequest(BaseModel):
    """Запрос на перерасчёт снимков."""
    from_: str
    to: str


class JobAccepted(BaseModel):
    """Подтверждение асинхронной задачи."""
    job_id: str
    status: str = "queued"


class CashFlowPoint(BaseModel):
    """Точка денежного потока за период."""
    period_start: str
    income: str
    expenses: str
    net: str


class CashFlowSeries(BaseModel):
    """Серия денежного потока."""
    currency: str
    items: list[CashFlowPoint]


class NetWorthPoint(BaseModel):
    """Точка чистого капитала."""
    date: str
    total_cash: str
    total_assets: str
    total_liabilities: str
    net_worth: str


class NetWorthSeries(BaseModel):
    """Серия чистого капитала."""
    currency: str
    items: list[NetWorthPoint]
