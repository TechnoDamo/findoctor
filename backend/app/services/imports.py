"""
Сервис идемпотентного импорта транзакций.

Поддерживает массовую вставку до 1000 транзакций за один запрос.
Дубликаты определяются по (account_id, external_id) и пропускаются.
"""

from psycopg import AsyncConnection

from app.repositories import imports as import_repo


async def import_transactions(
    conn: AsyncConnection, user_id: str, items: list[dict], source: str | None = None
) -> dict:
    """
    Идемпотентный импорт списка транзакций.

    Args:
        conn: Соединение с БД.
        user_id: ID пользователя.
        items: Список транзакций для импорта (каждая с обязательным external_id).
        source: Метка источника импорта (например, ключ банковской интеграции).

    Returns:
        Словарь с результатами: created_count, skipped_duplicate_count, failed_count, items.
    """
    result_items: list[dict] = []
    created = 0
    skipped = 0
    failed = 0

    async with conn.transaction():
        for item in items:
            try:
                data = {
                    "user_id": user_id,
                    "account_id": item["account_id"],
                    "category_id": item.get("category_id"),
                    "type": item["type"],
                    "amount": item["amount"],
                    "currency": item["currency"],
                    "transaction_datetime": item["transaction_datetime"],
                    "description": item.get("description"),
                    "merchant_id": item.get("merchant_id"),
                    "merchant_name": item.get("merchant_name"),
                    "geo_location": item.get("geo_location"),
                    "recurring_transaction_id": item.get("recurring_transaction_id"),
                    "external_id": item.get("external_id"),
                    "transfer_id": None,
                    "transfer_leg": None,
                }

                transaction_id = await import_repo.upsert_transaction(conn, data)

                if transaction_id is None:
                    skipped += 1
                    result_items.append({
                        "status": "duplicate",
                        "transaction_id": None,
                        "external_id": item.get("external_id"),
                        "error": None,
                    })
                else:
                    created += 1
                    result_items.append({
                        "status": "created",
                        "transaction_id": transaction_id,
                        "external_id": item.get("external_id"),
                        "error": None,
                    })
            except Exception as e:
                failed += 1
                result_items.append({
                    "status": "failed",
                    "transaction_id": None,
                    "external_id": item.get("external_id"),
                    "error": str(e),
                })

    return {
        "created_count": created,
        "skipped_duplicate_count": skipped,
        "failed_count": failed,
        "items": result_items,
    }
