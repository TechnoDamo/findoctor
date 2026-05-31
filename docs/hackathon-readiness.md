# Хакатонная Готовность ПрофИИта

Этот документ помогает быстро проверить проект перед сдачей, подготовить честный демо-сценарий и показать архитектуру так, чтобы она выглядела как цельный продукт, а не набор сервисов.

## Что Уже Сильно

- Реальная финансовая доменная модель: счета, операции, переводы, активы, обязательства, цели, регулярные платежи, теги.
- PostgreSQL schema + Alembic migrations + DBML-документация.
- FastAPI backend с OpenAPI-контрактом.
- Явный SQL без ORM для прикладной персистентности.
- JWT/session auth с refresh-token hash в БД.
- User-scoped доступ к пользовательским ресурсам: чужой UUID возвращает `404`.
- Полный backend test suite на реальной PostgreSQL test DB.
- AI chat с conversation history.
- Agentic recommendation flow: planner -> user_data/RAG/search tools -> finalizer.
- Отдельный продуктовый endpoint `POST /api/v1/recommendations?type=...` для доходов, расходов, кредитного светофора, оценки кредита и общего финансового портрета.
- Опциональный self-hosted RAG/search/embedding контур: RAGFlow, SearXNG, TEI.
- Frontend production build проходит.
- `npm audit --audit-level=moderate` проходит без findings.

## Главный Демо-Сценарий

Лучше показывать не весь CRUD, а один законченный финансовый путь:

1. Пользователь входит в систему.
2. В БД уже загружен реалистичный сценарий из `db/tests/seed_test_users.sql`.
3. Backend показывает счета, операции, активы, обязательства и аналитику.
4. Пользователь спрашивает AI: "Можно ли мне досрочно погасить часть кредита без риска для подушки?"
5. AI вызывает user-data tool, при необходимости RAG/search, и возвращает рекомендацию с аргументами.
6. В ответе показываются `tool_results`, чтобы было видно: это не generic chatbot, а ассистент поверх финансового контекста.
7. Для продуктового сценария можно вызвать `POST /api/v1/recommendations?type=credit_decision` с параметрами кредита и показать готовые поля `status`, `analysis`, `advice`, `facts`.

## Команды Перед Сдачей

```bash
cd backend
./.venv/bin/python -m compileall -q app tests scripts
./.venv/bin/ruff check app tests scripts
./.venv/bin/pytest tests/ -q

cd ../frontend
npm audit --audit-level=moderate
npm run build
```

Дополнительно для recommendation-стека:

```bash
make recommendations-test
make backend-test-recommendations
```

## Что Говорить Судьям

Короткая формулировка:

> ПрофИИт — это персональный финансовый ассистент, который соединяет учет личных финансов, аналитику и AI-рекомендации. В отличие от обычного чат-бота, он работает поверх структурированных пользовательских данных и может подкреплять советы внутренними расчетами, RAG-документами и контролируемым поиском.

Технический акцент:

- backend не доверяет модели напрямую;
- модель планирует инструменты, backend выполняет только разрешенные операции;
- финансовые данные изолированы по `user_id`;
- OpenAPI-контракт держит API surface стабильным;
- тесты проверяют не только happy path, но и cross-user boundaries.

## Что Честно Называть Ограничениями

- Production deployment всего AI/RAG-стека требует выбранной инфраструктуры и секретов.
- Фоновые пересчеты daily snapshots пока оформлены API-контуром, но полноценный worker нужно добавить отдельно.
- Frontend уже собирается, но часть dashboard UX остается демонстрационной и должна дальше связываться с live API-данными.
- Финансовые рекомендации являются информационной аналитикой, не юридической или инвестиционной консультацией.

## Минимальный Чеклист Готовности

- [ ] `.env` заполнен без дефолтных production-секретов.
- [ ] Backend tests проходят.
- [ ] OpenAPI contract test проходит.
- [ ] `npm audit --audit-level=moderate` проходит.
- [ ] Frontend production build проходит.
- [ ] Есть подготовленный пользовательский сценарий.
- [ ] RAGFlow/SearXNG/TEI либо запущены и проверены, либо рекомендации отключены.
- [ ] Демо-вопрос к AI заранее проверен.
- [ ] В логах нет паролей, токенов, audio/base64 payloads.

## Репозиторный Сигнал Для Проверяющих

Если проверяющий смотрит код, главные места:

- `backend/app/api/dependencies.py` — bearer auth.
- `backend/app/db/queries/*.sql` — user-scoped SQL.
- `backend/tests/test_authorization_boundaries.py` — cross-user isolation.
- `backend/app/services/recommendations/orchestrator.py` — planner/tools/finalizer.
- `backend/app/api/routes/recommendations.py` и `backend/app/services/product_recommendations.py` — продуктовый endpoint рекомендаций поверх того же AI-пайплайна.
- `docs/architecture-uml.md` — архитектура, deployment-комбинации и sequence diagrams.
- `backend/STACK.md` — backend engineering rules.
- `backend/TESTING.md` — test gate и правила покрытия.
