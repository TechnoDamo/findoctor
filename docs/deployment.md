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

Корневой `Makefile` — **per-component deployment dispatcher**. Каждый компонент настраивается независимо:

```bash
make deploy-system [postgres=local|cloud] [ragflow=local|cloud|none] [searxng=local|cloud|none] \
                   [graylog=local|cloud|none] [tei=local|none] [vllm=local|none] [whisper=local|none]
```

`backend` и `frontend` деплоятся **всегда** (Docker контейнеры), флагов не требуют.

### Таблица компонентов

| Компонент | Флаги | Дефолт | `local` | `cloud` | `none` |
|-----------|-------|--------|---------|---------|--------|
| backend | — | — | Docker контейнер | — | — |
| frontend | — | — | Docker контейнер | — | — |
| postgres | `local` `cloud` | **local** | контейнер PostgreSQL + Alembic миграции | проверка managed `DATABASE_URL` | — |
| ragflow | `local` `cloud` `none` | **local** | upstream RAGFlow compose | проверка `RAGFLOW_BASE_URL`/`API_KEY`/`DATASET_ID` | пропустить |
| searxng | `local` `cloud` `none` | **local** | локальный SearXNG контейнер | проверка `SEARXNG_BASE_URL` | пропустить |
| graylog | `local` `cloud` `none` | **local** | локальный Graylog стек | проверка `GRAYLOG_HOST` | пропустить |
| tei | `local` `none` | **none** | локальный TEI embeddings контейнер | — | пропустить |
| vllm | `local` `none` | **none** | локальный OpenAI-совместимый vLLM | — | пропустить |
| whisper | `local` `none` | **none** | локальный whisper.cpp сервер + прокси | — | пропустить |

### Пресеты

| Команда | Что делает |
|---------|-----------|
| `make deploy-system` | дефолт: инфраструктура локально, AI не трогаем |
| `make deploy-system core` | только backend+frontend+postgres |
| `make deploy-system hybrid` | cloud LLM + локальные RAG/search/embeddings |
| `make deploy-system fully-local` | всё локально (включая vLLM, TEI, whisper) |
| `make deploy-system cloud` | всё cloud: только валидация env, ничего не деплоится |

### Остановка / статус / логи

Компоненты указываются через `COMPONENTS` (множественный) или `COMPONENT` (один):

```bash
make stop-system   COMPONENTS="postgres ragflow vllm"
make stop-system   COMPONENTS=all
make status-system COMPONENTS="backend ragflow"
make logs-system   COMPONENT=backend
make logs-system   COMPONENT=vllm
```

Совместимые алиасы (`make deploy-local-core`, `make deploy-full-local`) оставлены для muscle memory.

## Режимы Деплоя

Все режимы делятся на две группы:

- service-level запуск через существующие Makefile в `backend/`, `ragflow/`, `tei/`, `searxng/`, `vLLM/`, `graylog/`;
- root Docker deployment через `docker-compose.yml`, который собирает и запускает PostgreSQL, backend и frontend.

Backend и frontend dockerized:

- [`backend/Dockerfile`](../backend/Dockerfile) — FastAPI + migrations-on-start через `RUN_MIGRATIONS=true`;
- [`frontend/Dockerfile`](../frontend/Dockerfile) — production Next.js build;
- [`docker-compose.yml`](../docker-compose.yml) — root compose для `postgres`, `backend`, `frontend`.

### 1. Дефолтный Режим

Инфраструктура локально (postgres, ragflow, searxng, graylog) + backend + frontend. AI-модели (vllm, tei, whisper) не трогаем.

```bash
make deploy-system
```

### 2. Локальное Ядро

Только backend, frontend и postgres. Без рекомендаций и AI.

```bash
make deploy-system core
```

### 3. Локальные Рекомендации

Дефолтный режим уже включает ragflow, searxng. После запуска настройте API-ключ и dataset:

```env
# backend/.env
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...
SEARXNG_BASE_URL=http://localhost:8201
```

### 4. Полностью Локальный AI

```bash
make deploy-system vllm=local tei=local whisper=local
```

Настройте backend:

```env
LLM_BASE_URL=http://localhost:8100/v1
LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
```

### 5. Гибридный Режим

Cloud LLM + локальные RAG/search/embeddings:

```bash
make deploy-system tei=local
```

### 6. Облачные Сервисы

Всё через cloud — только валидация env, ничего локально не деплоится:

```bash
make deploy-system cloud
```

### 7. Full Local Demo

```bash
make deploy-system vllm=local tei=local whisper=local
```

## Корневые Make-Команды

Дефолтный запуск:

```bash
make deploy-system
```

Переопределение компонентов:

```bash
make deploy-system vllm=local whisper=local
make deploy-system ragflow=cloud searxng=none
```

Статус, логи, остановка:

```bash
make status-system COMPONENTS="backend ragflow"
make logs-system COMPONENT=backend
make stop-system COMPONENTS="ragflow searxng"
make stop-system COMPONENTS=all
```

```bash
make doctor
make status-system COMPONENTS="backend postgres"
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
make logs-system COMPONENT=backend
make logs-system COMPONENT=ragflow
make logs-system COMPONENT=searxng
make logs-system COMPONENT=tei
make logs-system COMPONENT=vllm
```

## Первый Запуск Рекомендаций

Для первого локального запуска recommendation-стека:

```bash
make deploy-system
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

```bash
make deploy-system whisper=local
```

Команда `make init` в whisper-server автоматически выполнит `git submodule update --init`.
Если сабмодуль не склонирован, `make build` выведет ошибку с инструкцией.

## Диагностика

Если локальный recommendation-стек падает из-за уже существующего контейнера:

```bash
make stop-system COMPONENTS="ragflow searxng tei"
make deploy-system
```

Если падают API-тесты RAGFlow:

- проверьте `RAGFLOW_API_KEY`;
- проверьте `RAGFLOW_DATASET_ID`;
- запустите `make logs-system COMPONENT=ragflow`;
- запустите `cd ragflow && make curl-examples`.

Если падают embeddings:

- запустите `make logs-system COMPONENT=tei`;
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
