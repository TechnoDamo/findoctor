-- name: list_accounts
-- Список счетов пользователя с фильтрацией
SELECT id, user_id, account_type_id, institution_id, name, institution_name,
       currency, balance, is_active, created_at, updated_at
FROM accounts
WHERE user_id = %(user_id)s
  AND (%(is_active)s::boolean IS NULL OR is_active = %(is_active)s::boolean)
  AND (%(account_type_id)s::uuid IS NULL OR account_type_id = %(account_type_id)s::uuid)
  AND (%(institution_id)s::uuid IS NULL OR institution_id = %(institution_id)s::uuid)
  AND (%(currency)s::varchar IS NULL OR currency = %(currency)s::varchar)
ORDER BY name;

-- name: find_account
-- Получение счёта по id
SELECT id, user_id, account_type_id, institution_id, name, institution_name,
       currency, balance, is_active, created_at, updated_at
FROM accounts WHERE id = %(account_id)s;

-- name: insert_account
-- Создание нового счёта
INSERT INTO accounts (id, user_id, account_type_id, institution_id, name, institution_name, currency, balance, is_active, created_at, updated_at)
VALUES (gen_random_uuid(), %(user_id)s, %(account_type_id)s, %(institution_id)s, %(name)s, %(institution_name)s, %(currency)s, %(opening_balance)s, true, now(), now())
RETURNING id, user_id, account_type_id, institution_id, name, institution_name, currency, balance, is_active, created_at, updated_at;

-- name: update_account
-- Обновление счёта
UPDATE accounts SET
    account_type_id = COALESCE(%(account_type_id)s, account_type_id),
    institution_id = COALESCE(%(institution_id)s::uuid, institution_id),
    name = COALESCE(%(name)s, name),
    institution_name = COALESCE(%(institution_name)s::varchar, institution_name),
    currency = COALESCE(%(currency)s, currency),
    balance = COALESCE(%(balance)s, balance),
    is_active = COALESCE(%(is_active)s, is_active),
    updated_at = now()
WHERE id = %(account_id)s
RETURNING id, user_id, account_type_id, institution_id, name, institution_name, currency, balance, is_active, created_at, updated_at;

-- name: archive_account
-- Архивация счёта (вместо удаления — сохраняем историю)
UPDATE accounts SET is_active = false, updated_at = now()
WHERE id = %(account_id)s
RETURNING id, user_id, account_type_id, institution_id, name, institution_name, currency, balance, is_active, created_at, updated_at;
