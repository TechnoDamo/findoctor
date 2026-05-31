# Локальный запуск PostgreSQL

Короткая инструкция для запуска PostgreSQL в Docker с данными из `.env` в корне проекта.

Команды рассчитаны на уже загруженный образ `postgres:16-alpine`.

---

## 1. Переменные окружения

В корне проекта должен быть файл `.env`:

```bash
POSTGRES_DB=findoctor
POSTGRES_USER=findoctor
POSTGRES_PASSWORD=change_me
POSTGRES_PORT=5432
```

Файл `.env` не коммитится в Git.

---

## 2. Запустить PostgreSQL

Выполнять из корня проекта:

```bash
set -a
source .env
set +a

mkdir -p db/postgres-data

docker run -d \
  --name findoctor-postgres \
  --env-file .env \
  -p "${POSTGRES_PORT:-5432}:5432" \
  -v "$(pwd)/db/postgres-data:/var/lib/postgresql/data" \
  postgres:16-alpine
```

Данные PostgreSQL будут храниться локально в `db/postgres-data`.

---

## 3. Проверить статус

```bash
docker ps --filter name=findoctor-postgres
```

```bash
docker logs -f findoctor-postgres
```

---

## 4. Подключиться через psql внутри контейнера

```bash
set -a
source .env
set +a

docker exec -it findoctor-postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

---

## 5. Connection string

Для локальных инструментов, включая ChartDB:

```bash
postgresql://findoctor:change_me@localhost:5432/findoctor
```

Если значения в `.env` другие:

```bash
set -a
source .env
set +a

echo "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT:-5432}/${POSTGRES_DB}"
```

---

## 6. Остановить и запустить снова

```bash
docker stop findoctor-postgres
```

```bash
docker start findoctor-postgres
```

---

## 7. Удалить контейнер без удаления данных

```bash
docker stop findoctor-postgres
docker rm findoctor-postgres
```

Данные останутся в `db/postgres-data`.

---

## 8. Полностью удалить локальную базу

Осторожно: команда удалит все локальные данные PostgreSQL.

```bash
docker stop findoctor-postgres || true
docker rm findoctor-postgres || true
rm -rf db/postgres-data
```

---

## 9. Сделать backup

```bash
set -a
source .env
set +a

mkdir -p db/backups

docker exec findoctor-postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  > "db/backups/findoctor_$(date +%Y%m%d_%H%M%S).sql"
```

---

## 10. Восстановить backup

Указать нужный файл вместо `db/backups/findoctor_backup.sql`:

```bash
set -a
source .env
set +a

cat db/backups/findoctor_backup.sql | docker exec -i findoctor-postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

---

## 11. Применить SQL из DBML

Если из `db/schema.dbml` сгенерирован SQL-файл, например `db/schema.sql`:

```bash
set -a
source .env
set +a

cat db/schema.sql | docker exec -i findoctor-postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

---

## 12. Частые проблемы

Если порт занят, измените `POSTGRES_PORT` в `.env`, например:

```bash
POSTGRES_PORT=5433
```

Если контейнер уже существует:

```bash
docker start findoctor-postgres
```

Если нужно пересоздать контейнер, но сохранить данные:

```bash
docker stop findoctor-postgres || true
docker rm findoctor-postgres || true

set -a
source .env
set +a

docker run -d \
  --name findoctor-postgres \
  --env-file .env \
  -p "${POSTGRES_PORT:-5432}:5432" \
  -v "$(pwd)/db/postgres-data:/var/lib/postgresql/data" \
  postgres:16-alpine
```
