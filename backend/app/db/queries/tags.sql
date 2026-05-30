-- name: list_tags
-- Список тегов пользователя
SELECT id, user_id, name FROM tags WHERE user_id = %(user_id)s ORDER BY name;

-- name: find_tag
-- Поиск тега по id
SELECT id, user_id, name FROM tags WHERE id = %(tag_id)s;

-- name: insert_tag
-- Создание тега
INSERT INTO tags (id, user_id, name)
VALUES (gen_random_uuid(), %(user_id)s, %(name)s)
RETURNING id, user_id, name;

-- name: update_tag
-- Обновление тега
UPDATE tags SET name = %(name)s WHERE id = %(tag_id)s
RETURNING id, user_id, name;

-- name: delete_tag
-- Удаление тега
DELETE FROM tags WHERE id = %(tag_id)s;

-- name: list_transaction_tags
-- Получение списка тегов транзакции
SELECT tg.id, tg.user_id, tg.name
FROM transaction_tags tt
JOIN tags tg ON tt.tag_id = tg.id
WHERE tt.transaction_id = %(transaction_id)s
ORDER BY tg.name;

-- name: delete_transaction_tags
-- Удаление всех тегов транзакции (для массовой замены)
DELETE FROM transaction_tags WHERE transaction_id = %(transaction_id)s;

-- name: insert_transaction_tag
-- Прикрепление тега к транзакции
INSERT INTO transaction_tags (transaction_id, tag_id)
VALUES (%(transaction_id)s, %(tag_id)s)
ON CONFLICT DO NOTHING;

-- name: delete_transaction_tag
-- Открепление тега от транзакции
DELETE FROM transaction_tags WHERE transaction_id = %(transaction_id)s AND tag_id = %(tag_id)s;
