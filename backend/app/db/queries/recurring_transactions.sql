-- name: list_recurring_transactions
-- Список регулярных операций пользователя с фильтрацией
SELECT id, user_id, account_id, category_id, liability_id,
       operation_type, name, expected_amount, currency,
       frequency, interval_count, day_of_month,
       start_date, end_date, next_payment_date,
       auto_generated, confidence_score, is_active
FROM recurring_transactions
WHERE user_id = %(user_id)s
  AND (%(is_active)s::boolean IS NULL OR is_active = %(is_active)s::boolean)
  AND (%(account_id)s::uuid IS NULL OR account_id = %(account_id)s::uuid)
  AND (%(liability_id)s::uuid IS NULL OR liability_id = %(liability_id)s::uuid)
  AND (%(next_payment_before)s::date IS NULL OR next_payment_date <= %(next_payment_before)s)
ORDER BY next_payment_date ASC NULLS LAST;

-- name: find_recurring_transaction
-- Получение регулярной операции по id
SELECT id, user_id, account_id, category_id, liability_id,
       operation_type, name, expected_amount, currency,
       frequency, interval_count, day_of_month,
       start_date, end_date, next_payment_date,
       auto_generated, confidence_score, is_active
FROM recurring_transactions
WHERE id = %(recurring_transaction_id)s
  AND user_id = %(user_id)s;

-- name: insert_recurring_transaction
-- Создание регулярной операции
INSERT INTO recurring_transactions (id, user_id, account_id, category_id, liability_id,
    operation_type, name, expected_amount, currency,
    frequency, interval_count, day_of_month,
    start_date, end_date, next_payment_date,
    auto_generated, confidence_score, is_active)
VALUES (gen_random_uuid(), %(user_id)s, %(account_id)s, %(category_id)s, %(liability_id)s,
    %(operation_type)s, %(name)s, %(expected_amount)s, %(currency)s,
    %(frequency)s, %(interval_count)s, %(day_of_month)s,
    %(start_date)s, %(end_date)s, %(next_payment_date)s,
    false, NULL, true)
RETURNING id, user_id, account_id, category_id, liability_id,
    operation_type, name, expected_amount, currency,
    frequency, interval_count, day_of_month,
    start_date, end_date, next_payment_date,
    auto_generated, confidence_score, is_active;

-- name: update_recurring_transaction
-- Обновление регулярной операции
UPDATE recurring_transactions SET
    account_id = COALESCE(%(account_id)s, account_id),
    category_id = COALESCE(%(category_id)s::uuid, category_id),
    liability_id = COALESCE(%(liability_id)s::uuid, liability_id),
    operation_type = COALESCE(%(operation_type)s, operation_type),
    name = COALESCE(%(name)s, name),
    expected_amount = COALESCE(%(expected_amount)s::numeric, expected_amount),
    currency = COALESCE(%(currency)s::varchar, currency),
    frequency = COALESCE(%(frequency)s, frequency),
    interval_count = COALESCE(%(interval_count)s, interval_count),
    day_of_month = COALESCE(%(day_of_month)s, day_of_month),
    start_date = COALESCE(%(start_date)s::date, start_date),
    end_date = COALESCE(%(end_date)s::date, end_date),
    next_payment_date = COALESCE(%(next_payment_date)s::date, next_payment_date),
    is_active = COALESCE(%(is_active)s, is_active)
WHERE id = %(recurring_transaction_id)s
  AND user_id = %(user_id)s
RETURNING id, user_id, account_id, category_id, liability_id,
    operation_type, name, expected_amount, currency,
    frequency, interval_count, day_of_month,
    start_date, end_date, next_payment_date,
    auto_generated, confidence_score, is_active;

-- name: deactivate_recurring_transaction
-- Деактивация регулярной операции
UPDATE recurring_transactions SET is_active = false
WHERE id = %(recurring_transaction_id)s
  AND user_id = %(user_id)s;
