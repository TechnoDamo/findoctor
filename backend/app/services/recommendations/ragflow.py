"""RAGFlow HTTP adapter."""

from typing import Any

import httpx

from app.clients.http import get_http_client
from app.services.recommendations.schemas import RecommendationEvidence


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("content", "text", "chunk", "snippet", "document_content"):
            text = _first_text(value.get(key))
            if text:
                return text
    return ""


def _extract_chunks(payload: Any) -> list[dict]:
    """Find chunk-like dictionaries in RAGFlow responses across version shapes."""

    chunks: list[dict] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if any(key in value for key in ("content", "text", "chunk", "snippet")):
                chunks.append(value)
                return
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return chunks


async def retrieve_from_ragflow(
    *,
    base_url: str,
    api_key: str,
    dataset_id: str,
    query: str,
    page_size: int,
) -> list[RecommendationEvidence]:
    """Retrieve relevant chunks from RAGFlow."""

    if not base_url or not api_key or not dataset_id:
        return []

    client = get_http_client()
    response = await client.post(
        f"{base_url.rstrip('/')}/api/v1/retrieval",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "question": query,
            "dataset_ids": [dataset_id],
            "page": 1,
            "page_size": page_size,
        },
        timeout=httpx.Timeout(60.0, connect=10.0),
    )
    response.raise_for_status()
    payload = response.json()

    evidence: list[RecommendationEvidence] = []
    for chunk in _extract_chunks(payload):
        text = _first_text(chunk)
        if not text:
            continue
        evidence.append(
            RecommendationEvidence(
                source="ragflow",
                query=query,
                title=chunk.get("document_name") or chunk.get("title"),
                url=chunk.get("url") or chunk.get("source_url"),
                text=text,
                score=chunk.get("similarity") or chunk.get("score"),
                metadata={
                    key: value
                    for key, value in chunk.items()
                    if key not in {"content", "text", "chunk", "snippet"}
                },
            )
        )
    return evidence

