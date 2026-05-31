# SearXNG

Внутренний self-hosted сервис поиска для ПрофИИта.

SearXNG нужен только для поиска новых URL. Он не решает, каким источникам можно доверять. Backend ПрофИИта обязан фильтровать каждый найденный URL через `ragflow/allowed_resources.txt`.

Интеграция backend описана в `../backend/docs/recommendations.md`.

```text
planner search_queries
  -> SearXNG /search?format=json
  -> backend фильтрует URL через allowed_resources.txt
  -> backend загружает approved pages
  -> при необходимости отправляет их в RAGFlow
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
cd searxng
make init
make pull
make run
make test
```

URL сервиса:

```text
http://localhost:8201
```

## Файлы

```text
searxng/
├── .env.example
├── .env                    # локальный config, игнорируется git
├── Makefile
├── README.md
├── config/
│   ├── settings.yml.example # tracked template, JSON включен
│   └── settings.yml         # генерируется make init, игнорируется git
└── scripts/
    ├── common.sh
    ├── print_curl_examples.sh
    ├── test_allowed_query.sh
    ├── test_json_search.sh
    └── wait_for_searxng.sh
```

## Команды

| Команда | Назначение |
|---|---|
| `make init` | Создать `.env` и сгенерировать `SEARXNG_SECRET_KEY` |
| `make pull` | Скачать Docker image `searxng/searxng` |
| `make run` | Запустить контейнер |
| `make stop` | Остановить и удалить контейнер |
| `make restart` | Перезапустить контейнер |
| `make logs` | Смотреть логи |
| `make wait` | Дождаться готовности HTTP endpoint |
| `make test` | Запустить smoke tests JSON API |
| `make curl-examples` | Показать готовые curl-примеры |

## JSON API

`config/settings.yml` включает:

```yaml
search:
  formats:
    - html
    - json
```

Пример:

```bash
curl -sS -G "http://localhost:8201/search" \
  --data-urlencode "q=site:cbr.ru key rate" \
  --data-urlencode "format=json" \
  --data-urlencode "language=all" \
  | python3 -m json.tool
```

## Правило Безопасности Backend

SearXNG может вернуть страницы вне нужного набора источников. Backend adapter обязан:

1. прочитать `ragflow/allowed_resources.txt`;
2. нормализовать hosts;
3. отбросить запрещенные результаты;
4. загружать только allowed URL;
5. сохранить source URL, title, snippet, engine и timestamp в `tool_results`.

Источники: [SearXNG Docker install docs](https://docs.searxng.org/admin/installation-docker.html), [SearXNG Search API docs](https://docs.searxng.org/dev/search_api), [SearXNG settings docs](https://docs.searxng.org/admin/settings/settings.html).
