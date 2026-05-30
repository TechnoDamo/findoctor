-- name: list_liability_payments
-- Список платежей по обязательствам с фильтрацией
SELECT id, user_id, liability_id, transaction_id, recurring_transaction_id,
       payment_date, total_amount, principal_amount, interest_amount,
       fee_amount, currency, balance_after_payment, created_at
FROM liability_payments
WHERE user_id = %(user_id)s
  AND (%(liability_id)s::uuid IS NULL OR liability_id = %(liability_id)s::uuid)
  AND (%(from)s::timestamptz IS NULL OR payment_date >= %(from)s)
  AND (%(to)s::timestamptz IS NULL OR payment_date <= %(to)s)
ORDER BY payment_date DESC;

-- name: find_liability_payment
-- Получение платежа по id
SELECT id, user_id, liability_id, transaction_id, recurring_transaction_id,
       payment_date, total_amount, principal_amount, interest_amount,
       fee_amount, currency, balance_after_payment, created_at
FROM liability_payments
WHERE id = %(liability_payment_id)s
  AND user_id = %(user_id)s;

-- name: insert_liability_payment
-- Создание платежа по обязательству
INSERT INTO liability_payments (id, user_id, liability_id, transaction_id, recurring_transaction_id,
    payment_date, total_amount, principal_amount, interest_amount,
    fee_amount, currency, balance_after_payment, created_at)
VALUES (gen_random_uuid(), %(user_id)s, %(liability_id)s, %(transaction_id)s, %(recurring_transaction_id)s,
    %(payment_date)s, %(total_amount)s, %(principal_amount)s, %(interest_amount)s,
    %(fee_amount)s, %(currency)s, %(balance_after_payment)s, now())
RETURNING id, user_id, liability_id, transaction_id, recurring_transaction_id,
    payment_date, total_amount, principal_amount, interest_amount,
    fee_amount, currency, balance_after_payment, created_at;

-- name: update_liability_payment
-- Обновление платежа
UPDATE liability_payments SET
    recurring_transaction_id = COALESCE(%(recurring_transaction_id)s::uuid, recurring_transaction_id),
    payment_date = COALESCE(%(payment_date)s, payment_date),
    total_amount = COALESCE(%(total_amount)s, total_amount),
    principal_amount = COALESCE(%(principal_amount)s::numeric, principal_amount),
    interest_amount = COALESCE(%(interest_amount)s::numeric, interest_amount),
    fee_amount = COALESCE(%(fee_amount)s::numeric, fee_amount),
    currency = COALESCE(%(currency)s, currency),
    balance_after_payment = COALESCE(%(balance_after_payment)s::numeric, balance_after_payment)
WHERE id = %(liability_payment_id)s
  AND user_id = %(user_id)s
RETURNING id, user_id, liability_id, transaction_id, recurring_transaction_id,
    payment_date, total_amount, principal_amount, interest_amount,
    fee_amount, currency, balance_after_payment, created_at;

-- name: delete_liability_payment
-- Удаление платежа
DELETE FROM liability_payments
WHERE id = %(liability_payment_id)s
  AND user_id = %(user_id)s;
