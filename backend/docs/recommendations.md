# Архитектура Рекомендаций, RAG И Поиска

Рекомендации ПрофИИта реализованы как поток «сначала план, потом действие» внутри существующего AI-чата.

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

## Продуктовый Endpoint Рекомендаций

Для экранов продукта добавлен единый endpoint:

```http
POST /api/v1/recommendations?type=income
Authorization: Bearer <access_token>
Content-Type: application/json
```

`type` выбирает сценарий анализа:

| type | Статус | Что возвращает |
| --- | --- | --- |
| `income` | активно | Аналитика доходов пользователя и советы по улучшению доходной части. |
| `expenses` | активно | Аналитика расходов и советы по оптимизации/снижению трат. |
| `debt_traffic_light` | активно | Кредитный светофор: долговая ситуация, нагрузка, история и допустимость новых кредитов. |
| `credit_decision` | активно | Оценка конкретного кредита: статус, факты, влияние на рейтинг, свободные средства, допустимые условия. |
| `about_me` | активно | Общий финансовый портрет пользователя и отчет по улучшению ситуации. |
| `savings_goal` | зарезервировано | Временно возвращает `422`, пока пользователь не выбирает конкретную цель накопления. |

Минимальный запрос для активных типов:

```json
{
  "question": "Сделай краткий, понятный анализ"
}
```

Для `type=credit_decision` обязателен объект `credit`:

```json
{
  "credit": {
    "amount": "500000 RUB",
    "termMonths": 24,
    "monthlyPayment": "26000 RUB",
    "interestRate": "18.5%",
    "purpose": "ремонт квартиры",
    "incomeStability": "зарплата стабильна последние 12 месяцев, есть премии"
  },
  "question": "Стоит ли брать этот кредит сейчас?"
}
```

Ответ всегда русскоязычный и готовый для показа пользователю:

```json
{
  "type": "credit_decision",
  "title": "Расчет целесообразности кредита",
  "status": "Желтый",
  "analysis": "Текущая долговая нагрузка близка к верхней комфортной зоне...",
  "advice": "Брать кредит стоит только при снижении платежа...",
  "facts": ["Доходы покрывают регулярные расходы", "Резерв ниже желательного"],
  "creditRatingImpact": "При регулярных платежах влияние может быть нейтральным...",
  "freeCashAfterCredit": "После платежа останется около ...",
  "recommendedCredit": "Лучше рассматривать сумму до ...",
  "notBeforeMonths": 3,
  "sections": [],
  "outputText": "Полный текст ответа LLM...",
  "toolResults": [],
  "usage": {"inputTokens": 1200, "outputTokens": 450}
}
```

Endpoint использует тот же backend-controlled AI pipeline, что и chat-рекомендации:

```text
request -> product service -> recommendation orchestrator
        -> planner LLM -> user_data/RAGFlow/SearXNG tools
        -> finalizer LLM -> normalized product response
```

Логика кредитного светофора не зашита enum-порогами в код. Системный контекст находится в:

```text
backend/app/prompts/recommendation_endpoint.txt
```

Prompt задает ориентиры долговой нагрузки, но финальное решение требует учитывать весь доступный контекст: стабильность дохода, резерв, историю платежей, цель кредита, уже существующие обязательства и найденные evidence из RAG/search.

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
2. Создайте или выберите dataset для рекомендаций ПрофИИта.
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
