"""Agentic recommendation planning and evidence orchestration."""

import json
from typing import Any

from psycopg import AsyncConnection

from app.services import ai_chat
from app.services.recommendations.ragflow import retrieve_from_ragflow
from app.services.recommendations.schemas import (
    RECOMMENDATION_PLAN_JSON_SCHEMA,
    RecommendationEvidence,
    RecommendationPlan,
)
from app.services.recommendations.search import search_searxng
from app.services.recommendations.source_policy import load_allowed_hosts
from app.services.recommendations.user_data_tool import execute_user_data_queries
from app.settings import settings


def _planner_system_prompt() -> str:
    return "\n\n".join(
        [
            ai_chat._read_prompt("recommendation_planner.txt"),
            ai_chat._read_prompt("recommendation_context_policy.txt"),
            ai_chat._read_prompt("recommendation_safety_policy.txt"),
        ]
    )


def _finalizer_system_prompt(prompt_name: str, financial_context: str) -> str:
    return "\n\n".join(
        [
            ai_chat._read_prompt(f"{prompt_name}.txt"),
            ai_chat._read_prompt("recommendation_context_policy.txt"),
            ai_chat._read_prompt("recommendation_safety_policy.txt"),
            ai_chat._read_prompt("recommendation_finalizer.txt"),
            "---",
            financial_context,
        ]
    )


async def run_recommendation_flow(
    *,
    conn: AsyncConnection,
    user_id: str,
    user_text: str,
    financial_context: str,
    prompt_name: str = "llm_text",
    conversation_id: str | None = None,
    context_defaults: dict | None = None,
    max_passes: int | None = None,
) -> tuple[str, dict, list[dict]]:
    """Plan needed tools, execute retrieval/search/user-data, and produce the final answer.

    Runs up to *max_passes* rounds of planner → executor before the finalizer,
    so the LLM can chain follow-up queries based on intermediate results.
    """
    if max_passes is None:
        max_passes = settings.ai_chat_max_tool_passes

    accumulated_evidence: list[RecommendationEvidence] = []
    accumulated_tool_results: list[dict] = []
    total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}

    plan: RecommendationPlan | None = None
    planner_response_text = ""

    for _pass_num in range(max_passes):
        plan, planner_usage = await _run_planner(
            user_text=user_text,
            financial_context=financial_context,
            previous_tool_results=accumulated_tool_results,
        )
        total_usage["prompt_tokens"] += planner_usage.get("prompt_tokens") or 0
        total_usage["completion_tokens"] += planner_usage.get("completion_tokens") or 0
        planner_response_text = plan.response_text

        if plan.needed_tools is None:
            break

        evidence, data_results = await _execute_tools(
            plan, conn=conn, user_id=user_id,
            conversation_id=conversation_id,
            context_defaults=context_defaults,
        )
        accumulated_evidence.extend(evidence)
        accumulated_tool_results.extend(data_results)

        if not _should_continue(plan, data_results):
            break

    if accumulated_evidence or accumulated_tool_results:
        final_text, final_usage = await _run_finalizer(
            user_text=user_text,
            financial_context=financial_context,
            planner_response=planner_response_text,
            evidence=accumulated_evidence,
            tool_results=accumulated_tool_results,
            prompt_name=prompt_name,
        )
        total_usage["prompt_tokens"] += final_usage.get("prompt_tokens") or 0
        total_usage["completion_tokens"] += final_usage.get("completion_tokens") or 0

        enriched_tool_results = accumulated_tool_results + [
            {"type": "recommendation_plan", "plan": plan.model_dump(mode="json") if plan else {}},
        ]
        return final_text, total_usage, enriched_tool_results

    enriched_tool_results = accumulated_tool_results + [
        {"type": "recommendation_plan", "plan": plan.model_dump(mode="json") if plan else {}},
    ]
    return planner_response_text, total_usage, enriched_tool_results


def _should_continue(plan: RecommendationPlan, tool_results: list[dict]) -> bool:
    if plan.needed_tools is None:
        return False
    if not tool_results:
        return False
    return not any(r.get("error") for r in tool_results if isinstance(r, dict))


async def _run_planner(
    *,
    user_text: str,
    financial_context: str,
    previous_tool_results: list[dict] | None = None,
) -> tuple[RecommendationPlan, dict]:
    _base_url, _api_key, model = ai_chat._provider_config("llm")
    system_prompt = "\n\n".join([_planner_system_prompt(), "---", financial_context])

    user_content = user_text
    if previous_tool_results:
        user_content = json.dumps(
            {"user_text": user_text, "previous_results": previous_tool_results},
            ensure_ascii=False,
        )

    payload = {
        "model": settings.recommendation_planner_model or model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "recommendation_tool_plan",
                "strict": True,
                "schema": RECOMMENDATION_PLAN_JSON_SCHEMA,
            },
        },
    }
    response = await ai_chat._chat_completion("llm", payload)
    raw_text = ai_chat._message_text(response)
    plan = RecommendationPlan.model_validate_json(raw_text).normalized()
    return plan, response.get("usage") or {}


async def _execute_tools(
    plan: RecommendationPlan,
    *,
    conn: AsyncConnection,
    user_id: str,
    conversation_id: str | None = None,
    context_defaults: dict | None = None,
) -> tuple[list[RecommendationEvidence], list[dict]]:
    tools = plan.needed_tools
    if tools is None:
        return [], []

    evidence: list[RecommendationEvidence] = []
    data_results: list[dict] = []

    async def _gather_rag():
        if not tools.rag:
            return []
        items = []
        for query in tools.rag.rag_requests[: settings.recommendation_max_rag_requests]:
            try:
                items.extend(
                    await retrieve_from_ragflow(
                        base_url=settings.ragflow_base_url,
                        api_key=settings.ragflow_api_key,
                        dataset_id=settings.ragflow_dataset_id,
                        query=query,
                        page_size=settings.ragflow_page_size,
                    )
                )
            except Exception as exc:
                data_results.append({"type": "rag_error", "query": query, "error": str(exc)})
        return items

    async def _gather_search():
        if not tools.search:
            return []
        items = []
        allowed_hosts = load_allowed_hosts(settings.recommendation_allowed_resources_file)
        for query in tools.search.search_queries[: settings.recommendation_max_search_queries]:
            try:
                items.extend(
                    await search_searxng(
                        base_url=settings.searxng_base_url,
                        query=query,
                        allowed_hosts=allowed_hosts,
                        timeout_seconds=settings.searxng_timeout_seconds,
                        limit=settings.recommendation_max_evidence_items,
                    )
                )
            except Exception as exc:
                data_results.append({"type": "search_error", "query": query, "error": str(exc)})
        return items

    async def _gather_user_data():
        if not tools.user_data:
            return []
        defaults = context_defaults or {}
        if conversation_id:
            defaults["conversation_id"] = conversation_id
        try:
            results = await execute_user_data_queries(conn, user_id, tools.user_data, defaults)
            for r in results:
                data_results.append({
                    "type": "user_data",
                    "name": "user_data",
                    "result": r.model_dump(mode="json"),
                })
        except Exception as exc:
            data_results.append({"type": "user_data_error", "error": str(exc)})
        return []

    rag_evidence, search_evidence, _ = await _run_in_parallel(
        _gather_rag(), _gather_search(), _gather_user_data()
    )
    evidence.extend(rag_evidence)
    evidence.extend(search_evidence)
    return evidence[: settings.recommendation_max_evidence_items], data_results


async def _run_in_parallel(*coros):
    import asyncio
    return await asyncio.gather(*coros, return_exceptions=True)


async def _run_finalizer(
    *,
    user_text: str,
    financial_context: str,
    planner_response: str,
    evidence: list[RecommendationEvidence],
    tool_results: list[dict] | None = None,
    prompt_name: str,
) -> tuple[str, dict]:
    _base_url, _api_key, model = ai_chat._provider_config("llm")
    evidence_payload = _bounded_evidence(evidence)
    user_data_payload = _compact_tool_results(tool_results or [])

    payload = {
        "model": settings.recommendation_finalizer_model or model,
        "messages": [
            {
                "role": "system",
                "content": _finalizer_system_prompt(prompt_name, financial_context),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "user_text": user_text,
                        "planner_response": planner_response,
                        "evidence": evidence_payload,
                        "user_data": user_data_payload,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    response = await ai_chat._chat_completion("llm", payload)
    return ai_chat._message_text(response), response.get("usage") or {}


def _compact_tool_results(results: list[dict], max_chars: int = 6000) -> str:
    text = json.dumps(results, ensure_ascii=False, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("}", 1)[0] + "}"


def _bounded_evidence(evidence: list[RecommendationEvidence]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    total_chars = 0
    for item in evidence[: settings.recommendation_max_evidence_items]:
        compact = item.compact()
        text = compact["text"] or ""
        if total_chars + len(text) > settings.recommendation_max_evidence_chars:
            remaining = settings.recommendation_max_evidence_chars - total_chars
            if remaining <= 0:
                break
            compact["text"] = text[:remaining].rsplit(" ", 1)[0].rstrip()
        total_chars += len(compact["text"] or "")
        items.append(compact)
    return items
