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

## Режимы Деплоя

### 1. Локальное Ядро

Используйте этот режим для разработки backend, базы данных и frontend без RAG/search-рекомендаций.

```bash
make init-core
make local-up-core
make backend-run
```

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

Настройте backend:

```env
LLM_BASE_URL=http://localhost:8100/v1
LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
RAGFLOW_EMBEDDING_BASE_URL=http://host.docker.internal:8200/v1
```

Конкретная LLM-модель выбирается в `vLLM/.env`.

### 4. Гибридный Режим

Используйте этот режим, когда LLM/STT/TTS находятся в облаке или в RouterAI-compatible провайдере, а RAG/search/embeddings остаются локальными.

```bash
make init-recommendations
make pull-recommendations
make hybrid-up-recommendations
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
make local-up-core
make local-up-recommendations
make local-up-ai
make local-up
make hybrid-up-recommendations
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

Логи:

```bash
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
