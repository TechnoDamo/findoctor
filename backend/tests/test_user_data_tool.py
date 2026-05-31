"""Tests for user_data_tool: domain handlers, aggregation, isolation, error handling."""

import pytest
from psycopg import AsyncConnection

from app.db.operations import execute, fetchrow
from app.db.pool import LoggedConnection
from app.services.recommendations.schemas import (
    UserDataQuery,
    UserDataToolPlan,
)
from app.services.recommendations.user_data_tool import (
    _DOMAIN_HANDLERS,
    execute_user_data_queries,
)

pytestmark = pytest.mark.anyio


def _wrap(conn: AsyncConnection) -> LoggedConnection:
    return LoggedConnection(conn)


async def _seed_user(conn: AsyncConnection, email: str = "tool-test@example.com", base_currency: str = "RUB") -> dict:
    from app.core.security import hash_password
    return await fetchrow(conn,
        "INSERT INTO users (email, password_hash, phone, first_name, last_name, country, base_currency, timezone, created_at, updated_at)"
        " VALUES (%(e)s, %(ph)s, '+79001234567', 'Test', 'User', 'RU', %(bc)s, 'Europe/Moscow', now(), now())"
        " RETURNING id",
        {"e": email, "ph": hash_password("test123"), "bc": base_currency},
    )


async def _seed_accounts(conn: AsyncConnection, user_id: str) -> tuple[str, str]:
    row = await fetchrow(conn, "SELECT id FROM account_types LIMIT 1")
    at_id = row["id"] if row else None
    a1 = await fetchrow(conn,
        "INSERT INTO accounts (user_id, account_type_id, name, currency, balance, created_at, updated_at)"
        " VALUES (%(u)s, %(at)s, 'Дебетовая карта', 'RUB', '100000.00', now(), now()) RETURNING id",
        {"u": user_id, "at": at_id},
    )
    a2 = await fetchrow(conn,
        "INSERT INTO accounts (user_id, account_type_id, name, currency, balance, created_at, updated_at)"
        " VALUES (%(u)s, %(at)s, 'Накопительный счёт', 'RUB', '50000.00', now(), now()) RETURNING id",
        {"u": user_id, "at": at_id},
    )
    return a1["id"], a2["id"]


async def _seed_transactions(conn: AsyncConnection, user_id: str, account_id: str) -> None:
    await execute(conn,
        "INSERT INTO transactions (user_id, account_id, type, amount, currency,"
        " transaction_datetime, description, created_at)"
        " VALUES (%(u)s, %(a)s, 'expense', '2500.00', 'RUB', '2025-06-01T12:00:00Z', 'Обед в Кофемании', now()),"
        " (%(u)s, %(a)s, 'expense', '1500.00', 'RUB', '2025-06-03T18:00:00Z', 'Такси до дома', now()),"
        " (%(u)s, %(a)s, 'income', '80000.00', 'RUB', '2025-06-05T10:00:00Z', 'Зарплата', now()),"
        " (%(u)s, %(a)s, 'expense', '1200.00', 'RUB', '2025-06-10T09:00:00Z', 'Продукты в Перекрёстке', now()),"
        " (%(u)s, %(a)s, 'expense', '3000.00', 'RUB', '2025-06-15T14:00:00Z', 'Ресторан', now())",
        {"u": user_id, "a": account_id},
    )


async def _seed_reference(conn: AsyncConnection) -> None:
    for name, typ in [("Продукты", "expense"), ("Рестораны", "expense"), ("Зарплата", "income"), ("Транспорт", "expense")]:
        await execute(conn, "INSERT INTO categories (name, type) VALUES (%(n)s, %(t)s) ON CONFLICT DO NOTHING",
                      {"n": name, "t": typ})
    for name, country, risk in [("Перекрёсток", "RU", "low"), ("Яндекс.Такси", "RU", "low"), ("Кофемания", "RU", "low")]:
        await execute(conn, "INSERT INTO merchants (name, country, risk_level) VALUES (%(n)s, %(c)s, %(r)s) ON CONFLICT DO NOTHING",
                      {"n": name, "c": country, "r": risk})


class TestDomainHandlers:
    async def test_all_domains_have_handler(self) -> None:
        valid_domains = [
            "accounts", "transactions", "transfers", "assets",
            "liabilities", "liability_payments", "recurring_transactions",
            "goals", "tags", "dashboard_summary", "cash_flow",
            "net_worth", "snapshots", "account_types", "asset_types",
            "liability_types", "provider_types", "categories",
            "merchants", "financial_institutions", "conversation_history",
        ]
        missing = [d for d in valid_domains if d not in _DOMAIN_HANDLERS]
        assert not missing, f"Missing handlers: {missing}"

    async def test_query_unknown_domain_returns_error(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        query = UserDataQuery(domain="nonexistent_domain")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert len(results) == 1
        assert results[0].error is not None

    async def test_query_accounts_returns_data(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        await _seed_accounts(db_connection, user["id"])
        query = UserDataQuery(domain="accounts", aggregation="none")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert len(results) == 1
        assert results[0].count == 2
        assert not results[0].error

    async def test_query_transactions_with_filter(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(
            domain="transactions",
            filters={"date_from": "2025-06-01", "date_to": "2025-06-30"},
            aggregation="none",
        )
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert len(results) == 1
        assert results[0].count == 5

    async def test_query_transactions_aggregation_sum(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(
            domain="transactions",
            filters={"operation_type": "expense"},
            aggregation="sum",
            aggregation_field="amount",
        )
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        data = results[0].data
        assert float(data["sum"]) == 8200.0

    async def test_query_transactions_aggregation_count(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(domain="transactions", filters={"operation_type": "income"}, aggregation="count")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].data["count"] == 1

    async def test_query_transactions_group_by(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(
            domain="transactions",
            aggregation="group_by",
            group_by_field="type",
        )
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        groups = results[0].data
        assert groups["income"] == 1
        assert groups["expense"] == 4

    async def test_query_transactions_top_n(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(
            domain="transactions", aggregation="top_n",
            sort_field="amount", sort_order="desc", limit=2,
        )
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 2

    async def test_user_id_isolation(self, db_connection: AsyncConnection) -> None:
        user1 = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user1["id"])
        await _seed_transactions(db_connection, user1["id"], a1)
        user2 = await _seed_user(db_connection, email="other@example.com", base_currency="USD")
        query = UserDataQuery(domain="transactions", aggregation="count")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user2["id"], plan)
        assert results[0].data["count"] == 0

    async def test_reference_domains_return_catalogs(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        for domain in ["account_types", "asset_types", "liability_types", "provider_types", "categories", "merchants"]:
            query = UserDataQuery(domain=domain)
            plan = UserDataToolPlan(queries=[query])
            results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
            assert not results[0].error, f"{domain}: {results[0].error}"

    async def test_categories_filtered_by_type(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        await _seed_reference(db_connection)
        query = UserDataQuery(domain="categories", filters={"type": "expense"})
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        data = results[0].data
        assert len(data) >= 3

    async def test_parallel_queries(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        await _seed_reference(db_connection)
        queries = [
            UserDataQuery(domain="accounts", aggregation="count"),
            UserDataQuery(domain="transactions", aggregation="count"),
            UserDataQuery(domain="categories", aggregation="count"),
        ]
        plan = UserDataToolPlan(queries=queries)
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert len(results) == 3
        assert all(not r.error for r in results)
        assert results[0].data["count"] == 2
        assert results[1].data["count"] == 5
        assert results[2].data["count"] >= 3

    async def test_invalid_aggregation_falls_back(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        await _seed_accounts(db_connection, user["id"])
        query = UserDataQuery(domain="accounts", aggregation="invalid_agg")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert not results[0].error
        assert results[0].count >= 2

    async def test_limit_respected(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(domain="transactions", limit=2, aggregation="none")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 2

    async def test_name_search_filter_works(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        await _seed_accounts(db_connection, user["id"])
        query = UserDataQuery(domain="accounts", filters={"name_search": "накопит"}, aggregation="none")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 1

    async def test_tags_domain_works(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        await execute(db_connection,
            "INSERT INTO tags (user_id, name) VALUES (%(u)s, 'еда') ON CONFLICT DO NOTHING",
            {"u": user["id"]},
        )
        query = UserDataQuery(domain="tags", filters={"name_search": "еда"})
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 1

    async def test_goals_domain_with_filter(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        await execute(db_connection,
            "INSERT INTO financial_goals (user_id, name, target_amount, current_amount, priority, created_at, updated_at)"
            " VALUES (%(u)s, 'Купить машину', '1000000.00', '200000.00', 1, now(), now())",
            {"u": user["id"]},
        )
        query = UserDataQuery(domain="goals", filters={"name_search": "машин"})
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 1

    async def test_dashboard_summary(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(domain="dashboard_summary", filters={"base_currency": "RUB"})
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert not results[0].error

    async def test_cash_flow_domain(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await _seed_transactions(db_connection, user["id"], a1)
        query = UserDataQuery(domain="cash_flow", filters={"date_from": "2025-06-01", "date_to": "2025-06-30"})
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert not results[0].error

    async def test_assets_domain(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        row = await fetchrow(db_connection, "SELECT id FROM asset_types LIMIT 1")
        await execute(db_connection,
            "INSERT INTO assets (user_id, asset_type_id, name, estimated_value, currency, purchase_price, purchase_date, created_at, updated_at)"
            " VALUES (%(u)s, %(at)s, 'Квартира', '5000000.00', 'RUB', '4000000.00', '2023-01-15', now(), now())",
            {"u": user["id"], "at": row["id"]},
        )
        query = UserDataQuery(domain="assets", aggregation="none")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 1
        assert not results[0].error

    async def test_liabilities_domain(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        row = await fetchrow(db_connection, "SELECT id FROM liability_types LIMIT 1")
        await execute(db_connection,
            "INSERT INTO liabilities (user_id, liability_type_id, name, current_balance, currency, interest_rate, minimum_payment_amount, payment_due_day, created_at, updated_at)"
            " VALUES (%(u)s, %(lt)s, 'Ипотека', '3000000.00', 'RUB', 9.5, '30000.00', 10, now(), now())",
            {"u": user["id"], "lt": row["id"]},
        )
        query = UserDataQuery(domain="liabilities", aggregation="none")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 1
        assert not results[0].error

    async def test_recurring_transactions_domain(self, db_connection: AsyncConnection) -> None:
        user = await _seed_user(db_connection)
        a1, _ = await _seed_accounts(db_connection, user["id"])
        await execute(db_connection,
            "INSERT INTO recurring_transactions (user_id, account_id, operation_type, name, expected_amount, currency,"
            " frequency, day_of_month, start_date, next_payment_date)"
            " VALUES (%(u)s, %(a)s, 'expense', 'Аренда квартиры', '45000.00', 'RUB', 'monthly', 5, '2025-01-01', '2025-07-05')",
            {"u": user["id"], "a": a1},
        )
        query = UserDataQuery(domain="recurring_transactions", aggregation="none")
        plan = UserDataToolPlan(queries=[query])
        results = await execute_user_data_queries(_wrap(db_connection), user["id"], plan)
        assert results[0].count == 1
        assert not results[0].error
