"""
Сервис управления переводами между счетами.

Ключевая бизнес-логика:
  - Создание перевода атомарно создаёт transfer + debit-транзакцию + credit-транзакцию.
  - Обновление перевода синхронизирует связанные транзакции.
  - Удаление перевода удаляет transfer и обе транзакции в одной транзакции БД.
"""

from psycopg import AsyncConnection

from app.core.errors import ConflictError, NotFoundError
from app.repositories import accounts as accounts_repo
from app.repositories import transactions as txn_repo
from app.repositories import transfers as transfer_repo


async def create_transfer(
    conn: AsyncConnection, user_id: str, data: dict
) -> dict:
    """
    Создание перевода и двух связанных транзакций в одной атомарной операции.

    Проверяет:
      - Оба счёта существуют и принадлежат пользователю.
      - Счёт-источник и счёт-получатель — разные счета.
    """
    from_account = await accounts_repo.find_account(conn, data["from_account_id"])
    to_account = await accounts_repo.find_account(conn, data["to_account_id"])

    if from_account is None or to_account is None:
        raise NotFoundError("Счёт не найден")
    if from_account["user_id"] != user_id or to_account["user_id"] != user_id:
        raise NotFoundError("Счёт не найден")
    if data["from_account_id"] == data["to_account_id"]:
        raise ConflictError("Нельзя перевести средства на тот же счёт")

    from decimal import Decimal

    async with conn.transaction():
        transfer = await transfer_repo.insert_transfer(
            conn,
            {
                "user_id": user_id,
                "from_account_id": data["from_account_id"],
                "to_account_id": data["to_account_id"],
                "amount": data["amount"],
                "currency": data["currency"],
                "transaction_datetime": data["transaction_datetime"],
                "description": data.get("description"),
            },
        )

        debit_amount = str(-Decimal(str(data["amount"])))
        debit_txn = await txn_repo.insert_transaction(
            conn,
            {
                "user_id": user_id,
                "account_id": data["from_account_id"],
                "category_id": data.get("category_id"),
                "type": "transfer",
                "amount": debit_amount,
                "currency": data["currency"],
                "transaction_datetime": data["transaction_datetime"],
                "description": data.get("description"),
                "merchant_id": None,
                "merchant_name": None,
                "geo_location": None,
                "recurring_transaction_id": None,
                "external_id": data.get("external_id"),
                "transfer_id": transfer["id"],
                "transfer_leg": "debit",
            },
        )

        credit_txn = await txn_repo.insert_transaction(
            conn,
            {
                "user_id": user_id,
                "account_id": data["to_account_id"],
                "category_id": data.get("category_id"),
                "type": "transfer",
                "amount": data["amount"],
                "currency": data["currency"],
                "transaction_datetime": data["transaction_datetime"],
                "description": data.get("description"),
                "merchant_id": None,
                "merchant_name": None,
                "geo_location": None,
                "recurring_transaction_id": None,
                "external_id": None,
                "transfer_id": transfer["id"],
                "transfer_leg": "credit",
            },
        )

    return {
        **transfer,
        "from_transaction_id": debit_txn["id"],
        "to_transaction_id": credit_txn["id"],
        "from_transaction": debit_txn,
        "to_transaction": credit_txn,
    }


async def update_transfer(
    conn: AsyncConnection, user_id: str, transfer_id: str, data: dict
) -> dict:
    """
    Обновление перевода и синхронизация связанных транзакций.

    Если меняется счёт-источник или счёт-получатель, обновляются и транзакции.
    """
    existing = await transfer_repo.find_transfer(conn, transfer_id)
    if existing is None or existing["user_id"] != user_id:
        raise NotFoundError("Перевод не найден")

    from decimal import Decimal

    async with conn.transaction():
        updated_transfer = await transfer_repo.update_transfer(conn, transfer_id, data)

        if "from_account_id" in data:
            await txn_repo.update_transaction(
                conn,
                existing["from_transaction_id"],
                {"account_id": data["from_account_id"]},
            )
        if "to_account_id" in data:
            await txn_repo.update_transaction(
                conn,
                existing["to_transaction_id"],
                {"account_id": data["to_account_id"]},
            )
        if "amount" in data:
            await txn_repo.update_transaction(
                conn,
                existing["from_transaction_id"],
                {"amount": str(-Decimal(str(data["amount"])))},
            )
            await txn_repo.update_transaction(
                conn,
                existing["to_transaction_id"],
                {"amount": data["amount"]},
            )
        if "currency" in data:
            await txn_repo.update_transaction(
                conn, existing["from_transaction_id"], {"currency": data["currency"]}
            )
            await txn_repo.update_transaction(
                conn, existing["to_transaction_id"], {"currency": data["currency"]}
            )
        if "transaction_datetime" in data:
            await txn_repo.update_transaction(
                conn,
                existing["from_transaction_id"],
                {"transaction_datetime": data["transaction_datetime"]},
            )
            await txn_repo.update_transaction(
                conn,
                existing["to_transaction_id"],
                {"transaction_datetime": data["transaction_datetime"]},
            )
        if "description" != None:
            await txn_repo.update_transaction(
                conn,
                existing["from_transaction_id"],
                {"description": data["description"]},
            )
            await txn_repo.update_transaction(
                conn,
                existing["to_transaction_id"],
                {"description": data["description"]},
            )

    return updated_transfer


async def delete_transfer(
    conn: AsyncConnection, user_id: str, transfer_id: str
) -> None:
    """
    Удаление перевода и связанных транзакций в одной атомарной операции.
    """
    existing = await transfer_repo.find_transfer(conn, transfer_id)
    if existing is None or existing["user_id"] != user_id:
        raise NotFoundError("Перевод не найден")

    async with conn.transaction():
        await transfer_repo.delete_transfer_transactions(conn, transfer_id)
        await transfer_repo.delete_transfer(conn, transfer_id)
