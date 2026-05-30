-- name: list_transfers
-- Список переводов пользователя с пагинацией
SELECT tf.id, tf.user_id, tf.from_account_id, tf.to_account_id,
       tf.amount, tf.currency, tf.transaction_datetime, tf.description
FROM transfers tf
WHERE tf.user_id = %(user_id)s
  AND (%(from)s IS NULL OR tf.transaction_datetime >= %(from)s)
  AND (%(to)s IS NULL OR tf.transaction_datetime <= %(to)s)
  AND (%(account_id)s IS NULL OR tf.from_account_id = %(account_id)s OR tf.to_account_id = %(account_id)s)
ORDER BY tf.transaction_datetime DESC
LIMIT %(page_size)s OFFSET %(offset)s;

-- name: count_transfers
-- Подсчёт переводов для пагинации
SELECT COUNT(*) AS total
FROM transfers tf
WHERE tf.user_id = %(user_id)s
  AND (%(from)s IS NULL OR tf.transaction_datetime >= %(from)s)
  AND (%(to)s IS NULL OR tf.transaction_datetime <= %(to)s)
  AND (%(account_id)s IS NULL OR tf.from_account_id = %(account_id)s OR tf.to_account_id = %(account_id)s);

-- name: find_transfer
-- Получение перевода по id с полными данными связанных транзакций
SELECT
    tf.id, tf.user_id, tf.from_account_id, tf.to_account_id,
    tf.amount, tf.currency, tf.transaction_datetime, tf.description,
    ft.id AS from_transaction_id, ft.amount AS from_transaction_amount,
    ft.type AS from_transaction_type, ft.transfer_leg AS from_transfer_leg,
    tt.id AS to_transaction_id, tt.amount AS to_transaction_amount,
    tt.type AS to_transaction_type, tt.transfer_leg AS to_transfer_leg
FROM transfers tf
LEFT JOIN transactions ft ON ft.transfer_id = tf.id AND ft.transfer_leg = 'debit'
LEFT JOIN transactions tt ON tt.transfer_id = tf.id AND tt.transfer_leg = 'credit'
WHERE tf.id = %(transfer_id)s;

-- name: insert_transfer
-- Создание перевода (без транзакций — они создаются отдельно в сервисе)
INSERT INTO transfers (id, user_id, from_account_id, to_account_id, amount, currency, transaction_datetime, description)
VALUES (gen_random_uuid(), %(user_id)s, %(from_account_id)s, %(to_account_id)s, %(amount)s, %(currency)s, %(transaction_datetime)s, %(description)s)
RETURNING id, user_id, from_account_id, to_account_id, amount, currency, transaction_datetime, description;

-- name: update_transfer
-- Обновление перевода
UPDATE transfers SET
    from_account_id = COALESCE(%(from_account_id)s, from_account_id),
    to_account_id = COALESCE(%(to_account_id)s, to_account_id),
    amount = COALESCE(%(amount)s, amount),
    currency = COALESCE(%(currency)s, currency),
    transaction_datetime = COALESCE(%(transaction_datetime)s, transaction_datetime),
    description = %(description)s
WHERE id = %(transfer_id)s
RETURNING id, user_id, from_account_id, to_account_id, amount, currency, transaction_datetime, description;

-- name: delete_transfer
-- Удаление перевода
DELETE FROM transfers WHERE id = %(transfer_id)s;

-- name: find_transfer_linked_transactions
-- Получение ID связанных транзакций перевода
SELECT id, transfer_leg FROM transactions WHERE transfer_id = %(transfer_id)s;

-- name: delete_transfer_transactions
-- Удаление связанных транзакций перевода
DELETE FROM transactions WHERE transfer_id = %(transfer_id)s;
