-- name: list_conversations
-- Список диалогов пользователя с пагинацией
SELECT
    c.id, c.user_id, c.title,
    (SELECT m.content->0->>'text' FROM ai_chat_messages m
     WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message_preview,
    c.created_at, c.updated_at
FROM ai_chat_conversations c
WHERE c.user_id = %(user_id)s
ORDER BY c.updated_at DESC
LIMIT %(page_size)s OFFSET %(offset)s;

-- name: count_conversations
-- Подсчёт диалогов для пагинации
SELECT COUNT(*) AS total FROM ai_chat_conversations WHERE user_id = %(user_id)s;

-- name: find_conversation
-- Получение диалога по id с сообщениями
SELECT id, user_id, title, created_at, updated_at
FROM ai_chat_conversations WHERE id = %(conversation_id)s;

-- name: insert_conversation
-- Создание нового диалога
INSERT INTO ai_chat_conversations (id, user_id, title, created_at, updated_at)
VALUES (gen_random_uuid(), %(user_id)s, %(title)s, now(), now())
RETURNING id, user_id, title, created_at, updated_at;

-- name: update_conversation
-- Обновление заголовка диалога
UPDATE ai_chat_conversations SET title = %(title)s, updated_at = now()
WHERE id = %(conversation_id)s
RETURNING id, user_id, title, created_at, updated_at;

-- name: delete_conversation
-- Удаление диалога и всех его сообщений (каскадно)
DELETE FROM ai_chat_conversations WHERE id = %(conversation_id)s;

-- name: list_messages
-- Список сообщений диалога
SELECT id, conversation_id, role, content, metadata, created_at
FROM ai_chat_messages
WHERE conversation_id = %(conversation_id)s
ORDER BY created_at;

-- name: insert_message
-- Добавление сообщения в диалог
INSERT INTO ai_chat_messages (id, conversation_id, role, content, metadata, created_at)
VALUES (gen_random_uuid(), %(conversation_id)s, %(role)s, %(content)s, %(metadata)s, now())
RETURNING id, conversation_id, role, content, metadata, created_at;

-- name: touch_conversation
-- Обновление времени последнего изменения диалога
UPDATE ai_chat_conversations SET updated_at = now() WHERE id = %(conversation_id)s;
