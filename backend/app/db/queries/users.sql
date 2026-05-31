-- name: find_user_by_id
-- Получение профиля пользователя
SELECT id, email, phone, first_name, last_name, country, base_currency, timezone, role, created_at, updated_at
FROM users WHERE id = %(user_id)s;

-- name: update_user
-- Обновление профиля пользователя
UPDATE users SET
    phone = COALESCE(%(phone)s, phone),
    first_name = COALESCE(%(first_name)s, first_name),
    last_name = COALESCE(%(last_name)s, last_name),
    country = COALESCE(%(country)s, country),
    base_currency = COALESCE(%(base_currency)s, base_currency),
    timezone = COALESCE(%(timezone)s, timezone),
    updated_at = now()
WHERE id = %(user_id)s
RETURNING id, email, phone, first_name, last_name, country, base_currency, timezone, role, created_at, updated_at;
