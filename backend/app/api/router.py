"""
Главный роутер API, объединяющий все маршруты приложения.
"""

from fastapi import APIRouter

from app.api.routes import (
    accounts,
    ai_chat,
    analytics,
    assets,
    auth,
    financial_institutions,
    goals,
    imports,
    liabilities,
    liability_payments,
    me,
    recurring_transactions,
    reference,
    tags,
    transactions,
    transfers,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(me.router, prefix="/me", tags=["Current User"])
api_router.include_router(reference.router, prefix="/reference", tags=["Reference Data"])
api_router.include_router(reference.merchants_router, prefix="/merchants", tags=["Reference Data"])
api_router.include_router(financial_institutions.router, prefix="/financial-institutions", tags=["Financial Institutions"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["Transfers"])
api_router.include_router(recurring_transactions.router, prefix="/recurring-transactions", tags=["Recurring Transactions"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(liabilities.router, prefix="/liabilities", tags=["Liabilities"])
api_router.include_router(liability_payments.router, prefix="/liability-payments", tags=["Liability Payments"])
api_router.include_router(goals.router, prefix="/goals", tags=["Goals"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ai_chat.router, prefix="/ai/chat", tags=["AI Chat"])
api_router.include_router(imports.router, prefix="/transactions/import", tags=["Imports"])
