"""
Сервис управления платежами по обязательствам.

При создании платежа без явного transaction_id:
  - Автоматически создаёт транзакцию-расход на указанном счёте.
  - Привязывает её к платежу по обязательству.
"""

from psycopg import AsyncConnection

from app.core.errors import NotFoundError
from app.repositories import accounts as accounts_repo
from app.repositories import liabilities as liability_repo
from app.repositories import liability_payments as lp_repo
from app.repositories import transactions as txn_repo


async def create_liability_payment(
    conn: AsyncConnection, user_id: str, data: dict
) -> dict:
    """
    Создание платежа по обязательству.

    Если transaction_id не указан — создаёт транзакцию-расход автоматически.
    """
    liability = await liability_repo.find_liability(conn, user_id, data["liability_id"])
    if liability is None:
        raise NotFoundError("Обязательство не найдено")

    transaction_id = data.get("transaction_id")

    if transaction_id is None:
        account = await accounts_repo.find_account(conn, user_id, data["account_id"])
        if account is None:
            raise NotFoundError("Счёт не найден")

        transaction = await txn_repo.insert_transaction(
            conn,
            {
                "user_id": user_id,
                "account_id": data["account_id"],
                "category_id": None,
                "type": "expense",
                "amount": str(-abs(float(data["total_amount"]))),
                "currency": data["currency"],
                "transaction_datetime": f"{data['payment_date']}T12:00:00Z",
                "description": f"Платёж по: {liability['name']}",
                "merchant_id": None,
                "merchant_name": liability.get("creditor_name"),
                "geo_location": None,
                "recurring_transaction_id": data.get("recurring_transaction_id"),
                "external_id": None,
                "transfer_id": None,
                "transfer_leg": None,
            },
        )
        transaction_id = transaction["id"]

    payment = await lp_repo.insert_liability_payment(
        conn,
        {
            "user_id": user_id,
            "liability_id": data["liability_id"],
            "transaction_id": transaction_id,
            "recurring_transaction_id": data.get("recurring_transaction_id"),
            "payment_date": data["payment_date"],
            "total_amount": data["total_amount"],
            "principal_amount": data.get("principal_amount"),
            "interest_amount": data.get("interest_amount"),
            "fee_amount": data.get("fee_amount"),
            "currency": data["currency"],
            "balance_after_payment": data.get("balance_after_payment"),
        },
    )

    return payment
