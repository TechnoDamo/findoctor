-- name: list_transactions
-- Список транзакций с пагинацией и фильтрацией
SELECT t.id, t.user_id, t.account_id, t.category_id, t.type,
       t.amount, t.currency, t.transaction_datetime, t.description,
       t.merchant_id, t.merchant_name, t.geo_location,
       t.recurring_transaction_id, t.external_id,
       t.transfer_id, t.transfer_leg, t.created_at,
       COALESCE(json_agg(json_build_object('id', tg.id, 'user_id', tg.user_id, 'name', tg.name))
                FILTER (WHERE tg.id IS NOT NULL), '[]'::json) AS tags
FROM transactions t
LEFT JOIN transaction_tags tt ON t.id = tt.transaction_id
LEFT JOIN tags tg ON tt.tag_id = tg.id
WHERE t.user_id = %(user_id)s
  AND (%(from)s IS NULL OR t.transaction_datetime >= %(from)s)
  AND (%(to)s IS NULL OR t.transaction_datetime <= %(to)s)
  AND (%(account_id)s IS NULL OR t.account_id = %(account_id)s)
  AND (%(category_id)s IS NULL OR t.category_id = %(category_id)s)
  AND (%(type)s IS NULL OR t.type = %(type)s)
  AND (%(merchant_id)s IS NULL OR t.merchant_id = %(merchant_id)s)
  AND (%(recurring_transaction_id)s IS NULL OR t.recurring_transaction_id = %(recurring_transaction_id)s)
  AND (%(tag_id)s IS NULL OR tt.tag_id = %(tag_id)s)
GROUP BY t.id
ORDER BY t.transaction_datetime DESC
LIMIT %(page_size)s OFFSET %(offset)s;

-- name: count_transactions
-- Подсчёт транзакций для пагинации
SELECT COUNT(DISTINCT t.id) AS total
FROM transactions t
LEFT JOIN transaction_tags tt ON t.id = tt.transaction_id
WHERE t.user_id = %(user_id)s
  AND (%(from)s IS NULL OR t.transaction_datetime >= %(from)s)
  AND (%(to)s IS NULL OR t.transaction_datetime <= %(to)s)
  AND (%(account_id)s IS NULL OR t.account_id = %(account_id)s)
  AND (%(category_id)s IS NULL OR t.category_id = %(category_id)s)
  AND (%(type)s IS NULL OR t.type = %(type)s)
  AND (%(merchant_id)s IS NULL OR t.merchant_id = %(merchant_id)s)
  AND (%(recurring_transaction_id)s IS NULL OR t.recurring_transaction_id = %(recurring_transaction_id)s)
  AND (%(tag_id)s IS NULL OR tt.tag_id = %(tag_id)s);

-- name: find_transaction
-- Получение транзакции по id с тегами
SELECT t.id, t.user_id, t.account_id, t.category_id, t.type,
       t.amount, t.currency, t.transaction_datetime, t.description,
       t.merchant_id, t.merchant_name, t.geo_location,
       t.recurring_transaction_id, t.external_id,
       t.transfer_id, t.transfer_leg, t.created_at,
       COALESCE(json_agg(json_build_object('id', tg.id, 'user_id', tg.user_id, 'name', tg.name))
                FILTER (WHERE tg.id IS NOT NULL), '[]'::json) AS tags
FROM transactions t
LEFT JOIN transaction_tags tt ON t.id = tt.transaction_id
LEFT JOIN tags tg ON tt.tag_id = tg.id
WHERE t.id = %(transaction_id)s
GROUP BY t.id;

-- name: insert_transaction
-- Создание транзакции
INSERT INTO transactions (id, user_id, account_id, category_id, type, amount, currency,
    transaction_datetime, description, merchant_id, merchant_name, geo_location,
    recurring_transaction_id, external_id, transfer_id, transfer_leg, created_at)
VALUES (gen_random_uuid(), %(user_id)s, %(account_id)s, %(category_id)s, %(type)s,
    %(amount)s, %(currency)s, %(transaction_datetime)s, %(description)s,
    %(merchant_id)s, %(merchant_name)s, %(geo_location)s,
    %(recurring_transaction_id)s, %(external_id)s,
    %(transfer_id)s, %(transfer_leg)s, now())
RETURNING id, user_id, account_id, category_id, type, amount, currency,
    transaction_datetime, description, merchant_id, merchant_name, geo_location,
    recurring_transaction_id, external_id, transfer_id, transfer_leg, created_at;

-- name: update_transaction
-- Обновление транзакции
UPDATE transactions SET
    account_id = COALESCE(%(account_id)s, account_id),
    category_id = COALESCE(%(category_id)s::uuid, category_id),
    type = COALESCE(%(type)s, type),
    amount = COALESCE(%(amount)s, amount),
    currency = COALESCE(%(currency)s, currency),
    transaction_datetime = COALESCE(%(transaction_datetime)s, transaction_datetime),
    description = COALESCE(%(description)s::varchar, description),
    merchant_id = COALESCE(%(merchant_id)s::uuid, merchant_id),
    merchant_name = COALESCE(%(merchant_name)s::varchar, merchant_name),
    geo_location = COALESCE(%(geo_location)s::varchar, geo_location),
    recurring_transaction_id = COALESCE(%(recurring_transaction_id)s::uuid, recurring_transaction_id),
    external_id = COALESCE(%(external_id)s::varchar, external_id)
WHERE id = %(transaction_id)s
RETURNING id, user_id, account_id, category_id, type, amount, currency,
    transaction_datetime, description, merchant_id, merchant_name, geo_location,
    recurring_transaction_id, external_id, transfer_id, transfer_leg, created_at;

-- name: delete_transaction
-- Удаление транзакции
DELETE FROM transactions WHERE id = %(transaction_id)s;
