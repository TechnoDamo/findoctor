"""User data search tool — executes structured queries against the user's financial database.

The planner LLM generates ``UserDataQuery`` objects. This module dispatches them
to the appropriate repository, enforces user-id isolation, applies aggregations,
and formats results for LLM consumption.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from psycopg import AsyncConnection

from app.repositories import (
    accounts as accounts_repo,
    ai_chat as chat_repo,
    analytics as analytics_repo,
    assets as assets_repo,
    financial_institutions as fi_repo,
    goals as goals_repo,
    liabilities as liab_repo,
    liability_payments as lp_repo,
    recurring_transactions as rt_repo,
    reference as ref_repo,
    tags as tags_repo,
    transactions as txn_repo,
    transfers as transfer_repo,
)
from app.services.recommendations.schemas import (
    UserDataQuery,
    UserDataToolPlan,
    UserDataToolResult,
    VALID_AGGREGATIONS,
)

MAX_LIMIT = 250
EXECUTION_TIMEOUT = 5.0

_DOMAIN_HANDLERS: dict[str, Any] = {}


def _register(domain: str):
    def wrapper(fn):
        _DOMAIN_HANDLERS[domain] = fn
        return fn
    return wrapper


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def execute_user_data_queries(
    conn: AsyncConnection,
    user_id: str,
    plan: UserDataToolPlan,
    defaults: dict | None = None,
) -> list[UserDataToolResult]:
    """Execute all queries in parallel and return formatted results."""
    defaults = defaults or {}
    tasks = [
        _execute_one(conn, user_id, query, defaults)
        for query in plan.queries
    ]
    results = await asyncio.wait_for(
        asyncio.gather(*tasks, return_exceptions=True),
        timeout=EXECUTION_TIMEOUT * len(plan.queries),
    )
    return _unwrap_results(results, plan.queries)


async def _execute_one(
    conn: AsyncConnection,
    user_id: str,
    query: UserDataQuery,
    defaults: dict,
) -> UserDataToolResult:
    handler = _DOMAIN_HANDLERS.get(query.domain)
    if handler is None:
        return UserDataToolResult(
            domain=query.domain,
            query=query,
            data={"error": f"Unknown domain: {query.domain}"},
            count=0,
            error=f"Unknown domain: {query.domain}",
        )
    try:
        raw = await asyncio.wait_for(
            handler(conn, user_id, query, defaults),
            timeout=EXECUTION_TIMEOUT,
        )
        result = _apply_aggregation(raw, query)
        formatted = _format_for_llm(query.domain, result)
        count = _count_result(result)
        return UserDataToolResult(
            domain=query.domain,
            query=query,
            data=formatted,
            count=count,
        )
    except asyncio.TimeoutError:
        return UserDataToolResult(
            domain=query.domain,
            query=query,
            data={"error": "Query timed out"},
            count=0,
            error="Query timed out",
        )
    except Exception as exc:
        return UserDataToolResult(
            domain=query.domain,
            query=query,
            data={"error": str(exc)},
            count=0,
            error=str(exc),
        )


def _unwrap_results(results: list, queries: list[UserDataQuery]) -> list[UserDataToolResult]:
    out: list[UserDataToolResult] = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            out.append(UserDataToolResult(
                domain=queries[i].domain,
                query=queries[i],
                data={"error": str(r)},
                count=0,
                error=str(r),
            ))
        else:
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# Aggregation engine
# ---------------------------------------------------------------------------


def _apply_aggregation(rows: Any, query: UserDataQuery) -> list[dict] | dict:
    if query.aggregation == "none" or query.aggregation not in VALID_AGGREGATIONS:
        return rows[: query.limit] if isinstance(rows, list) else rows

    if not isinstance(rows, list):
        return rows

    if not rows:
        return [] if query.aggregation == "none" else _empty_agg(query)

    agg = query.aggregation
    field = query.aggregation_field

    if agg == "count":
        return {"count": len(rows)}

    if agg == "sum" and field:
        total = sum(_to_decimal(r.get(field, 0)) for r in rows if r.get(field) is not None)
        return {"sum": str(total), "items": len(rows)}

    if agg == "avg" and field:
        values = [_to_decimal(r.get(field, 0)) for r in rows if r.get(field) is not None]
        return {"avg": str(sum(values) / max(len(values), 1)), "items": len(values)} if values else {"avg": "0"}

    if agg == "min" and field:
        values = [(r.get(field, 0), r) for r in rows if r.get(field) is not None]
        if values:
            best = min(values, key=lambda v: _to_decimal(v[0]))
            return {"min": str(_to_decimal(best[0])), "item": best[1]}
        return {"min": "0"}

    if agg == "max" and field:
        values = [(r.get(field, 0), r) for r in rows if r.get(field) is not None]
        if values:
            best = max(values, key=lambda v: _to_decimal(v[0]))
            return {"max": str(_to_decimal(best[0])), "item": best[1]}
        return {"max": "0"}

    if agg == "group_by":
        gf = query.group_by_field or "category"
        groups: dict[str, list[dict]] = {}
        for r in rows:
            key = str(r.get(gf, "unknown"))
            groups.setdefault(key, []).append(r)
        return {k: len(v) for k, v in sorted(groups.items(), key=lambda x: -len(x[1]))}

    if agg == "top_n":
        sf = query.sort_field
        if sf:
            reverse = query.sort_order != "asc"
            sorted_rows = sorted(rows, key=lambda r: _to_decimal(r.get(sf, 0)), reverse=reverse)
        else:
            sorted_rows = rows
        return sorted_rows[: query.limit]

    return rows[: query.limit]


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(0)


def _empty_agg(query: UserDataQuery) -> dict:
    agg = query.aggregation
    if agg in {"sum", "avg"}:
        return {"sum": "0"} if agg == "sum" else {"avg": "0"}
    if agg in {"min", "max"}:
        return {"min": "0"} if agg == "min" else {"max": "0"}
    if agg == "count":
        return {"count": 0}
    if agg == "group_by":
        return {}
    return []


def _count_result(result: list[dict] | dict) -> int:
    if isinstance(result, list):
        return len(result)
    if isinstance(result, dict):
        return result.get("items", result.get("count", 1))
    return 0


# ---------------------------------------------------------------------------
# LLM formatters
# ---------------------------------------------------------------------------


def _format_for_llm(domain: str, result: list[dict] | dict) -> list[dict] | dict:
    return result


# ---------------------------------------------------------------------------
# User-owned data domains
# ---------------------------------------------------------------------------


@_register("accounts")
async def _query_accounts(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    filters = query.filters
    rows = await accounts_repo.list_accounts(
        conn,
        user_id=user_id,
        is_active=_bool_or_none(filters.get("is_active")),
        currency=filters.get("currency"),
    )
    if filters.get("name_search"):
        term = filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("name") or r.get("account_name") or "").lower()]
    if filters.get("institution_name"):
        term = filters["institution_name"].lower()
        rows = [r for r in rows if term in (r.get("institution_name") or "").lower()]
    if filters.get("balance_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("current_balance", 0)) >= _to_decimal(filters["balance_min"])]
    if filters.get("balance_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("current_balance", 0)) <= _to_decimal(filters["balance_max"])]
    return rows


@_register("transactions")
async def _query_transactions(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    filters = query.filters
    kwargs: dict[str, Any] = {
        "user_id": user_id,
        "page_size": min(query.limit, MAX_LIMIT),
        "from": filters.get("date_from") or filters.get("from"),
        "to": filters.get("date_to") or filters.get("to"),
        "type": filters.get("operation_type") or filters.get("type"),
        "account_id": filters.get("account_id"),
        "category_id": filters.get("category_id"),
        "merchant_id": filters.get("merchant_id"),
        "recurring_transaction_id": filters.get("recurring_transaction_id"),
        "tag_id": filters.get("tag_id"),
    }
    rows, _ = await txn_repo.list_transactions(conn, **kwargs)
    if filters.get("category_name"):
        term = filters["category_name"].lower()
        rows = [r for r in rows if term in (r.get("category_name") or "").lower()]
    if filters.get("merchant_name"):
        term = filters["merchant_name"].lower()
        rows = [r for r in rows if term in (r.get("merchant_name") or "").lower()]
    if filters.get("tag_name"):
        term = filters["tag_name"].lower()
        rows = [r for r in rows if any(term in (t.get("name") or "").lower() for t in (r.get("tags") or []))]
    if filters.get("account_name"):
        term = filters["account_name"].lower()
        rows = [r for r in rows if term in (r.get("account_name") or r.get("name") or "").lower()]
    if filters.get("amount_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("amount", 0)) >= _to_decimal(filters["amount_min"])]
    if filters.get("amount_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("amount", 0)) <= _to_decimal(filters["amount_max"])]
    if filters.get("description_search"):
        term = filters["description_search"].lower()
        rows = [r for r in rows if term in (r.get("description") or "").lower()]
    return rows


@_register("transfers")
async def _query_transfers(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    kwargs: dict[str, Any] = {"user_id": user_id, "page_size": min(query.limit, MAX_LIMIT)}
    for k in ("date_from", "date_to", "account_id", "currency"):
        if k in query.filters:
            kwargs[k] = query.filters[k]
    rows, _ = await transfer_repo.list_transfers(conn, **kwargs)
    if query.filters.get("account_name"):
        term = query.filters["account_name"].lower()
        rows = [r for r in rows if term in (r.get("source_account_name") or "").lower()
                or term in (r.get("destination_account_name") or "").lower()]
    if query.filters.get("amount_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("amount", 0)) >= _to_decimal(query.filters["amount_min"])]
    if query.filters.get("amount_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("amount", 0)) <= _to_decimal(query.filters["amount_max"])]
    return rows


@_register("assets")
async def _query_assets(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    rows = await assets_repo.list_assets(conn, user_id)
    filters = query.filters
    if filters.get("asset_type_name"):
        term = filters["asset_type_name"].lower()
        rows = [r for r in rows if term in (_single_field(r, "asset_type_name") or "").lower()]
    if filters.get("name_search"):
        term = filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("asset_name") or r.get("name") or "").lower()]
    if filters.get("value_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("estimated_value", 0)) >= _to_decimal(filters["value_min"])]
    if filters.get("value_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("estimated_value", 0)) <= _to_decimal(filters["value_max"])]
    if filters.get("currency"):
        rows = [r for r in rows if (r.get("currency") or "").upper() == filters["currency"].upper()]
    if filters.get("purchase_date_from"):
        rows = [r for r in rows if (r.get("purchase_date") or "") >= filters["purchase_date_from"]]
    if filters.get("purchase_date_to"):
        rows = [r for r in rows if (r.get("purchase_date") or "") <= filters["purchase_date_to"]]
    return rows


@_register("liabilities")
async def _query_liabilities(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    filters = query.filters
    status = filters.get("status") if filters.get("status") in {"active", "repaid"} else None
    rows = await liab_repo.list_liabilities(conn, user_id, status=status)
    if filters.get("liability_type_name"):
        term = filters["liability_type_name"].lower()
        rows = [r for r in rows if term in (_single_field(r, "liability_type_name") or "").lower()]
    if filters.get("name_search"):
        term = filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("liability_name") or r.get("name") or "").lower()]
    if filters.get("balance_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("current_balance", 0)) >= _to_decimal(filters["balance_min"])]
    if filters.get("balance_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("current_balance", 0)) <= _to_decimal(filters["balance_max"])]
    if filters.get("interest_rate_min") is not None:
        rows = [r for r in rows if float(r.get("interest_rate", 0)) >= float(filters["interest_rate_min"])]
    if filters.get("interest_rate_max") is not None:
        rows = [r for r in rows if float(r.get("interest_rate", 0)) <= float(filters["interest_rate_max"])]
    if filters.get("currency"):
        rows = [r for r in rows if (r.get("currency") or "").upper() == filters["currency"].upper()]
    return rows


@_register("liability_payments")
async def _query_liability_payments(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    kwargs: dict[str, Any] = {"user_id": user_id}
    for k in ("date_from", "date_to", "liability_id", "account_id", "currency"):
        if k in query.filters:
            kwargs[k] = query.filters[k]
    rows = await lp_repo.list_liability_payments(conn, **kwargs)
    if query.filters.get("liability_name"):
        term = query.filters["liability_name"].lower()
        rows = [r for r in rows if term in (r.get("liability_name") or "").lower()]
    if query.filters.get("account_name"):
        term = query.filters["account_name"].lower()
        rows = [r for r in rows if term in (r.get("account_name") or "").lower()]
    if query.filters.get("amount_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("total_amount", 0)) >= _to_decimal(query.filters["amount_min"])]
    if query.filters.get("amount_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("total_amount", 0)) <= _to_decimal(query.filters["amount_max"])]
    return rows


@_register("recurring_transactions")
async def _query_recurring_transactions(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    kwargs: dict[str, Any] = {
        "user_id": user_id,
        "is_active": _bool_or_none(query.filters.get("is_active")),
        "account_id": query.filters.get("account_id"),
        "liability_id": query.filters.get("liability_id"),
        "next_payment_before": query.filters.get("next_payment_before"),
    }
    rows = await rt_repo.list_recurring_transactions(conn, **kwargs)
    if query.filters.get("name_search"):
        term = query.filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("name") or "").lower()]
    if query.filters.get("amount_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("expected_amount", 0)) >= _to_decimal(query.filters["amount_min"])]
    if query.filters.get("amount_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("expected_amount", 0)) <= _to_decimal(query.filters["amount_max"])]
    return rows


@_register("goals")
async def _query_goals(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    rows = await goals_repo.list_goals(conn, user_id)
    if query.filters.get("name_search"):
        term = query.filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("name") or "").lower()]
    if query.filters.get("target_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("target_amount", 0)) >= _to_decimal(query.filters["target_min"])]
    if query.filters.get("target_max") is not None:
        rows = [r for r in rows if _to_decimal(r.get("target_amount", 0)) <= _to_decimal(query.filters["target_max"])]
    if query.filters.get("priority"):
        rows = [r for r in rows if r.get("priority") == query.filters["priority"]]
    if query.filters.get("progress_min") is not None:
        rows = [r for r in rows if _to_decimal(r.get("current_amount", 0)) >= _to_decimal(query.filters["progress_min"])]
    return rows


@_register("tags")
async def _query_tags(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    rows = await tags_repo.list_tags(conn, user_id)
    if query.filters.get("name_search"):
        term = query.filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("name") or "").lower()]
    return rows


@_register("dashboard_summary")
async def _query_dashboard(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> dict | list[dict]:
    currency = query.filters.get("base_currency") or defaults.get("base_currency") or "RUB"
    result = await analytics_repo.get_dashboard_summary(conn, user_id, currency)
    if result is None:
        return {"error": "No dashboard data available"}
    return [result]


@_register("cash_flow")
async def _query_cash_flow(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await analytics_repo.get_cash_flow(
        conn, user_id,
        date_from=query.filters.get("date_from"),
        date_to=query.filters.get("date_to"),
        group_by=query.filters.get("group_by", "month"),
    )


@_register("net_worth")
async def _query_net_worth(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await analytics_repo.get_net_worth(
        conn, user_id,
        date_from=query.filters.get("date_from"),
        date_to=query.filters.get("date_to"),
    )


@_register("snapshots")
async def _query_snapshots(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await analytics_repo.list_snapshots(
        conn, user_id,
        date_from=query.filters.get("date_from"),
        date_to=query.filters.get("date_to"),
    )


# ---------------------------------------------------------------------------
# Reference / catalog domains (full catalogs, no user scoping)
# ---------------------------------------------------------------------------


@_register("account_types")
async def _query_account_types(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await ref_repo.list_account_types(conn)


@_register("asset_types")
async def _query_asset_types(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await ref_repo.list_asset_types(conn)


@_register("liability_types")
async def _query_liability_types(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await ref_repo.list_liability_types(conn)


@_register("provider_types")
async def _query_provider_types(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await ref_repo.list_provider_types(conn)


@_register("categories")
async def _query_categories(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    rows = await ref_repo.list_categories(
        conn,
        type_=query.filters.get("type"),
    )
    if query.filters.get("parent_name"):
        term = query.filters["parent_name"].lower()
        rows = [r for r in rows if term in (r.get("parent_name") or "").lower()]
    if query.filters.get("name_search"):
        term = query.filters["name_search"].lower()
        rows = [r for r in rows if term in (r.get("name") or "").lower()]
    return rows


@_register("merchants")
async def _query_merchants(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await ref_repo.list_merchants(
        conn,
        q=query.filters.get("q") or query.filters.get("name_search"),
        country=query.filters.get("country"),
        risk_level=query.filters.get("risk_level"),
    )


@_register("financial_institutions")
async def _query_institutions(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    return await fi_repo.list_institutions(
        conn,
        q=query.filters.get("q") or query.filters.get("name_search"),
        country=query.filters.get("country"),
        provider_type_code=query.filters.get("provider_type_code"),
        active_only=query.filters.get("active_only", True),
    )


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------


@_register("conversation_history")
async def _query_conversation_history(conn: AsyncConnection, user_id: str, query: UserDataQuery, defaults: dict) -> list[dict]:
    conversation_id = query.filters.get("conversation_id") or defaults.get("conversation_id")
    if not conversation_id:
        return [{"error": "conversation_history requires conversation_id"}]
    rows = await chat_repo.list_messages(conn, conversation_id)
    if query.filters.get("date_from"):
        rows = [r for r in rows if (r.get("created_at") or "") >= query.filters["date_from"]]
    if query.filters.get("date_to"):
        rows = [r for r in rows if (r.get("created_at") or "") <= query.filters["date_to"]]
    if query.filters.get("message_text_search"):
        term = query.filters["message_text_search"].lower()
        filtered: list[dict] = []
        for r in rows:
            text = _extract_message_text(r)
            if term in text.lower():
                filtered.append(r)
        rows = filtered
    last_n = query.filters.get("last_n")
    if last_n and isinstance(last_n, int):
        rows = rows[-last_n:]
    return rows


def _extract_message_text(msg: dict) -> str:
    content = msg.get("content", [])
    if isinstance(content, str):
        import json
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content
    parts: list[str] = []
    for part in content:
        if isinstance(part, dict) and part.get("text"):
            parts.append(part["text"])
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _single_field(row: dict, *names: str) -> Any:
    for n in names:
        if n in row:
            return row[n]
    return None
