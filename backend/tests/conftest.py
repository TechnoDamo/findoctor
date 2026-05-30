"""
Фикстуры для тестов.

Каждый тест работает с реальной PostgreSQL базой через Docker.
База очищается после каждого теста для изоляции.
"""

import os
import asyncio
from collections.abc import AsyncGenerator

os.environ["APP_ENV"] = "test"
os.environ["POSTGRES_HOST"] = os.environ.get("POSTGRES_HOST", "localhost")
os.environ["POSTGRES_PORT"] = os.environ.get("POSTGRES_PORT", "5433")
os.environ["POSTGRES_DB"] = os.environ.get("TEST_POSTGRES_DB", "findoctor_test")
os.environ["POSTGRES_USER"] = os.environ.get("POSTGRES_USER", "findoctor")
os.environ["POSTGRES_PASSWORD"] = os.environ.get("POSTGRES_PASSWORD", "change_me")
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://"
    f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
)
os.environ["GRAYLOG_ENABLED"] = "false"

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from psycopg import AsyncConnection
from psycopg.rows import dict_row

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ["DATABASE_URL"],
)
TEST_PSYCOPG_DSN = os.environ.get(
    "TEST_PSYCOPG_DSN",
    (
        "postgres://"
        f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    ),
)

TEST_ALEMBIC_INI = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Применяет миграции Alembic к тестовой БД перед запуском тестов."""
    alembic_cfg = Config(TEST_ALEMBIC_INI)
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


async def _cleanup_database() -> None:
    tables = [
        "ai_chat_messages",
        "ai_chat_conversations",
        "transaction_tags",
        "liability_payments",
        "transactions",
        "transfers",
        "recurring_transactions",
        "financial_goals",
        "tags",
        "liabilities",
        "assets",
        "accounts",
        "auth_sessions",
        "users",
        "financial_institution_provider_types",
        "financial_institutions",
        "merchants",
    ]
    conn = await AsyncConnection.connect(TEST_PSYCOPG_DSN, autocommit=True)
    try:
        for table in tables:
            await conn.execute(f"DELETE FROM {table}")
    finally:
        await conn.close()


@pytest.fixture(autouse=True)
def clean_database() -> AsyncGenerator[None, None]:
    asyncio.run(_cleanup_database())
    yield
    asyncio.run(_cleanup_database())


@pytest.fixture()
async def db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Создаёт чистое соединение с БД для одного теста."""
    conn = await AsyncConnection.connect(
        TEST_PSYCOPG_DSN, row_factory=dict_row, autocommit=False
    )

    async with conn.transaction():
        yield conn


@pytest.fixture()
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Создаёт HTTP-клиент для тестирования API."""
    from app.main import app
    from app.db.pool import init_pool, close_pool
    
    # Manually initialize the connection pool
    await init_pool()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clean up
    await close_pool()


@pytest.fixture()
def register_data() -> dict:
    """Тестовые данные для регистрации."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "base_currency": "RUB",
        "timezone": "Europe/Moscow",
    }


@pytest.fixture()
async def auth_headers(test_client: AsyncClient, register_data: dict) -> dict[str, str]:
    """Получает заголовки авторизации для тестового пользователя."""
    resp = await test_client.post("/api/v1/auth/register", json=register_data)
    if resp.status_code == 409:
        resp = await test_client.post("/api/v1/auth/login", json={
            "email": register_data["email"],
            "password": register_data["password"],
        })
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}
