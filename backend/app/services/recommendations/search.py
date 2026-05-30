"""SearXNG search adapter with allowed-source filtering."""

from typing import Any

import httpx

from app.clients.http import get_http_client
from app.services.recommendations.schemas import RecommendationEvidence
from app.services.recommendations.source_policy import constrain_search_query, is_allowed_url


async def search_searxng(
    *,
    base_url: str,
    query: str,
    allowed_hosts: set[str],
    timeout_seconds: float,
    limit: int = 5,
) -> list[RecommendationEvidence]:
    """Run SearXNG search and keep only allowed URLs."""

    if not base_url:
        return []

    client = get_http_client()
    constrained_query = constrain_search_query(query, allowed_hosts)
    response = await client.get(
        f"{base_url.rstrip('/')}/search",
        params={"q": constrained_query, "format": "json", "language": "all"},
        timeout=httpx.Timeout(timeout_seconds, connect=5.0),
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()

    results: list[RecommendationEvidence] = []
    for item in payload.get("results") or []:
        url = item.get("url") or ""
        if allowed_hosts and not is_allowed_url(url, allowed_hosts):
            continue
        text = item.get("content") or item.get("snippet") or ""
        if not text:
            continue
        results.append(
            RecommendationEvidence(
                source="searxng",
                query=query,
                title=item.get("title"),
                url=url,
                text=text,
                score=item.get("score"),
                metadata={
                    "engine": item.get("engine"),
                    "engines": item.get("engines"),
                    "category": item.get("category"),
                    "constrained_query": constrained_query,
                },
            )
        )
        if len(results) >= limit:
            break

    return results

