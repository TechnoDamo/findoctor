# Тестирование backend

Backend тестируется как интеграционный API-сервис: FastAPI вызывается через `httpx`, а данные пишутся в реальную PostgreSQL test DB. Это медленнее чистых unit-тестов, зато хорошо ловит ошибки миграций, SQL, авторизации и контрактов.

## Быстрый запуск

```bash
cd backend
./.venv/bin/python -m compileall -q app tests scripts
./.venv/bin/ruff check app tests scripts
./.venv/bin/pytest tests/ -q
```

Через Makefile:

```bash
cd backend
make test
```

`make test` запускает lint, compile, reset test DB и pytest.

## Требования

- PostgreSQL доступен на тестовых настройках из `tests/conftest.py`.
- Alembic-миграции применимы к test DB.
- Python-зависимости установлены в `.venv` или доступны через `uv`.

По умолчанию тестовая БД называется `findoctor_test`. Можно переопределить:

```bash
TEST_POSTGRES_DB=findoctor_test
TEST_DATABASE_URL=postgresql+psycopg://...
TEST_PSYCOPG_DSN=postgres://...
```

## Структура

```text
backend/tests/
  conftest.py                         # фикстуры, миграции, очистка БД
  test_auth.py                        # базовый auth flow
  test_auth_comprehensive.py          # auth + проверка состояния БД
  test_authorization_boundaries.py    # cross-user isolation
  test_openapi_contract.py            # parity FastAPI routes и OpenAPI YAML
  test_smoke_e2e.py                   # полный lifecycle пользователя
  test_recommendations.py             # recommendation planner/tools
  test_user_data_tool.py              # внутренний finance data tool
  ...
```

## Что покрываем

- Регистрация, логин, refresh, logout.
- Хеширование паролей и хранение refresh-token hash.
- Защищенные endpoints и отсутствие чувствительных полей в API.
- CRUD счетов, операций, переводов, активов, обязательств, целей, тегов.
- Переводы как атомарная связка `transfer + debit transaction + credit transaction`.
- Платежи по обязательствам и автоматическое создание transaction.
- Аналитика: dashboard, cash-flow, net-worth, snapshots.
- AI chat: сообщения, диалоги, голосовой сценарий, agentic режим.
- OpenAPI-контракт: количество и набор операций должны совпадать с FastAPI.
- Изоляция пользователей: чужие UUID возвращают `404`.

## Команды Makefile

| Команда | Назначение |
| --- | --- |
| `make test` | полный backend gate |
| `make test-unit` | только pytest |
| `make test-auth` | auth-тесты |
| `make test-accounts` | тесты счетов |
| `make test-comprehensive` | расширенные auth-тесты с БД-проверками |
| `make test-coverage` | pytest с coverage report |
| `make lint` | Ruff |
| `make compile` | compileall |
| `make contract-check` | только OpenAPI parity |

## Фикстуры

| Фикстура | Что дает |
| --- | --- |
| `test_client` | `httpx.AsyncClient` поверх FastAPI ASGI app |
| `db_connection` | чистое PostgreSQL-соединение для прямых проверок |
| `register_data` | стандартный payload регистрации |
| `auth_headers` | bearer headers для тестового пользователя |

База очищается до и после каждого теста. Справочники, засеянные миграциями, сохраняются.

## Как писать новые тесты

Минимальный API-тест:

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_endpoint(test_client: AsyncClient, auth_headers: dict) -> None:
    response = await test_client.get("/api/v1/accounts", headers=auth_headers)
    assert response.status_code == 200
    assert "items" in response.json()
```

Тест с прямой проверкой БД:

```python
async def test_database_state(test_client, db_connection, auth_headers):
    response = await test_client.post("/api/v1/tags", json={"name": "важное"}, headers=auth_headers)
    assert response.status_code == 201

    async with db_connection.cursor() as cur:
        await cur.execute("SELECT name FROM tags WHERE id = %s", (response.json()["id"],))
        row = await cur.fetchone()
        assert row["name"] == "важное"
```

## Обязательные проверки для финансовых endpoints

Для каждого нового пользовательского ресурса добавляйте:

- happy path create/list/get/update/delete;
- unauthorized request без bearer token;
- cross-user test: User A создает ресурс, User B получает `404` на get/update/delete;
- проверку OpenAPI-контракта, если меняется route surface;
- проверку БД-инвариантов, если операция затрагивает несколько таблиц.

## Перед демо или PR

```bash
cd backend
./.venv/bin/pytest tests/ -q

cd ../frontend
npm audit --audit-level=moderate
npm run build
```

Ожидаемый здоровый результат на текущем состоянии проекта: полный backend suite проходит, npm audit не находит уязвимостей, frontend production build собирается.
