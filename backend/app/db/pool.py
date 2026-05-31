"""
Пул соединений с PostgreSQL.

Использует psycopg_pool.ConnectionPool для управления соединениями.
Каждый HTTP-запрос получает своё соединение через FastAPI Depends.
"""

from collections.abc import AsyncGenerator
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.db.operations import execute, fetch, fetchrow
from app.settings import settings

_pool: AsyncConnectionPool | None = None


class LoggedConnection:
    """Proxy that logs all DB write statements executed through psycopg."""

    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    async def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if args or kwargs:
            cursor = await self._conn.execute(query, params, *args, **kwargs)
            return cursor
        return await execute(self._conn, query, params)

    async def fetch(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query and return all rows."""
        return await fetch(self._conn, query, params)

    async def fetchrow(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a query and return one row."""
        return await fetchrow(self._conn, query, params)

    def transaction(self, *args: Any, **kwargs: Any) -> Any:
        return self._conn.transaction(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


async def init_pool() -> None:
    """Инициализирует глобальный пул соединений (вызывается на старте приложения)."""
    global _pool
    _pool = AsyncConnectionPool(
        conninfo=settings.psycopg_dsn,
        min_size=2,
        max_size=10,
        open=False,
        kwargs={"row_factory": dict_row},
    )
    await _pool.open()
    await _pool.wait()


async def close_pool() -> None:
    """Закрывает глобальный пул соединений (вызывается при остановке приложения)."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_connection() -> AsyncGenerator[AsyncConnection, None]:
    """FastAPI-зависимость: предоставляет соединение на время одного запроса."""
    if _pool is None:
        raise RuntimeError("Пул соединений не инициализирован")
    async with _pool.connection() as conn:
        async with conn.transaction():
            yield LoggedConnection(conn)
