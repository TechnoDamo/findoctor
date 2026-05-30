# Архитектура Рекомендаций, RAG И Поиска

Рекомендации ФинДоктора реализованы как поток «сначала план, потом действие» внутри существующего AI-чата.

```text
POST /api/v1/ai/chat/messages
  -> LLM-планировщик рекомендаций возвращает строгий JSON
  -> backend выполняет запрошенные инструменты
  -> LLM-финализатор отвечает на основе финансового контекста и evidence
  -> response.tool_results содержит план и evidence
```

По умолчанию поток выключен. Включение:

```env
RECOMMENDATIONS_ENABLED=true
```

## Строгий Контракт Planner

Первый LLM-вызов ограничен через `response_format.type=json_schema`.

Обязательная структура ответа:

```json
{
  "response_text": "Нужно проверить разрешенные источники перед ответом.",
  "needed_tools": {
    "rag": {
      "rag_requests": [
        "emergency fund before taking new debt"
      ]
    },
    "search": {
      "search_queries": [
        "site:cbr.ru consumer debt burden"
      ]
    }
  }
}
```

`needed_tools` может быть `null`. Отдельные секции tools тоже могут быть `null`.

Смысл полей:

- `rag.rag_requests`: запросы к уже проиндексированному разрешенному контенту в RAGFlow;
- `search.search_queries`: discovery URL через SearXNG с последующей фильтрацией по allowlist;
- `needed_tools: null`: ответ можно дать без retrieval.

Схема находится здесь:

```text
backend/app/services/recommendations/schemas.py
```

Prompt planner находится здесь:

```text
backend/app/prompts/recommendation_planner.txt
```

Planner и finalizer также подключают общие policy-файлы:

```text
backend/app/prompts/recommendation_context_policy.txt
backend/app/prompts/recommendation_safety_policy.txt
```

## Backend-Модули

```text
backend/app/services/recommendations/
├── orchestrator.py      # planner -> tools -> finalizer
├── ragflow.py           # RAGFlow retrieval adapter
├── search.py            # SearXNG adapter
├── schemas.py           # строгая planner-схема и evidence-модели
└── source_policy.py     # парсинг allowed_resources.txt и URL-фильтрация
```

Существующий chat service вызывает orchestrator из:

```text
backend/app/services/ai_chat.py
```

## Переменные Окружения

```env
RECOMMENDATIONS_ENABLED=true
RECOMMENDATION_ALLOWED_RESOURCES_FILE=../ragflow/allowed_resources.txt
RECOMMENDATION_MAX_RAG_REQUESTS=3
RECOMMENDATION_MAX_SEARCH_QUERIES=3
RECOMMENDATION_MAX_EVIDENCE_ITEMS=8
RECOMMENDATION_MAX_EVIDENCE_CHARS=12000

RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...
RAGFLOW_PAGE_SIZE=5

SEARXNG_BASE_URL=http://localhost:8201
SEARXNG_TIMEOUT_SECONDS=20
```

`RECOMMENDATION_PLANNER_MODEL` и `RECOMMENDATION_FINALIZER_MODEL` могут переопределять `LLM_MODEL`. Если они пустые, используется обычный LLM provider config.

## Разрешенные Источники

Пока список разрешенных источников хранится здесь:

```text
ragflow/allowed_resources.txt
```

Backend читает один URL или domain на строку. Пустые строки и комментарии игнорируются.

Результаты поиска фильтруются по нормализованному host. SearXNG сам по себе не считается доверенным источником: он только находит candidate URL.

## Tool Results

API-ответ сохраняет существующее поле `tool_results`:

```json
[
  {
    "type": "recommendation_plan",
    "plan": {
      "response_text": "...",
      "needed_tools": {
        "rag": {"rag_requests": ["..."]},
        "search": null
      }
    }
  },
  {
    "type": "recommendation_evidence",
    "items": [
      {
        "source": "ragflow",
        "query": "...",
        "title": "...",
        "url": "...",
        "text": "...",
        "score": 0.82,
        "metadata": {}
      }
    ]
  }
]
```

Так рекомендация остается проверяемой без изменения верхнеуровневого chat-контракта.

## Локальный Стек Сервисов

Предпочтительные команды из корня репозитория:

```bash
make init-recommendations
make pull-recommendations
make local-up-recommendations
```

Эквивалентные команды по отдельным сервисам:

```bash
cd tei
make init && make pull && make run && make test

cd ../ragflow
make init && make fetch && make configure && make up && make wait

cd ../searxng
make init && make pull && make run && make test
```

Затем настройте RAGFlow:

1. Создайте внутренний service account/API key.
2. Создайте или выберите dataset для рекомендаций ФинДоктора.
3. Запишите значения в `ragflow/.env` и `backend/.env`.
4. Настройте RAGFlow embeddings через TEI:

```env
RAGFLOW_EMBEDDING_BASE_URL=http://host.docker.internal:8200/v1
RAGFLOW_EMBEDDING_MODEL=BAAI/bge-m3
RAGFLOW_EMBEDDING_API_KEY=local-dev-key
```

## Тестовая Стратегия

Backend unit tests покрывают:

- парсинг разрешенных источников и host-фильтрацию;
- фильтрацию результатов SearXNG;
- нормализацию planner JSON;
- интеграцию chat при включенном потоке рекомендаций.

Директории сервисов также содержат внешние smoke tests:

- `ragflow/make test`;
- `searxng/make test`;
- `tei/make test`.

Дополнительный контекст:

- `docs/deployment.md`;
- `backend/docs/recommendation_examples.md`;
- `backend/docs/ragflow_dataset_setup.md`.
