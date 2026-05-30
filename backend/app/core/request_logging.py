"""HTTP request/response logging middleware."""

from __future__ import annotations

import base64
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.settings import settings

logger = structlog.get_logger("http")


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request and response, including headers and full bodies."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        clear_contextvars()
        bind_contextvars(request_id=request_id)

        started_at = time.perf_counter()
        request_body = await request.body()
        request._receive = _make_receive(request_body)  # noqa: SLF001
        request_target = _request_target(request)

        logger.info(
            f"REQUEST: {request.method} {request_target}",
            event_type="http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
            target=request_target,
            client_host=request.client.host if request.client else None,
            headers=_headers(request.headers) if settings.log_http_headers else None,
            body=_body(request_body, request.headers.get("content-type"))
            if settings.log_http_bodies
            else None,
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            logger.exception(
                f"RESPONSE_ERROR: {request.method} {request_target} {duration_ms}ms",
                event_type="http_response_error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                query=str(request.url.query),
                target=request_target,
                duration_ms=duration_ms,
            )
            raise

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info(
            f"RESPONSE: {response.status_code} {request.method} {request_target} {duration_ms}ms",
            event_type="http_response",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
            target=request_target,
            status_code=response.status_code,
            duration_ms=duration_ms,
            headers=_headers(response.headers) if settings.log_response_headers else None,
            body=_body(response_body, response.headers.get("content-type"))
            if settings.log_response_bodies
            else None,
        )

        headers = dict(response.headers)
        headers["x-request-id"] = request_id
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )


def _make_receive(body: bytes) -> Callable[[], Awaitable[Message]]:
    async def receive() -> Message:
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


def _headers(headers: Any) -> dict[str, str]:
    return {key: value for key, value in headers.items()}


def _request_target(request: Request) -> str:
    query = str(request.url.query)
    if query:
        return f"{request.url.path}?{query}"
    return request.url.path


def _body(body: bytes, content_type: str | None) -> dict[str, Any]:
    if not body:
        return {"encoding": "utf-8", "content": ""}

    try:
        return {"encoding": "utf-8", "content": body.decode("utf-8")}
    except UnicodeDecodeError:
        return {
            "encoding": "base64",
            "content_type": content_type,
            "content": base64.b64encode(body).decode("ascii"),
        }
