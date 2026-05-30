-- name: list_assets
-- Список активов пользователя с фильтрацией по типу
SELECT id, user_id, asset_type_id, name, estimated_value, currency,
       purchase_price, purchase_date, monthly_cost, created_at, updated_at
FROM assets
WHERE user_id = %(user_id)s
  AND (%(asset_type_id)s IS NULL OR asset_type_id = %(asset_type_id)s)
ORDER BY name;

-- name: find_asset
-- Получение актива по id
SELECT id, user_id, asset_type_id, name, estimated_value, currency,
       purchase_price, purchase_date, monthly_cost, created_at, updated_at
FROM assets WHERE id = %(asset_id)s;

-- name: insert_asset
-- Создание актива
INSERT INTO assets (id, user_id, asset_type_id, name, estimated_value, currency,
    purchase_price, purchase_date, monthly_cost, created_at, updated_at)
VALUES (gen_random_uuid(), %(user_id)s, %(asset_type_id)s, %(name)s,
    %(estimated_value)s, %(currency)s, %(purchase_price)s,
    %(purchase_date)s, %(monthly_cost)s, now(), now())
RETURNING id, user_id, asset_type_id, name, estimated_value, currency,
    purchase_price, purchase_date, monthly_cost, created_at, updated_at;

-- name: update_asset
-- Обновление актива
UPDATE assets SET
    asset_type_id = COALESCE(%(asset_type_id)s, asset_type_id),
    name = COALESCE(%(name)s, name),
    estimated_value = COALESCE(%(estimated_value)s, estimated_value),
    currency = COALESCE(%(currency)s, currency),
    purchase_price = COALESCE(%(purchase_price)s::numeric, purchase_price),
    purchase_date = COALESCE(%(purchase_date)s::date, purchase_date),
    monthly_cost = COALESCE(%(monthly_cost)s::numeric, monthly_cost),
    updated_at = now()
WHERE id = %(asset_id)s
RETURNING id, user_id, asset_type_id, name, estimated_value, currency,
    purchase_price, purchase_date, monthly_cost, created_at, updated_at;

-- name: delete_asset
-- Удаление актива
DELETE FROM assets WHERE id = %(asset_id)s;
