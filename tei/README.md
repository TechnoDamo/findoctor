# TEI

Внутренний локальный сервис embedding inference для ПрофИИта на базе Hugging Face Text Embeddings Inference.

TEI дает OpenAI-compatible endpoint `/v1/embeddings` и native embedding endpoints. RAGFlow может использовать этот сервис как локальный embedding provider.

Поток рекомендаций backend описан в `../backend/docs/recommendations.md`.

```text
RAGFlow ingestion
  -> TEI /v1/embeddings
  -> vectors сохраняются внутри retrieval backend, настроенного в RAGFlow
```

## Быстрый Старт

Из корня репозитория:

```bash
make init-recommendations
make pull-recommendations
make local-up-recommendations
```

Из этой директории:

```bash
cd tei
make init
make pull
make run
make test
```

URL по умолчанию:

```text
http://localhost:8200
```

Модель по умолчанию:

```text
BAAI/bge-m3
```

Это хороший multilingual default для русских и английских финансовых материалов. Если локальный CPU слишком медленный, задайте:

```env
TEI_MODEL_ID=intfloat/multilingual-e5-small
```

## Файлы

```text
tei/
├── .env.example
├── .env                 # локальный config, игнорируется git
├── Makefile
├── README.md
├── models/              # локальный model cache, игнорируется git
└── scripts/
    ├── common.sh
    ├── print_curl_examples.sh
    ├── test_embed.sh
    ├── test_openai_embeddings.sh
    ├── test_similarity.sh
    └── wait_for_tei.sh
```

## Команды

| Команда | Назначение |
|---|---|
| `make init` | Создать `.env` и директорию model cache |
| `make pull` | Скачать Docker image TEI |
| `make run` | Запустить TEI |
| `make stop` | Остановить и удалить контейнер |
| `make restart` | Перезапустить контейнер |
| `make logs` | Смотреть логи |
| `make wait` | Дождаться `/health` |
| `make info` | Показать `/info` |
| `make test` | Запустить health, native embedding, OpenAI embedding и similarity smoke tests |
| `make curl-examples` | Показать готовые curl-примеры |
| `make clean-all` | Остановить контейнер и удалить model cache |

## API-Примеры

Native endpoint:

```bash
curl -sS \
  -X POST "http://localhost:8200/embed" \
  -H "Content-Type: application/json" \
  -d '{"inputs":["ПрофИИт проверяет cash flow перед рекомендациями."]}' \
  | python3 -m json.tool
```

OpenAI-compatible endpoint:

```bash
curl -sS \
  -X POST "http://localhost:8200/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-m3","input":["Smoke test embeddings ПрофИИта."]}' \
  | python3 -m json.tool
```

## Интеграция С RAGFlow

Для RAGFlow в Docker на macOS/Windows используйте:

```env
RAGFLOW_EMBEDDING_BASE_URL=http://host.docker.internal:8200/v1
RAGFLOW_EMBEDDING_MODEL=BAAI/bge-m3
RAGFLOW_EMBEDDING_API_KEY=local-dev-key
```

Если оба сервиса находятся в одной Docker network, используйте имя TEI container/service вместо `host.docker.internal`.

Источники: [Hugging Face TEI docs](https://huggingface.co/docs/text-embeddings-inference), [TEI Quick Tour](https://huggingface.co/docs/text-embeddings-inference/quick_tour), [TEI OpenAPI docs](https://huggingface.github.io/text-embeddings-inference/).
