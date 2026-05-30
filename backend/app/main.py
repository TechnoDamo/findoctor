"""
Точка входа FastAPI-приложения FinDoctor.

Настраивает жизненный цикл (lifespan), CORS-политику, логирование,
обработку ошибок и подключает единый роутер API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg import Error as PsycopgError
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.api.router import api_router
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.core.request_logging import HttpLoggingMiddleware
from app.db.pool import init_pool, close_pool
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения.

    На старте: настраивает логирование, инициализирует пул соединений БД.
    На остановке: закрывает пул соединений БД.
    """
    configure_logging()
    settings.validate_runtime_settings()
    await init_pool()
    yield
    await close_pool()


app = FastAPI(
    title="FinDoctor API",
    version="0.1.0",
    description="Client-facing API для управления личными финансами: счета, транзакции, активы, обязательства, цели, аналитика и AI-ассистент.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HttpLoggingMiddleware)


# ---------------------------------------------------------------------------
# Глобальные обработчики ошибок
# Преобразуют исключения приложения в JSON-ответы согласно OpenAPI-контракту.
# ---------------------------------------------------------------------------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Обработчик всех исключений приложения."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(PsycopgError)
async def database_error_handler(request: Request, exc: PsycopgError) -> JSONResponse:
    """Convert database exceptions into controlled JSON API responses."""
    if isinstance(exc, UniqueViolation):
        status_code = 409
        code = "conflict"
        message = "Database uniqueness constraint failed"
    elif isinstance(exc, ForeignKeyViolation):
        status_code = 409
        code = "conflict"
        message = "Referenced database row does not exist"
    else:
        status_code = 400
        code = "database_error"
        message = "Database request failed"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": {"pgcode": getattr(exc, "sqlstate", None)},
            }
        },
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_error_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
    """Catch response validation errors and return a controlled 500."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "server_error",
                "message": "Internal server error",
                "details": None,
            }
        },
    )


# ---------------------------------------------------------------------------
# Роутер
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.api_prefix)
