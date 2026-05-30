-- name: list_account_types
-- Список всех типов счетов
SELECT id, code, name, description FROM account_types ORDER BY name;

-- name: list_asset_types
-- Список всех типов активов
SELECT id, code, name, description FROM asset_types ORDER BY name;

-- name: list_liability_types
-- Список всех типов обязательств
SELECT id, code, name, description, is_secured FROM liability_types ORDER BY name;

-- name: list_provider_types
-- Список всех типов финансовых провайдеров
SELECT id, code, name, description FROM provider_types ORDER BY name;

-- name: list_categories
-- Список категорий (фильтрация по типу и родителю)
SELECT id, parent_id, type, name, description
FROM categories
WHERE (%(type)s IS NULL OR type = %(type)s)
  AND (%(parent_id)s IS NULL OR parent_id = %(parent_id)s)
ORDER BY name;

-- name: find_category
-- Поиск категории по id
SELECT id, parent_id, type, name, description FROM categories WHERE id = %(category_id)s;

-- name: insert_category
-- Создание новой категории
INSERT INTO categories (id, parent_id, type, name, description)
VALUES (gen_random_uuid(), %(parent_id)s, %(type)s, %(name)s, %(description)s)
RETURNING id, parent_id, type, name, description;

-- name: update_category
-- Обновление категории
UPDATE categories SET
    parent_id = %(parent_id)s,
    type = %(type)s,
    name = %(name)s,
    description = %(description)s
WHERE id = %(category_id)s
RETURNING id, parent_id, type, name, description;

-- name: delete_category
-- Удаление категории
DELETE FROM categories WHERE id = %(category_id)s;

-- name: list_merchants
-- Поиск продавцов по названию, стране и уровню риска
SELECT id, name, category, country, risk_level
FROM merchants
WHERE (%(q)s IS NULL OR name ILIKE %(q_like)s)
  AND (%(country)s IS NULL OR country = %(country)s)
  AND (%(risk_level)s IS NULL OR risk_level = %(risk_level)s)
ORDER BY name;

-- name: find_merchant
-- Поиск продавца по id
SELECT id, name, category, country, risk_level FROM merchants WHERE id = %(merchant_id)s;

-- name: insert_merchant
-- Добавление продавца
INSERT INTO merchants (id, name, category, country, risk_level)
VALUES (gen_random_uuid(), %(name)s, %(category)s, %(country)s, %(risk_level)s)
RETURNING id, name, category, country, risk_level;

-- name: update_merchant
-- Обновление данных продавца
UPDATE merchants SET
    name = %(name)s,
    category = %(category)s,
    country = %(country)s,
    risk_level = %(risk_level)s
WHERE id = %(merchant_id)s
RETURNING id, name, category, country, risk_level;

-- name: delete_merchant
-- Удаление продавца
DELETE FROM merchants WHERE id = %(merchant_id)s;
