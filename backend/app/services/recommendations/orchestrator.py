"""Agentic recommendation planning and evidence orchestration."""

import json
from typing import Any

from app.services import ai_chat
from app.services.recommendations.ragflow import retrieve_from_ragflow
from app.services.recommendations.schemas import (
    RECOMMENDATION_PLAN_JSON_SCHEMA,
    RecommendationEvidence,
    RecommendationPlan,
)
from app.services.recommendations.search import search_searxng
from app.services.recommendations.source_policy import load_allowed_hosts
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
    user_text: str,
    financial_context: str,
    prompt_name: str = "llm_text",
) -> tuple[str, dict, list[dict]]:
    """Plan needed tools, execute retrieval/search, and produce the final answer."""

    plan, planner_usage = await _run_planner(user_text=user_text, financial_context=financial_context)
    if plan.needed_tools is None:
        return plan.response_text, planner_usage, [
            {"type": "recommendation_plan", "plan": plan.model_dump(mode="json")}
        ]

    evidence = await _execute_tools(plan)
    final_text, final_usage = await _run_finalizer(
        user_text=user_text,
        financial_context=financial_context,
        planner_response=plan.response_text,
        evidence=evidence,
        prompt_name=prompt_name,
    )

    usage = {
        "prompt_tokens": (planner_usage.get("prompt_tokens") or 0)
        + (final_usage.get("prompt_tokens") or 0),
        "completion_tokens": (planner_usage.get("completion_tokens") or 0)
        + (final_usage.get("completion_tokens") or 0),
    }
    return final_text, usage, [
        {"type": "recommendation_plan", "plan": plan.model_dump(mode="json")},
        {
            "type": "recommendation_evidence",
            "items": [
                item.compact(max_chars=1200)
                for item in evidence[: settings.recommendation_max_evidence_items]
            ],
        },
    ]


async def _run_planner(
    *, user_text: str, financial_context: str
) -> tuple[RecommendationPlan, dict]:
    _base_url, _api_key, model = ai_chat._provider_config("llm")
    system_prompt = "\n\n".join([_planner_system_prompt(), "---", financial_context])
    payload = {
        "model": settings.recommendation_planner_model or model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_text,
            },
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


async def _execute_tools(plan: RecommendationPlan) -> list[RecommendationEvidence]:
    tools = plan.needed_tools
    if tools is None:
        return []

    evidence: list[RecommendationEvidence] = []

    if tools.rag:
        for query in tools.rag.rag_requests[: settings.recommendation_max_rag_requests]:
            evidence.extend(
                await retrieve_from_ragflow(
                    base_url=settings.ragflow_base_url,
                    api_key=settings.ragflow_api_key,
                    dataset_id=settings.ragflow_dataset_id,
                    query=query,
                    page_size=settings.ragflow_page_size,
                )
            )

    if tools.search:
        allowed_hosts = load_allowed_hosts(settings.recommendation_allowed_resources_file)
        for query in tools.search.search_queries[: settings.recommendation_max_search_queries]:
            evidence.extend(
                await search_searxng(
                    base_url=settings.searxng_base_url,
                    query=query,
                    allowed_hosts=allowed_hosts,
                    timeout_seconds=settings.searxng_timeout_seconds,
                    limit=settings.recommendation_max_evidence_items,
                )
            )

    return evidence[: settings.recommendation_max_evidence_items]


async def _run_finalizer(
    *,
    user_text: str,
    financial_context: str,
    planner_response: str,
    evidence: list[RecommendationEvidence],
    prompt_name: str,
) -> tuple[str, dict]:
    _base_url, _api_key, model = ai_chat._provider_config("llm")
    evidence_payload = _bounded_evidence(evidence)
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
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    response = await ai_chat._chat_completion("llm", payload)
    return ai_chat._message_text(response), response.get("usage") or {}


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
