# RAGFlow

Внутренний self-hosted RAG-сервис ФинДоктора. Используется рекомендательным оркестратором backend для retrieval из проиндексированной базы знаний.

Backend-поток рекомендаций описан в `../backend/docs/recommendations.md`. Архитектура AI-чата — в `../backend/docs/ai-chat.md`.

## Структура

```text
ragflow/
├── .env.example               # шаблон конфигурации
├── .env                        # локальный конфиг (игнорируется git)
├── Makefile                    # управление контейнерами
├── samples/
│   └── findoctor-rag-smoke.md  # тестовый документ для загрузки в датасет
└── scripts/
    └── configure_upstream_env.sh  # подготовка upstream .env
```

Upstream-репозиторий RAGFlow клонируется в `.runtime/ragflow` командой `make fetch`. Полный upstream Docker-стек в репозиторий не вендорится.

## Быстрый старт

```bash
cd ragflow

make init       # создать .env из .env.example
make fetch      # склонировать upstream RAGFlow
make configure  # подготовить upstream docker/.env
make pull       # скачать все Docker-образы (elasticsearch, postgres, redis, RAGFlow API и т.д.)
make up         # запустить Docker-стек
```

После запуска откройте RAGFlow по адресу `http://localhost:9380`, создайте service account API-ключ и датасет для рекомендаций, заполните `RAGFLOW_API_KEY` и `RAGFLOW_DATASET_ID` в `ragflow/.env`.

Проверьте работу:

```bash
make test     # health-чек + retrieval smoke test
```

## Конфигурация

Файл: `ragflow/.env`

### Сам RAGFlow

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `RAGFLOW_BASE_URL` | `http://localhost:9380` | HTTP API RAGFlow |
| `RAGFLOW_API_KEY` | — | API-ключ service account (заполнить после настройки) |
| `RAGFLOW_DATASET_ID` | — | ID датасета рекомендаций (заполнить после настройки) |
| `RAGFLOW_DATASET_NAME` | `findoctor-recommendations` | Человекочитаемое имя датасета |

### Embedding-провайдер

Переменная `RAGFLOW_EMBEDDING_PROVIDER` — выбор между локальным TEI и облачным OpenAI-совместимым эндпоинтом.

**Вариант `tei`** (самодеплойный, бесплатный):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `TEI_BASE_URL` | `http://localhost:8200` | Адрес TEI |
| `TEI_MODEL_ID` | `BAAI/bge-m3` | HuggingFace-модель (multilingual, хороша для русского) |
| `TEI_API_KEY` | `local-dev-key` | TEI не требует аутентификации, но RAGFlow ожидает заголовок |

**Вариант `openai`** (облачный или RouterAI):

| Переменная | Назначение |
|---|---|
| `EMBEDDING_BASE_URL` | OpenAI-совместимый эндпоинт `/v1/embeddings` |
| `EMBEDDING_API_KEY` | API-ключ провайдера |
| `EMBEDDING_MODEL` | Имя модели (например `text-embedding-3-small`, `Qwen/Qwen3-Embedding-8B`) |

### LLM-провайдер (внутренний чат RAGFlow)

Переменная `RAGFLOW_LLM_PROVIDER` — выбор между локальным vLLM и облачной OpenAI-совместимой LLM.

**Вариант `vllm`** (самодеплойный, бесплатный):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VLLM_BASE_URL` | `http://localhost:8100/v1` | Адрес vLLM |
| `VLLM_MODEL` | `Qwen/Qwen2.5-1.5B-Instruct` | Модель, загруженная в vLLM |

**Вариант `openai`** (облачный или RouterAI):

| Переменная | Назначение |
|---|---|
| `LLM_BASE_URL` | OpenAI-совместимый эндпоинт `/v1/chat/completions` |
| `LLM_API_KEY` | API-ключ провайдера |
| `LLM_MODEL` | Имя модели (например `gpt-4o`, `google/gemini-2.5-flash`) |

### Пример: RouterAI

Если используется RouterAI и локально ничего не поднимается (`../tei/` и `../vLLM/` не запущены):

```env
# embeddings
RAGFLOW_EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://routerai.ru/api/v1
EMBEDDING_API_KEY=sk-gY63dt1jGYJUvi19vPH9HVT9cVtQRKGo
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B

# LLM
RAGFLOW_LLM_PROVIDER=openai
LLM_BASE_URL=https://routerai.ru/api/v1
LLM_API_KEY=sk-gY63dt1jGYJUvi19vPH9HVT9cVtQRKGo
LLM_MODEL=google/gemini-2.5-flash
```

Backend Работает с теми же URL и ключом (`backend/.env`), поэтому значения совпадают.

### Пример: полностью локально

Если запущены TEI и vLLM (через `../tei/make run` и `../vLLM/make run`):

```env
RAGFLOW_EMBEDDING_PROVIDER=tei
TEI_BASE_URL=http://host.docker.internal:8200
TEI_MODEL_ID=BAAI/bge-m3
TEI_API_KEY=local-dev-key

RAGFLOW_LLM_PROVIDER=vllm
VLLM_BASE_URL=http://host.docker.internal:8100/v1
VLLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
```

`host.docker.internal` нужен потому, что RAGFlow работает в Docker, а TEI/vLLM — снаружи. Если все сервисы в одной Docker-сети, используйте имена контейнеров.

## Управление контейнерами

| Команда | Команда Docker | Что делает |
|---|---|---|
| `make pull` | `docker compose pull` | Скачивает все Docker-образы (DB, Elasticsearch, RAGFlow API и т.д.) |
| `make up` | `docker compose up -d` | Создаёт и запускает все контейнеры |
| `make down` | `docker compose down` | Останавливает и удаляет контейнеры + сети |
| `make stop` | `docker compose stop` | Приостанавливает контейнеры (сохраняет на диске) |
| `make start` | `docker compose start` | Возобновляет остановленные через `stop` контейнеры |
| `make reload` | `docker compose up -d --force-recreate` | Пересоздаёт контейнеры заново (сброс состояния) |
| `make restart` | `docker compose restart` | Перезапускает существующие контейнеры на месте |

Различия:

- **`stop` vs `down`**: `stop` сохраняет контейнеры и тома, `down` удаляет. После `down` нужен `up`, после `stop` — `start`.
- **`start` vs `up`**: `start` возобновляет ранее созданные контейнеры, `up` создаёт новые.
- **`reload` vs `restart`**: `reload` пересоздаёт контейнеры (сбрасывает состояние, перечитывает конфигурацию), `restart` просто перезапускает процессы внутри существующих контейнеров.

Вспомогательные команды:

| Команда | Что делает |
|---|---|
| `make init` | Создаёт `.env` из `.env.example` |
| `make fetch` | Клонирует upstream RAGFlow в `.runtime/ragflow` |
| `make configure` | Копирует upstream `docker/.env.example` → `docker/.env` |
| `make test` | Проверяет API: health-чек + векторный поиск + LLM-ретривал |

### Управление API-ключами и датасетами

Эти команды требуют `RAGFLOW_ADMIN_EMAIL` и `RAGFLOW_ADMIN_PASSWORD` в `.env`. Работают через RAGFlow REST API, не требуя открывать UI.

| Команда | Параметры | Что делает |
|---|---|---|
| `make key-create` | `NAME=<имя>` | Создаёт API-ключ и записывает его в `RAGFLOW_API_KEY` в `.env` |
| `make key-list` | — | Показывает все API-ключи |
| `make key-delete` | `TOKEN=<ключ>` | Удаляет указанный API-ключ |
| `make ds-create` | `NAME=<имя>` | Создаёт датасет и записывает ID в `RAGFLOW_DATASET_ID` в `.env` |
| `make ds-list` | — | Показывает все датасеты (id + name) |
| `make ds-delete` | `ID=<dataset_id>` | Удаляет указанный датасет |

**Типичный сценарий настройки:**

```bash
# 1. Заполните admin credentials в .env
#    RAGFLOW_ADMIN_EMAIL=admin@example.com
#    RAGFLOW_ADMIN_PASSWORD=ваш_пароль

# 2. Запустите RAGFlow
make up

# 3. Создайте датасет
make ds-create NAME=findoctor-recommendations
# → датасет создан, ID записан в RAGFLOW_DATASET_ID

# 4. Создайте API-ключ для backend
make key-create NAME=findoctor-backend
# → ключ создан, записан в RAGFLOW_API_KEY

# 5. Проверьте
make test
```

**При первом запуске**, когда admin-аккаунт ещё не создан, откройте RAGFlow UI (`http://localhost:9380`), зарегистрируйтесь, затем заполните email и пароль в `.env`.

## API-примеры

Все примеры предполагают, что переменные окружения загружены:

```bash
export RAGFLOW_BASE_URL=http://localhost:9380
export RAGFLOW_API_KEY="<ваш API-ключ>"
export RAGFLOW_DATASET_ID="<ID датасета>"
```

### 1. Полноценный RAG-запрос (retrieval)

`POST /api/v1/retrieval` — семантический поиск по датасету с возвратом проранжированных чанков. Именно так backend вызывает RAGFlow в потоке рекомендаций.

```bash
curl -sS \
  -X POST "$RAGFLOW_BASE_URL/api/v1/retrieval" \
  -H "Authorization: Bearer $RAGFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Что проверить перед рекомендацией взять новый кредит?",
    "dataset_ids": ["'"$RAGFLOW_DATASET_ID"'"],
    "page": 1,
    "page_size": 5
  }' | python3 -m json.tool
```

Параметры:

| Поле | Тип | Назначение |
|---|---|---|
| `question` | `string` | Поисковый запрос |
| `dataset_ids` | `string[]` | ID датасетов для поиска |
| `page` | `int` | Номер страницы |
| `page_size` | `int` | Чанков на страницу (backend использует 5) |

### 2. Векторный поиск (без RAG-переранжирования)

`POST /api/v1/datasets/{dataset_id}/search` — прямой семантический поиск по векторному индексу датасета, без шага RAG-переранжирования.

```bash
curl -sS \
  -X POST "$RAGFLOW_BASE_URL/api/v1/datasets/$RAGFLOW_DATASET_ID/search" \
  -H "Authorization: Bearer $RAGFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "размер финансовой подушки безопасности",
    "page": 1,
    "size": 10,
    "similarity_threshold": 0.2,
    "vector_similarity_weight": 0.3
  }' | python3 -m json.tool
```

Параметры:

| Поле | Тип | Назначение |
|---|---|---|
| `question` | `string` | Поисковый запрос |
| `page` | `int` | Номер страницы |
| `size` | `int` | Чанков на страницу |
| `similarity_threshold` | `float` | Порог гибридного сходства (0.0–1.0) |
| `vector_similarity_weight` | `float` | Вес векторного сходства (0.0–1.0), остальное — keyword |

Отличие от `/api/v1/retrieval`: этот эндпоинт возвращает сырые чанки без RAG-переранжирования. Полезен для отладки качества индексации или когда нужно больше контроля над ранжированием.
