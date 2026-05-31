# Деплой ПрофИИта

Этот документ описывает поддерживаемые режимы запуска и корневые команды `Makefile`, которые ими управляют.

## Карта Сервисов

```text
Фронтенд / голосовой интерфейс
  -> FastAPI backend
       -> PostgreSQL
       -> LLM/STT/TTS-провайдер
       -> оркестратор рекомендаций
            -> RAGFlow
            -> SearXNG
            -> TEI embeddings
```

Рекомендационные сервисы опциональны. Backend сохраняет прежний путь AI-чата, пока явно не включен флаг:

```env
RECOMMENDATIONS_ENABLED=true
```

## Production Safety Gate

Backend валидирует опасные настройки при старте. В production-режиме приложение не должно запускаться, если обнаружены:

- дефолтный `JWT_SECRET_KEY`;
- дефолтный пароль БД без явного `DATABASE_URL`;
- `APP_DEBUG=true`;
- подробное логирование HTTP headers/bodies;
- включенные рекомендации без обязательных RAG/search параметров.

По умолчанию HTTP headers, request bodies и response bodies не логируются. Если подробное логирование временно включено для диагностики, middleware редактирует чувствительные поля: токены, пароли, cookies, API keys, audio/base64 payloads.

## Makefile Policy

Корневой `Makefile` теперь работает как диспетчер deployment matrix. Основная команда одна:

```bash
make deploy-system ENTITY=<entity> DEPLOYMENT=<local|cloud|hybrid>
```

`ENTITY` отвечает за компонент системы, `DEPLOYMENT` — за способ размещения. Если выбран `local`, корень делегирует работу Makefile конкретной папки: `backend/`, `frontend/`, `db/`, `ragflow/`, `searxng/`, `tei/`, `vLLM/`, `whisper-server/`, `graylog/`. Если выбран `cloud`, локальный сервис не поднимается: команда проверяет, что backend/frontend или внешний endpoint настроены через env.

Базовая матрица:

| Entity | Local | Cloud |
| --- | --- | --- |
| `postgres` / `db` | `db/deploy-local`: PostgreSQL container + Alembic migrations | Проверка managed `DATABASE_URL` |
| `backend` | `backend/deploy-local`: backend Docker image/container | Проверка backend env для внешней инфраструктуры |
| `frontend` | `frontend/deploy-local`: frontend Docker image/container | Проверка `NEXT_PUBLIC_API_URL` |
| `core` | `postgres` + `backend` + `frontend` | Проверка cloud-конфигурации этих трёх сущностей |
| `ragflow` | Локальный upstream RAGFlow compose | Проверка external/internal RAGFlow endpoint |
| `searxng` / `search` | Локальный SearXNG container | Проверка external/internal search endpoint |
| `tei` / `embeddings` | Локальный TEI container | Проверка external/internal embeddings endpoint |
| `recommendations` | `tei` + `searxng` + `ragflow` локально | Проверка RAG/search env для backend |
| `vllm` / `llm` | Локальный OpenAI-compatible vLLM | Проверка cloud/external LLM env |
| `whisper` / `stt` | Локальный whisper.cpp proxy | Проверка cloud/external STT env |
| `graylog` / `observability` | Локальный Graylog stack | Проверка external log endpoint |
| `system` | `core` + `recommendations` | Cloud checks для core + recommendations |
| `full` | `system` + `vllm` + `graylog` | Не используется как cloud-сценарий |

Остановка и диагностика используют тот же `ENTITY`:

```bash
make stop-system ENTITY=backend
make status-system ENTITY=core
make logs-system ENTITY=ragflow
```

Старые команды (`make local-up-core`, `make deploy-local-core`, `make deploy-local-ai`) оставлены как совместимые алиасы, но новая политика должна идти через `deploy-system`.

## Режимы Деплоя

Все режимы делятся на две группы:

- service-level запуск через существующие Makefile в `backend/`, `ragflow/`, `tei/`, `searxng/`, `vLLM/`, `graylog/`;
- root Docker deployment через `docker-compose.yml`, который собирает и запускает PostgreSQL, backend и frontend.

Backend и frontend dockerized:

- [`backend/Dockerfile`](../backend/Dockerfile) — FastAPI + migrations-on-start через `RUN_MIGRATIONS=true`;
- [`frontend/Dockerfile`](../frontend/Dockerfile) — production Next.js build;
- [`docker-compose.yml`](../docker-compose.yml) — root compose для `postgres`, `backend`, `frontend`.

### 1. Локальное Ядро

Используйте этот режим для разработки backend, базы данных и frontend без RAG/search-рекомендаций.

```bash
make deploy-system ENTITY=core DEPLOYMENT=local
```

Это поднимает:

- PostgreSQL container;
- backend container;
- frontend container.

Если нужен backend без frontend:

```bash
make deploy-system ENTITY=postgres DEPLOYMENT=local
make deploy-system ENTITY=backend DEPLOYMENT=local
```

Тесты backend:

```bash
make backend-test
```

### 2. Локальные Рекомендации

Используйте этот режим, когда RAGFlow, SearXNG и TEI запускаются локально.

```bash
make deploy-system ENTITY=recommendations DEPLOYMENT=local
```

После запуска создайте в RAGFlow сервисный API-ключ и dataset, затем заполните:

```env
# backend/.env
RECOMMENDATIONS_ENABLED=true
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...
SEARXNG_BASE_URL=http://localhost:8201
```

Проверка:

```bash
make backend-test-recommendations
make recommendations-test
```

### 3. Полностью Локальный AI

Используйте этот режим, когда LLM inference и embeddings работают локально.

```bash
make deploy-system ENTITY=ai DEPLOYMENT=local
```

Настройте backend:

```env
LLM_BASE_URL=http://localhost:8100/v1
LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
RAGFLOW_EMBEDDING_BASE_URL=http://host.docker.internal:8200/v1
```

Если backend запущен в Docker container, используйте адрес хоста Docker:

```env
LLM_BASE_URL=http://host.docker.internal:8100/v1
RAGFLOW_BASE_URL=http://host.docker.internal:9380
SEARXNG_BASE_URL=http://host.docker.internal:8201
```

Конкретная LLM-модель выбирается в `vLLM/.env`.

### 4. Гибридный Режим

Используйте этот режим, когда LLM/STT/TTS находятся в облаке или в RouterAI-compatible провайдере, а RAG/search/embeddings остаются локальными.

```bash
make deploy-system ENTITY=ai DEPLOYMENT=hybrid
```

Настройте backend:

```env
LLM_BASE_URL=https://routerai.ru/api/v1
LLM_API_KEY=...
LLM_MODEL=...

RECOMMENDATIONS_ENABLED=true
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...
SEARXNG_BASE_URL=http://localhost:8201
```

Проверка:

```bash
make cloud-check
make cloud-recommendations-check
```

### 5. Облачные И Управляемые Сервисы

Используйте этот режим, когда backend работает с внешними endpoint для LLM, RAGFlow, SearXNG-compatible поиска или управляемых аналогов.

Локальные recommendation-контейнеры в этом режиме запускать не нужно. Настройте:

```env
RECOMMENDATIONS_ENABLED=true
LLM_BASE_URL=https://...
LLM_API_KEY=...
LLM_MODEL=...

RAGFLOW_BASE_URL=https://internal-ragflow.example
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...

SEARXNG_BASE_URL=https://internal-search.example
```

Проверьте форму env-конфига:

```bash
make cloud-check
make cloud-recommendations-check
```

Правило безопасности: RAGFlow и SearXNG должны оставаться приватными/internal сервисами. Фронтенд никогда не должен получать их API-ключи или прямые URL.

Docker-вариант:

Для проверки cloud-конфигурации через новую матрицу:

```bash
make deploy-system ENTITY=ai DEPLOYMENT=cloud
make deploy-system ENTITY=recommendations DEPLOYMENT=cloud
```

### 6. Full Local Demo

Используйте для максимально автономного демо на машине с Docker и достаточными ресурсами:

```bash
make deploy-system ENTITY=full DEPLOYMENT=local
```

Поднимает:

- vLLM;
- TEI;
- RAGFlow;
- SearXNG;
- Graylog;
- PostgreSQL;
- backend;
- frontend.

Это самый тяжелый режим. Для ноутбука без GPU обычно лучше использовать `deploy-hybrid-llm-local-rag`: LLM/STT/TTS в cloud/external API, RAG/search/embeddings локально.

## Корневые Make-Команды

Новый основной интерфейс:

```bash
make deploy-system ENTITY=postgres DEPLOYMENT=local
make deploy-system ENTITY=backend DEPLOYMENT=local
make deploy-system ENTITY=frontend DEPLOYMENT=local
make deploy-system ENTITY=recommendations DEPLOYMENT=local
make deploy-system ENTITY=ai DEPLOYMENT=hybrid
```

Статус, логи, остановка:

```bash
make status-system ENTITY=core
make logs-system ENTITY=backend
make stop-system ENTITY=recommendations
```

Совместимые алиасы старого слоя оставлены для скриптов и muscle memory: `make local-up-core`, `make deploy-local-core`, `make deploy-local-ai`, `make deploy-full-local`, `make deploy-down`.

Проверка:

```bash
make doctor
make status
make backend-test
make backend-test-recommendations
make recommendations-test
make recommendations-curl
```

Полная проверка перед демо или PR:

```bash
cd backend
./.venv/bin/python -m compileall -q app tests scripts
./.venv/bin/ruff check app tests scripts
./.venv/bin/pytest tests/ -q

cd ../frontend
npm audit --audit-level=moderate
npm run build
```

Если `npm audit` сообщает findings уровня moderate и выше, dependency lock нельзя считать готовым к сдаче.

Логи:

```bash
make logs-system ENTITY=backend
make logs-system ENTITY=ragflow
make logs-system ENTITY=searxng
make logs-system ENTITY=tei
make logs-system ENTITY=vllm
```

## Первый Запуск Рекомендаций

Для первого локального запуска recommendation-стека:

```bash
make deploy-system ENTITY=recommendations DEPLOYMENT=local
```

Затем:

1. Откройте admin UI RAGFlow.
2. Настройте TEI как embedding provider.
3. Создайте dataset `findoctor-recommendations`.
4. Создайте сервисный API-ключ.
5. Заполните `backend/.env`.
6. Запустите `make backend-test-recommendations`.
7. Запустите `make recommendations-test`.

### Локальный STT (whisper-server)

Для локального распознавания речи требуется инициализировать git-сабмодуль whisper.cpp:

```bash
make deploy-system ENTITY=whisper DEPLOYMENT=local
```

Команда `make init` в whisper-server автоматически выполнит `git submodule update --init`.
Если сабмодуль не склонирован, `make build` выведет ошибку с инструкцией.

## Диагностика

Если локальный recommendation-стек падает из-за уже существующего контейнера:

```bash
make stop-system ENTITY=recommendations
make deploy-system ENTITY=recommendations DEPLOYMENT=local
```

Если падают API-тесты RAGFlow:

- проверьте `RAGFLOW_API_KEY`;
- проверьте `RAGFLOW_DATASET_ID`;
- запустите `make logs-system ENTITY=ragflow`;
- запустите `cd ragflow && make curl-examples`.

Если падают embeddings:

- запустите `make logs-system ENTITY=tei`;
- попробуйте более легкую модель `TEI_MODEL_ID`;
- проверьте, что RAGFlow использует `/v1` в конце TEI base URL.

## UML И Sequence Диаграммы

Высокоуровневые диаграммы архитектуры, продуктовых блоков и sequence flows находятся в [`docs/architecture-uml.md`](architecture-uml.md):

- компонентная карта из frontend/backend/LLM/STT/TTS/RAG/search/embeddings/logging;
- карта продуктовых блоков: кредитный светофор, финансовый диагноз, трекер накоплений, AI assistant;
- sequence регистрации и CRUD;
- sequence AI chat с user data tool;
- sequence RAG/search рекомендации;
- sequence голосового режима;
- sequence Docker deployment.
