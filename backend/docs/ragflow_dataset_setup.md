# Настройка Dataset В RAGFlow

Этот документ описывает настройку базы знаний рекомендаций ПрофИИта в RAGFlow.

## Сервисы

Настройка из корня репозитория:

```bash
make init-recommendations
make pull-recommendations
make local-up-recommendations
```

Настройка по отдельным сервисам:

Сначала запустите embeddings:

```bash
cd tei
make init
make pull
make run
make test
```

Затем запустите RAGFlow:

```bash
cd ../ragflow
make init
make fetch
make configure
make up
make wait
```

Опциональный поиск новых URL:

```bash
cd ../searxng
make init
make pull
make run
make test
```

## Сервисный Аккаунт RAGFlow

Создайте один внутренний RAGFlow account/API key и храните его только на стороне сервера.

Запишите его сюда:

```env
# ragflow/.env
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...

# backend/.env
RAGFLOW_API_KEY=...
RAGFLOW_DATASET_ID=...
```

Не отдавайте этот ключ фронтенду.

## Embedding Provider

Используйте TEI как OpenAI-compatible endpoint для embeddings.

Для локального Docker на macOS/Windows:

```env
RAGFLOW_EMBEDDING_BASE_URL=http://host.docker.internal:8200/v1
RAGFLOW_EMBEDDING_MODEL=BAAI/bge-m3
RAGFLOW_EMBEDDING_API_KEY=local-dev-key
```

Для общей Docker network используйте service/container host TEI:

```env
RAGFLOW_EMBEDDING_BASE_URL=http://tei:80/v1
```

Рекомендуемая модель по умолчанию:

```text
BAAI/bge-m3
```

Более легкий CPU fallback:

```text
intfloat/multilingual-e5-small
```

## Настройки Dataset

Рекомендуемый dataset:

```text
name: findoctor-recommendations
language: Russian + English
purpose: approved educational and regulatory finance context
```

Рекомендуемые правила ingestion:

- по возможности использовать markdown/plain text;
- сохранять source URL в metadata;
- использовать умеренный размер chunks, пригодный для citations;
- не смешивать unrelated domains в одном документе;
- re-parse documents после смены embedding model;
- не загружать private financial data пользователя в общий recommendation dataset.

## Разрешенные Ресурсы

Временный allowlist находится здесь:

```text
ragflow/allowed_resources.txt
```

Для важных страниц лучше использовать точные URL. Domains используйте только там, где discovery допустим.

Примеры:

```txt
https://www.cbr.ru/
https://www.nalog.gov.ru/
https://journal.tinkoff.ru/
```

Правила backend:

- search может находить candidate URL;
- backend обязан отклонять URL вне allowlist;
- fetch и ingest разрешены только для approved pages;
- каждый финальный ответ должен сохранять metadata evidence в `tool_results`.

## Smoke Tests

После заполнения `.env`:

```bash
cd ragflow
make test
make test-upload
```

Ожидаемый результат:

- dataset listing проходит успешно;
- retrieval request возвращает JSON;
- sample document upload проходит успешно;
- parsing может зависеть от версии RAGFlow, но response должен показывать состояние документа.

## Проверка Backend

Включите рекомендации:

```env
RECOMMENDATIONS_ENABLED=true
```

Затем запустите:

```bash
cd backend
./.venv/bin/pytest tests/test_recommendations.py tests/test_ai_chat.py -q
```
