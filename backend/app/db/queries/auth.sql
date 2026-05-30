-- name: insert_user
-- Регистрация нового пользователя
INSERT INTO users (id, email, password_hash, phone, first_name, last_name, country, base_currency, timezone, created_at, updated_at)
VALUES (gen_random_uuid(), %(email)s, %(password_hash)s, %(phone)s, %(first_name)s, %(last_name)s, %(country)s, %(base_currency)s, %(timezone)s, now(), now())
RETURNING id, email, phone, first_name, last_name, country, base_currency, timezone, role, created_at, updated_at;

-- name: find_user_by_email
-- Поиск пользователя по email (возвращает все поля включая password_hash для проверки)
SELECT id, email, password_hash, phone, first_name, last_name, country, base_currency, timezone, role, created_at, updated_at
FROM users WHERE email = %(email)s;

-- name: find_user_by_id
-- Поиск пользователя по id (без password_hash)
SELECT id, email, phone, first_name, last_name, country, base_currency, timezone, role, created_at, updated_at
FROM users WHERE id = %(user_id)s;

-- name: insert_session
-- Создание сессии при логине (сохраняет хеш refresh-токена)
INSERT INTO auth_sessions (id, user_id, refresh_token_hash, expires_at, created_at)
VALUES (gen_random_uuid(), %(user_id)s, %(refresh_token_hash)s, %(expires_at)s, now())
RETURNING id, user_id, expires_at, created_at;

-- name: find_session_by_hash
-- Поиск сессии по хешу refresh-токена
SELECT id, user_id, refresh_token_hash, expires_at, created_at
FROM auth_sessions WHERE refresh_token_hash = %(token_hash)s AND expires_at > now();

-- name: find_session_by_id
-- Поиск активной сессии по id из access-токена
SELECT id, user_id, refresh_token_hash, expires_at, created_at
FROM auth_sessions WHERE id = %(session_id)s AND expires_at > now();

-- name: delete_session
-- Удаление сессии (logout)
DELETE FROM auth_sessions WHERE refresh_token_hash = %(token_hash)s;

-- name: delete_session_by_id
-- Удаление сессии по id из access-токена
DELETE FROM auth_sessions WHERE id = %(session_id)s;

-- name: delete_user_sessions
-- Удаление всех сессий пользователя (принудительный выход со всех устройств)
DELETE FROM auth_sessions WHERE user_id = %(user_id)s;
