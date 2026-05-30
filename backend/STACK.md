# Backend-стек ФинДоктора

Документ фиксирует инженерные правила backend-части. Его цель простая: любой разработчик должен быстро понять, где лежит бизнес-логика, где проходят транзакционные границы, как устроен доступ к данным и какие проверки обязательны перед сдачей проекта.

## Кратко

- Runtime: Python 3.12+
- Web framework: FastAPI
- ASGI server: Uvicorn
- Database: PostgreSQL
- Миграции: Alembic
- Доступ к БД: `psycopg` 3 и явный SQL
- Валидация: Pydantic v2
- Настройки: `pydantic-settings`
- Управление зависимостями: `uv`
- Тесты: pytest + httpx + реальная PostgreSQL test DB
- Линтинг: Ruff
- AI/voice: OpenAI-compatible HTTP providers
- Recommendation layer: planner -> tools -> finalizer, RAGFlow/SearXNG/TEI как опциональные сервисы

## Слои

```text
FastAPI route
  -> service/use-case
    -> repository
      -> named SQL file
        -> PostgreSQL
```

`api/routes` отвечает только за HTTP: параметры, зависимости, статус-коды и response model.

`services` содержит сценарии приложения: транзакционные границы, согласованное создание нескольких сущностей, проверки бизнес-инвариантов.

`repositories` содержит тонкие функции вокруг SQL. Репозиторий не должен знать про HTTP и не должен самостоятельно коммитить транзакции.

`db/queries/*.sql` содержит именованные SQL-запросы. Большие запросы хранятся в SQL-файлах, чтобы ревью было прозрачным.

`schemas` содержит Pydantic-модели входа и выхода API.

## Правила доступа к данным

Финансовые данные всегда принадлежат пользователю. Поэтому все пользовательские object-level операции должны быть user-scoped:

```sql
WHERE id = %(resource_id)s
  AND user_id = %(user_id)s
```

Это касается `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` и вложенных операций вроде тегов транзакции. Чужой ресурс должен выглядеть как отсутствующий ресурс: возвращаем `404`, а не раскрываем факт существования.

Для сущностей без прямого `user_id` проверка идет через родительскую сущность. Например, тег транзакции можно привязать только если и транзакция, и тег принадлежат текущему пользователю.

Backend принимает только bearer access token для защищенных API. Пароли не передаются в заголовках после логина и не используются как shortcut-аутентификация.

## Транзакции

Транзакции открываются на уровне service/use-case. Хороший пример — перевод:

1. Проверить, что оба счета принадлежат пользователю.
2. Создать `transfers`.
3. Создать debit transaction.
4. Создать credit transaction.
5. Вернуть единый объект перевода.

Все это должно быть атомарным:

```python
async with conn.transaction():
    ...
```

Репозитории выполняют SQL на переданном соединении и не вызывают commit/rollback самостоятельно.

## SQL и миграции

Правила:

- любое изменение структуры БД оформляется Alembic-миграцией;
- `db/schema.dbml` обновляется вместе с миграцией;
- SQL должен быть параметризованным, без конкатенации пользовательского ввода;
- derived/read-model таблицы не являются источником истины;
- аналитические агрегаты считаются отдельными CTE/подзапросами, чтобы не умножать суммы на join-кардинальности.

## Конфигурация и безопасность

Production startup должен падать на небезопасных настройках:

- `JWT_SECRET_KEY=change_me_in_production`;
- дефолтный пароль БД без `DATABASE_URL`;
- `APP_DEBUG=true`;
- включенное подробное логирование HTTP headers/bodies.

По умолчанию backend не логирует HTTP headers, request bodies и response bodies. Если подробное логирование включено для локальной диагностики, middleware редактирует чувствительные поля: `authorization`, `cookie`, `password`, `access_token`, `refresh_token`, `api_key`, аудио/base64 payloads.

Если `RECOMMENDATIONS_ENABLED=true`, backend валидирует обязательные параметры RAG/search-контура при старте.

## Тестовый стандарт

Минимальный gate перед сдачей:

```bash
cd backend
./.venv/bin/python -m compileall -q app tests scripts
./.venv/bin/ruff check app tests scripts
./.venv/bin/pytest tests/ -q
```

Для frontend/dependency scanner:

```bash
cd frontend
npm audit --audit-level=moderate
npm run build
```

Важные группы тестов:

- auth/session lifecycle;
- CRUD финансовых сущностей;
- transfer lifecycle с двумя связанными транзакциями;
- AI chat и conversation ownership;
- OpenAPI contract parity;
- cross-user authorization boundaries.

## AI и рекомендации

AI chat поддерживает обычный LLM-ответ и agentic flow. Recommendation flow работает так:

```text
user question
  -> planner JSON
  -> allowed tools: user_data, RAGFlow, SearXNG
  -> finalizer answer
  -> tool_results for transparency
```

Инструменты выполняются backend-ом, а не моделью напрямую. Это важно для безопасности: модель планирует, backend разрешает только известные операции и применяет allowlist источников.

## Что не делаем

- Не используем ORM для прикладной персистентности.
- Не храним пароли в открытом виде.
- Не логируем токены, пароли, аудио/base64 и полные финансовые payloads.
- Не возвращаем чужие пользовательские ресурсы даже при знании UUID.
- Не делаем внешние сетевые вызовы внутри длинных БД-транзакций без явной причины.
