"""Репозиторий для аналитики: дашборд, снимки, денежный поток, капитал."""

from psycopg import AsyncConnection

from app.db.query_loader import load_queries

_queries = load_queries("analytics.sql")


async def get_dashboard_summary(
    conn: AsyncConnection, user_id: str, base_currency: str
) -> dict | None:
    """Сводка финансового состояния пользователя."""
    return await conn.fetchrow(
        _queries["dashboard_summary"],
        {"user_id": user_id, "base_currency": base_currency},
    )


async def list_snapshots(
    conn: AsyncConnection,
    user_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Список ежедневных финансовых снимков."""
    rows = await conn.fetch(
        _queries["list_snapshots"],
        {"user_id": user_id, "from": date_from, "to": date_to},
    )
    return list(rows)


async def recalculate_snapshots(
    conn: AsyncConnection, user_id: str, date_from: str, date_to: str
) -> None:
    """Очистка снимков за период (для последующего перерасчёта)."""
    await conn.execute(
        _queries["recalculate_snapshots"],
        {"user_id": user_id, "from": date_from, "to": date_to},
    )


async def insert_snapshot(conn: AsyncConnection, data: dict) -> None:
    """Вставка пересчитанного снимка."""
    await conn.execute(_queries["insert_snapshot"], data)


async def get_cash_flow(
    conn: AsyncConnection,
    user_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    group_by: str = "month",
) -> list[dict]:
    """Денежный поток по периодам."""
    rows = await conn.fetch(
        _queries["cash_flow"],
        {
            "user_id": user_id,
            "from": date_from,
            "to": date_to,
            "group_by": group_by,
        },
    )
    return list(rows)


async def get_net_worth(
    conn: AsyncConnection,
    user_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """История изменения чистого капитала."""
    rows = await conn.fetch(
        _queries["net_worth"],
        {"user_id": user_id, "from": date_from, "to": date_to},
    )
    return list(rows)
