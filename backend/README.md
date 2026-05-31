# Backend ПрофИИта

FastAPI backend обслуживает клиентский API, применяет Alembic-миграции, работает с PostgreSQL через явный SQL и оркестрирует AI/recommendation-сценарии. Этот README сфокусирован на практическом запуске backend из текущей директории, без корневого compose и без frontend.

## Быстрый Docker-запуск из `backend/`

Минимальный рабочий путь:

```bash
cd backend
make init-env
make db-up
make docker-up
make docker-smoke
```

Что произойдёт:

- `make init-env` создаст `.env` из `.env.example`, если файла ещё нет;
- `make db-up` поднимет локальный PostgreSQL container `findoctor-postgres`;
- `make docker-up` соберёт image `findoctor-backend:local` и запустит container `findoctor-backend`;
- entrypoint выполнит `alembic upgrade head`, потому что для контейнера выставляется `RUN_MIGRATIONS=true`;
- `make docker-smoke` проверит публичный справочный endpoint `/api/v1/reference/account-types`.

После запуска API доступен по адресу:

```text
http://localhost:8001/api/v1
```

Проверка руками:

```bash
curl http://localhost:8001/api/v1/reference/account-types
```

## Docker-команды

| Команда | Назначение |
| --- | --- |
| `make docker-build` | Собрать backend image из директории `backend/`. |
| `make docker-up` | Собрать image и перезапустить backend container. |
| `make docker-run` | Запустить уже собранный image против локальной PostgreSQL. |
| `make docker-smoke` | Проверить, что контейнер отвечает через HTTP. |
| `make docker-logs` | Смотреть логи backend container. |
| `make docker-shell` | Открыть shell внутри запущенного container. |
| `make docker-stop` | Остановить и удалить backend container. |
| `make docker-clean` | Удалить container и локальный image. |

По умолчанию используются:

```text
Image:      findoctor-backend:local
Container:  findoctor-backend
Host port:  8001
App port:   8000
DB host:    host.docker.internal
DB port:    значение POSTGRES_PORT из .env
```

Переопределение без правки Makefile передаётся как аргументы `make`, потому что `.env` подключается самим Makefile:

```bash
make DOCKER_IMAGE=findoctor-backend:demo DOCKER_HOST_PORT=8010 docker-up
```

## Почему контейнер ходит в БД через `host.docker.internal`

`make db-up` запускает PostgreSQL отдельным container с пробросом порта на host. Backend container стартует отдельно, не в той же compose-сети, поэтому для него `localhost` означает сам backend container, а не PostgreSQL.

Makefile явно передаёт:

```text
POSTGRES_HOST=host.docker.internal
DATABASE_URL=postgresql+psycopg://...@host.docker.internal:PORT/DB
```

Так один и тот же backend image можно быстро гонять из `backend/`, не поднимая весь стек. Для root `docker-compose.yml` используется другой режим: backend и PostgreSQL находятся в одной compose-сети, поэтому compose передаёт `POSTGRES_HOST=postgres`.

## Локальный запуск без Docker

Если нужен reload и обычная разработка Python-кода:

```bash
cd backend
make init-env
make db-up
make migrate
make run
```

По умолчанию `make run` запускает:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Порт можно переопределить:

```bash
APP_PORT=8002 make run
```

## Миграции

Применить текущие миграции:

```bash
make migrate
```

Создать новую пустую миграцию:

```bash
make migration m="add payment schedule"
```

Проверить текущую ревизию:

```bash
make db-current
```

Правило проекта: изменение структуры БД должно быть отражено в Alembic-миграции и в `../db/schema.dbml`.

## Тестовый gate

Полная backend-проверка:

```bash
make test
```

Она запускает Ruff, compileall, reset test DB и pytest. Для быстрой проверки отдельных зон:

```bash
make test-auth
make test-accounts
make contract-check
```

Подробнее о тестовой стратегии: [`TESTING.md`](TESTING.md).

## Частые сбои

Если backend container сразу падает, сначала смотрите логи:

```bash
make docker-logs
```

Если в логах ошибка подключения к PostgreSQL:

```bash
make db-up
docker ps --filter name=findoctor-postgres
```

Если порт `8001` занят:

```bash
make DOCKER_HOST_PORT=8010 docker-up
curl http://localhost:8010/api/v1/reference/account-types
```

Если миграции не применяются, проверьте, что container получает `RUN_MIGRATIONS=true`. В штатном `make docker-run` это уже выставлено.
