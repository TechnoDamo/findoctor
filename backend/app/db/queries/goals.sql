-- name: list_goals
-- Список финансовых целей пользователя
SELECT id, user_id, name, target_amount, current_amount, deadline, priority, created_at, updated_at
FROM financial_goals
WHERE user_id = %(user_id)s
ORDER BY COALESCE(priority, 999), deadline ASC NULLS LAST, created_at DESC;

-- name: find_goal
-- Получение цели по id
SELECT id, user_id, name, target_amount, current_amount, deadline, priority, created_at, updated_at
FROM financial_goals WHERE id = %(goal_id)s;

-- name: insert_goal
-- Создание финансовой цели
INSERT INTO financial_goals (id, user_id, name, target_amount, current_amount, deadline, priority, created_at, updated_at)
VALUES (gen_random_uuid(), %(user_id)s, %(name)s, %(target_amount)s, %(current_amount)s, %(deadline)s, %(priority)s, now(), now())
RETURNING id, user_id, name, target_amount, current_amount, deadline, priority, created_at, updated_at;

-- name: update_goal
-- Обновление цели
UPDATE financial_goals SET
    name = COALESCE(%(name)s, name),
    target_amount = COALESCE(%(target_amount)s, target_amount),
    current_amount = COALESCE(%(current_amount)s, current_amount),
    deadline = COALESCE(%(deadline)s::date, deadline),
    priority = COALESCE(%(priority)s, priority),
    updated_at = now()
WHERE id = %(goal_id)s
RETURNING id, user_id, name, target_amount, current_amount, deadline, priority, created_at, updated_at;

-- name: delete_goal
-- Удаление цели
DELETE FROM financial_goals WHERE id = %(goal_id)s;
