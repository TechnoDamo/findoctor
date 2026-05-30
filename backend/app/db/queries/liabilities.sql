-- name: list_liabilities
-- Список обязательств пользователя с фильтрацией
SELECT id, user_id, liability_type_id, linked_account_id, collateral_asset_id,
       name, creditor_institution_id, creditor_name,
       original_amount, current_balance, currency,
       interest_rate, interest_type,
       minimum_payment_amount, regular_payment_amount,
       payment_due_day, start_date, maturity_date,
       status, created_at, updated_at
FROM liabilities
WHERE user_id = %(user_id)s
  AND (%(status)s::liability_status IS NULL OR status = %(status)s::liability_status)
  AND (%(liability_type_id)s::uuid IS NULL OR liability_type_id = %(liability_type_id)s::uuid)
ORDER BY name;

-- name: find_liability
-- Получение обязательства по id
SELECT id, user_id, liability_type_id, linked_account_id, collateral_asset_id,
       name, creditor_institution_id, creditor_name,
       original_amount, current_balance, currency,
       interest_rate, interest_type,
       minimum_payment_amount, regular_payment_amount,
       payment_due_day, start_date, maturity_date,
       status, created_at, updated_at
FROM liabilities WHERE id = %(liability_id)s;

-- name: insert_liability
-- Создание обязательства
INSERT INTO liabilities (id, user_id, liability_type_id, linked_account_id, collateral_asset_id,
    name, creditor_institution_id, creditor_name,
    original_amount, current_balance, currency,
    interest_rate, interest_type,
    minimum_payment_amount, regular_payment_amount,
    payment_due_day, start_date, maturity_date,
    status, created_at, updated_at)
VALUES (gen_random_uuid(), %(user_id)s, %(liability_type_id)s, %(linked_account_id)s,
    %(collateral_asset_id)s, %(name)s, %(creditor_institution_id)s,
    %(creditor_name)s, %(original_amount)s, %(current_balance)s,
    %(currency)s, %(interest_rate)s, %(interest_type)s,
    %(minimum_payment_amount)s, %(regular_payment_amount)s,
    %(payment_due_day)s, %(start_date)s, %(maturity_date)s,
    'active', now(), now())
RETURNING id, user_id, liability_type_id, linked_account_id, collateral_asset_id,
    name, creditor_institution_id, creditor_name,
    original_amount, current_balance, currency,
    interest_rate, interest_type,
    minimum_payment_amount, regular_payment_amount,
    payment_due_day, start_date, maturity_date,
    status, created_at, updated_at;

-- name: update_liability
-- Обновление обязательства
UPDATE liabilities SET
    liability_type_id = COALESCE(%(liability_type_id)s, liability_type_id),
    linked_account_id = COALESCE(%(linked_account_id)s::uuid, linked_account_id),
    collateral_asset_id = COALESCE(%(collateral_asset_id)s::uuid, collateral_asset_id),
    name = COALESCE(%(name)s, name),
    creditor_institution_id = COALESCE(%(creditor_institution_id)s::uuid, creditor_institution_id),
    creditor_name = COALESCE(%(creditor_name)s::varchar, creditor_name),
    original_amount = COALESCE(%(original_amount)s::numeric, original_amount),
    current_balance = COALESCE(%(current_balance)s, current_balance),
    currency = COALESCE(%(currency)s, currency),
    interest_rate = COALESCE(%(interest_rate)s, interest_rate),
    interest_type = COALESCE(%(interest_type)s::interest_type, interest_type),
    minimum_payment_amount = COALESCE(%(minimum_payment_amount)s::numeric, minimum_payment_amount),
    regular_payment_amount = COALESCE(%(regular_payment_amount)s::numeric, regular_payment_amount),
    payment_due_day = COALESCE(%(payment_due_day)s, payment_due_day),
    start_date = COALESCE(%(start_date)s::date, start_date),
    maturity_date = COALESCE(%(maturity_date)s::date, maturity_date),
    status = COALESCE(%(status)s, status),
    updated_at = now()
WHERE id = %(liability_id)s
RETURNING id, user_id, liability_type_id, linked_account_id, collateral_asset_id,
    name, creditor_institution_id, creditor_name,
    original_amount, current_balance, currency,
    interest_rate, interest_type,
    minimum_payment_amount, regular_payment_amount,
    payment_due_day, start_date, maturity_date,
    status, created_at, updated_at;

-- name: close_liability
-- Закрытие обязательства
UPDATE liabilities SET status = 'closed', updated_at = now()
WHERE id = %(liability_id)s
RETURNING id, user_id, liability_type_id, linked_account_id, collateral_asset_id,
    name, creditor_institution_id, creditor_name,
    original_amount, current_balance, currency,
    interest_rate, interest_type,
    minimum_payment_amount, regular_payment_amount,
    payment_due_day, start_date, maturity_date,
    status, created_at, updated_at;
