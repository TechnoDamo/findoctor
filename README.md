# ФинДоктор

ФинДоктор - финансовая аналитическая платформа для учета счетов, операций, переводов, активов, обязательств, целей и регулярных платежей. Проект сейчас находится на этапе проектирования ядра: база данных, миграции, OpenAPI-контракт и первые фронтенд/voice-прототипы.

## Содержание

- [Идея проекта](#идея-проекта)
- [Структура репозитория](#структура-репозитория)
- [Архитектура](#архитектура)
- [Ключевые решения](#ключевые-решения)
- [Доменная модель и функциональность](#доменная-модель-и-функциональность)
- [API](#api)
- [База данных](#база-данных)
- [Локальный запуск](#локальный-запуск)
- [Миграции](#миграции)
- [Связанные документы](#связанные-документы)
- [Текущий статус](#текущий-статус)

## Идея проекта

Цель системы - собрать личные финансовые данные пользователя в единую модель и дать поверх нее понятную аналитику: движение денег, чистый капитал, долговую нагрузку, регулярные платежи, цели и рекомендации.

Главный принцип модели: реальные движения денег хранятся в `transactions`, а счета, активы, долги, категории, теги и регулярные операции описывают контекст этих движений.

## Структура репозитория

```text
.
├── api-contract/          # OpenAPI/Swagger YAML и будущие контрактные артефакты
├── backend/               # Python/FastAPI backend, миграции Alembic, Makefile
├── db/                    # DBML-схема, описание модели, локальный PostgreSQL
├── frontend/              # фронтенд-прототип
└── voice-test/            # прототипы голосового ввода/вывода и RouterAI-тесты
```

Основные файлы:

- [`api-contract/openapi.yaml`](api-contract/openapi.yaml) - клиентский OpenAPI-контракт.
- [`db/schema.dbml`](db/schema.dbml) - схема базы данных в DBML.
- [`db/descriptions.md`](db/descriptions.md) - подробное описание таблиц и смысла модели.
- [`db/deployment.md`](db/deployment.md) - локальный запуск PostgreSQL в Docker.
- [`backend/STACK.md`](backend/STACK.md) - принятый backend-стек и инженерные правила.
- [`backend/migrations/versions/`](backend/migrations/versions/) - Alembic-миграции.

## Архитектура

Высокоуровневая схема:

```text
Фронтенд / мобильное приложение / голосовой интерфейс
        |
        | HTTP + OpenAPI contract
        v
FastAPI backend
        |
        | service/use-case layer
        v
Repositories with explicit SQL
        |
        v
PostgreSQL
```

Планируемые backend-слои:

- `api/routes` - HTTP-эндпоинты, валидация входа/выхода, OpenAPI-совместимые схемы.
- `services` - сценарии приложения и транзакционные границы.
- `repositories` - явный SQL и отображение строк БД в Python-структуры.
- `db` - пул подключений, транзакционные помощники, SQL-запросы.
- `workers` - фоновые задачи: пересчет аналитики, импорты, AI/voice processing.

## Ключевые решения

- Backend: Python 3.12+, FastAPI, Pydantic v2.
- Database: PostgreSQL.
- Миграции: Alembic.
- Доступ к БД: `psycopg` и явный SQL, без ORM для прикладной персистентности.
- Транзакции открываются на уровне service/use-case, а не внутри repository.
- OpenAPI-контракт хранится отдельно и служит источником клиентского API-дизайна.
- Аналитические таблицы являются производными данными, а не источником истины.

## Доменная модель и функциональность

### Пользователь и настройки

`users` хранит учетную запись, валюту по умолчанию, таймзону и базовые профильные данные. Клиентский API не должен отдавать или принимать `password_hash`; для этого есть отдельный auth-контур.

### Справочники

Справочные таблицы задают стабильную классификацию:

- `account_types` - типы счетов: карта, наличные, брокерский счет, криптокошелек.
- `asset_types` - типы активов: недвижимость, авто, акции, крипто, бизнес.
- `liability_types` - типы обязательств: ипотека, кредит, кредитная карта, налоговый долг.
- `provider_types` - роли финансовых провайдеров: банк, брокер, кредитор, биржа.
- `financial_institutions` - банки, брокеры, биржи, кредиторы и кошельки.
- `categories` - дерево категорий доходов и расходов.
- `merchants` - нормализованные продавцы и поставщики услуг.

### Счета и операции

`accounts` описывает места хранения или движения денег: банковские счета, карты, наличные, инвестиционные счета и кошельки.

`transactions` - главный денежный журнал. Доходы, расходы и legs переводов должны попадать сюда. Сумма хранится как положительное значение, направление задается типом операции и контекстом.

### Переводы

`transfers` - бизнес-сущность перевода между счетами пользователя. Перевод должен быть связан с двумя строками `transactions`:

- `transfer_leg = debit` - списание со счета-источника;
- `transfer_leg = credit` - зачисление на счет-получатель.

В `transactions` для этого есть `transfer_id` и `transfer_leg`. Ограничение БД требует, чтобы linked transaction имела `type = transfer`, а уникальный индекс не дает создать больше одного debit/credit leg для одного перевода.

### Регулярные операции

`recurring_transactions` хранит шаблоны ожидаемых платежей и поступлений: зарплата, аренда, подписки, коммунальные платежи, платежи по долгам. Это не реальные операции; фактическое движение денег все равно создается в `transactions`.

### Активы и обязательства

`assets` хранит имущество пользователя для расчета чистого капитала: недвижимость, автомобиль, портфель, бизнес, криптоактивы.

`liabilities` хранит долги и обязательства: кредиты, ипотеку, кредитные карты, рассрочки, налоговые долги.

`liability_payments` связывает фактический платеж из `transactions` с долгом и раскладывает платеж на тело долга, проценты и комиссии.

### Цели и теги

`financial_goals` хранит цели: накопить сумму, закрыть долг, купить актив, собрать резерв.

`tags` и `transaction_tags` дают пользовательскую разметку операций поверх системных категорий.

### Аналитика

`daily_financial_snapshots` хранит ежедневные агрегаты: кэш, активы, обязательства, чистый капитал, месячный доход, месячные расходы и savings rate. Это read model для графиков, отчетов и AI-аналитики.

### AI и голосовой интерфейс

OpenAPI-контракт уже предусматривает AI chat endpoints для текстового и голосового сценария:

- отправка текста;
- отправка аудио;
- получение текста;
- получение аудио;
- получение аудио вместе с текстом/транскриптом.

`voice-test/` содержит ранние эксперименты с записью, STT/TTS и аудиомоделями.

### Рекомендации, RAG и поиск

Рекомендационный контур добавлен как опциональный слой поверх AI-чата:

- первый LLM-вызов возвращает строгий JSON-план с `response_text` и `needed_tools`;
- backend выполняет только разрешенные инструменты: RAGFlow для RAG и SearXNG для поиска;
- источники поиска фильтруются через `ragflow/allowed_resources.txt`;
- финальный LLM-вызов отвечает уже с учетом найденных evidence chunks;
- план и evidence возвращаются в `tool_results`.

Подробная документация: [`backend/docs/recommendations.md`](backend/docs/recommendations.md).

Профили деплоя и корневые команды: [`docs/deployment.md`](docs/deployment.md).

Локальные self-hosted сервисы:

- [`ragflow/`](ragflow/) - внутренний RAGFlow-компонент для индексации и retrieval API;
- [`searxng/`](searxng/) - внутренний SearXNG для discovery по разрешенным доменам;
- [`tei/`](tei/) - локальный Hugging Face TEI embedding server для RAGFlow.

## API

Клиентский контракт находится в [`api-contract/openapi.yaml`](api-contract/openapi.yaml).

Основные группы endpoints:

- Auth и профиль: регистрация, логин, текущий пользователь.
- Reference data: типы счетов, активов, долгов, категории, merchants, institutions.
- CRUD пользовательских объектов: accounts, transactions, transfers, recurring transactions, assets, liabilities, liability payments, goals, tags.
- Imports: идемпотентный импорт операций.
- Analytics: dashboard, cash-flow, net-worth, daily snapshots.
- AI Chat: текстовый и голосовой чат.

## База данных

Схема описана в двух формах:

- [`db/schema.dbml`](db/schema.dbml) - компактная DBML-схема для визуализации и обсуждения.
- [`backend/migrations/versions/`](backend/migrations/versions/) - исполняемая история изменений через Alembic.

Подробная смысловая документация таблиц находится в [`db/descriptions.md`](db/descriptions.md).

## Локальный запуск

Файл `.env` в корне проекта должен содержать параметры PostgreSQL:

```bash
POSTGRES_DB=findoctor
POSTGRES_USER=findoctor
POSTGRES_PASSWORD=change_me
POSTGRES_PORT=5433
```

Запуск локальной БД:

```bash
cd backend
make db-up
```

Применение миграций:

```bash
cd backend
make migrate
```

Проверка текущей ревизии:

```bash
cd backend
make db-current
```

Более подробная инструкция по Docker/PostgreSQL: [`db/deployment.md`](db/deployment.md).

## Проверка Перед Демо

Проект рассчитан на строгую проверку перед хакатонной сдачей: сначала backend gate, затем dependency/security scan frontend, затем production build.

```bash
cd backend
./.venv/bin/python -m compileall -q app tests scripts
./.venv/bin/ruff check app tests scripts
./.venv/bin/pytest tests/ -q

cd ../frontend
npm audit --audit-level=moderate
npm run build
```

Проверки закрывают:

- синтаксис и импортируемость backend-кода;
- Ruff-линтинг;
- полный API/integration suite на PostgreSQL test DB;
- совпадение FastAPI route surface с `api-contract/openapi.yaml`;
- cross-user изоляцию финансовых сущностей;
- отсутствие npm audit findings уровня moderate и выше;
- production-сборку Next.js frontend.

## Корневой Makefile

В корне проекта есть общий `Makefile` для локального, гибридного и cloud-oriented запуска.

```bash
make help
make doctor
make init
```

Основные сценарии:

```bash
# Только ядро: PostgreSQL + backend migrations
make init-core
make local-up-core

# Рекомендационный стек локально: TEI + RAGFlow + SearXNG
make init-recommendations
make pull-recommendations
make local-up-recommendations

# Локальный AI-стек: vLLM + TEI + RAGFlow + SearXNG
make pull-ai-local
make local-up-ai

# Проверка cloud/hybrid конфигурации
make cloud-check
make cloud-recommendations-check
```

Полная инструкция по вариантам деплоя: [`docs/deployment.md`](docs/deployment.md).

## Миграции

Новая миграция создается из `backend/`:

```bash
make migration m="describe change"
```

После ручного редактирования миграции:

```bash
make migrate
```

Правило проекта: любое изменение структуры БД должно быть отражено и в Alembic-миграции, и в `db/schema.dbml`.

## Связанные документы

| Документ | Что внутри |
| --- | --- |
| [`api-contract/openapi.yaml`](api-contract/openapi.yaml) | Полный клиентский OpenAPI/Swagger-контракт. |
| [`backend/STACK.md`](backend/STACK.md) | Backend-стек, правила транзакций, SQL-подход, тестирование. |
| [`backend/TESTING.md`](backend/TESTING.md) | Backend test gate, fixtures, cross-user authorization tests и правила покрытия. |
| [`docs/deployment.md`](docs/deployment.md) | Локальные, гибридные, fully local AI и cloud-oriented профили деплоя. |
| [`docs/hackathon-readiness.md`](docs/hackathon-readiness.md) | Что показывать на демо, какие проверки запускать и какие границы системы честно проговаривать. |
| [`backend/docs/recommendations.md`](backend/docs/recommendations.md) | Recommendation planner/RAG/search architecture and runtime contract. |
| [`backend/docs/recommendation_examples.md`](backend/docs/recommendation_examples.md) | Example planner JSON and final-answer behavior. |
| [`backend/docs/ragflow_dataset_setup.md`](backend/docs/ragflow_dataset_setup.md) | RAGFlow dataset, TEI embedding, and smoke-test setup. |
| [`db/schema.dbml`](db/schema.dbml) | DBML-схема таблиц, enum, индексов и связей. |
| [`db/descriptions.md`](db/descriptions.md) | Подробное описание доменной модели и назначения таблиц. |
| [`db/deployment.md`](db/deployment.md) | Локальный запуск PostgreSQL, backup/restore, частые проблемы. |
| [`backend/migrations/README.md`](backend/migrations/README.md) | Контекст по миграциям. |

## Текущий статус

Готово:

- базовая схема PostgreSQL;
- Alembic-миграции;
- DBML-документация;
- OpenAPI-контракт клиентского API;
- модель переводов через две связанные транзакции;
- FastAPI backend с основными API-группами;
- AI chat endpoints с текстовым и голосовым сценариями;
- опциональный recommendation/RAG/search контур;
- user-scoped object-level доступ к пользовательским финансовым данным;
- redaction/выключение чувствительного HTTP-логирования по умолчанию;
- cross-user authorization тесты;
- dependency scanner clean для frontend (`npm audit --audit-level=moderate`);
- локальные service wrappers для vLLM, RAGFlow, SearXNG, TEI и voice-прототипов;
- черновой фронтенд/voice playground.

Следующие крупные шаги:

- довести клиентский UX и dashboard flows;
- реализовать фоновые пересчеты аналитических snapshots;
- подготовить production deployment manifests для выбранной инфраструктуры.
