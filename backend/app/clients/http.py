"""
Общий HTTP-клиент с таймаутами и повторными попытками.

Использует httpx.AsyncClient для вызовов внешних API.
Все внешние интеграции (LLM, банки, курсы валют) используют этот клиент.
"""

import httpx

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Возвращает глобальный HTTP-клиент."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
        )
    return _client


async def close_http_client() -> None:
    """Закрывает глобальный HTTP-клиент."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
