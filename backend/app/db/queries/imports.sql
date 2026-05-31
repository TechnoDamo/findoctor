-- name: upsert_transaction
-- Вставка или обновление транзакции по external_id (идемпотентный импорт)
-- Если external_id не указан, проверка пропускается и транзакция просто создаётся.
INSERT INTO transactions (id, user_id, account_id, category_id, type, amount, currency,
    transaction_datetime, description, merchant_id, merchant_name, geo_location,
    recurring_transaction_id, external_id, created_at)
VALUES (gen_random_uuid(), %(user_id)s, %(account_id)s, %(category_id)s, %(type)s,
    %(amount)s, %(currency)s, %(transaction_datetime)s, %(description)s,
    %(merchant_id)s, %(merchant_name)s, %(geo_location)s,
    %(recurring_transaction_id)s, %(external_id)s, now())
ON CONFLICT (account_id, external_id) WHERE external_id IS NOT NULL DO NOTHING
RETURNING id;

-- name: check_external_id_exists
-- Проверка существования транзакции по external_id
SELECT id FROM transactions
WHERE account_id = %(account_id)s AND external_id = %(external_id)s AND external_id IS NOT NULL;
