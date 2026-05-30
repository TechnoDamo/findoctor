# Деплой ФинДоктора

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
make init-core
make local-up-core
make backend-run
```

Docker-вариант:

```bash
make deploy-local-core
```

Поднимает:

- PostgreSQL container;
- backend container;
- frontend container.

Тесты backend:

```bash
make backend-test
```

### 2. Локальные Рекомендации

Используйте этот режим, когда RAGFlow, SearXNG и TEI запускаются локально.

```bash
make init-recommendations
make pull-recommendations
make local-up-recommendations
```

Docker-вариант приложения + локальные recommendation-сервисы:

```bash
make deploy-local-rag
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
make init
make pull-ai-local
make local-up-ai
```

Docker-вариант приложения + локальный vLLM/RAG/Search/Embeddings:

```bash
make deploy-local-ai
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
make init-recommendations
make pull-recommendations
make hybrid-up-recommendations
```

Docker-вариант:

```bash
make deploy-hybrid-llm-local-rag
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

```bash
make deploy-cloud-ai
```

В этом режиме root compose запускает только приложение и PostgreSQL, а все AI/RAG/search endpoints берутся из env.

### 6. Full Local Demo

Используйте для максимально автономного демо на машине с Docker и достаточными ресурсами:

```bash
make deploy-full-local
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

Инициализация:

```bash
make init
make init-core
make init-recommendations
make pull-recommendations
make pull-ai-local
```

Запуск:

```bash
make compose-build
make compose-up-core
make compose-up-app
make local-up-core
make local-up-recommendations
make local-up-ai
make local-up
make hybrid-up-recommendations
make deploy-local-core
make deploy-local-rag
make deploy-local-ai
make deploy-hybrid-llm-local-rag
make deploy-cloud-ai
make deploy-full-local
make deploy-down
make local-down
```

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
make compose-logs
make logs-ragflow
make logs-searxng
make logs-tei
make logs-vllm
make logs-backend
```

## Первый Запуск Рекомендаций

Для первого локального запуска recommendation-стека:

```bash
make init
make pull-recommendations
make local-up-recommendations
```

Затем:

1. Откройте admin UI RAGFlow.
2. Настройте TEI как embedding provider.
3. Создайте dataset `findoctor-recommendations`.
4. Создайте сервисный API-ключ.
5. Заполните `backend/.env`.
6. Запустите `make backend-test-recommendations`.
7. Запустите `make recommendations-test`.

## Диагностика

Если `make local-up-recommendations` падает из-за уже существующего контейнера:

```bash
make local-down-recommendations
make local-up-recommendations
```

Если падают API-тесты RAGFlow:

- проверьте `RAGFLOW_API_KEY`;
- проверьте `RAGFLOW_DATASET_ID`;
- запустите `make logs-ragflow`;
- запустите `cd ragflow && make curl-examples`.

Если падают embeddings:

- запустите `make logs-tei`;
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
