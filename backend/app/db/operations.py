"""Small psycopg helpers with asyncpg-like fetch helpers."""

import re
import time
from typing import Any

import structlog
from psycopg import AsyncConnection

from app.settings import settings

logger = structlog.get_logger("db")

_WRITE_PATTERN = re.compile(
    r"^\s*(?:--.*?\n\s*)*(insert|update|delete|merge|create|alter|drop|truncate)\b",
    re.IGNORECASE | re.DOTALL,
)
_TABLE_PATTERN = re.compile(
    r"\b(?:into|update|from|table)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)",
    re.IGNORECASE,
)


async def fetchrow(
    conn: AsyncConnection,
    query: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Execute a query and return one row."""
    cursor = await conn.execute(query, params)
    return await cursor.fetchone()


async def fetch(
    conn: AsyncConnection,
    query: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute a query and return all rows."""
    cursor = await conn.execute(query, params)
    return await cursor.fetchall()


async def execute(
    conn: AsyncConnection,
    query: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Execute SQL and log write operations."""
    started_at = time.perf_counter()
    cursor = await conn.execute(query, params)
    _log_write(query, params, cursor.rowcount, started_at)
    return cursor


def _log_write(
    query: str,
    params: dict[str, Any] | None,
    rowcount: int,
    started_at: float,
) -> None:
    if not settings.log_db_writes:
        return

    match = _WRITE_PATTERN.search(query)
    if not match:
        return

    table_match = _TABLE_PATTERN.search(query)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
    logger.info(
        "db_write",
        operation=match.group(1).lower(),
        table=table_match.group(1) if table_match else None,
        rowcount=rowcount,
        duration_ms=duration_ms,
        params_keys=sorted(params.keys()) if isinstance(params, dict) else None,
    )
