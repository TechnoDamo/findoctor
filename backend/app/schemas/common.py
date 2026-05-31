"""Общие типы и схемы, используемые в нескольких модулях."""

import re
from typing import Annotated

from pydantic import BaseModel, Field

CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
MONEY_PATTERN = re.compile(r"^-?\d+(\.\d{1,8})?$")


def validate_currency(v: str) -> str:
    """Проверяет, что строка соответствует ISO 4217 (3 заглавные буквы)."""
    if not CURRENCY_PATTERN.match(v):
        raise ValueError(f"Код валюты должен быть из 3 заглавных букв, получено: {v}")
    return v


def validate_money(v: str) -> str:
    """Проверяет формат денежной суммы: целое или с 1-8 знаками после запятой."""
    if not MONEY_PATTERN.match(v):
        raise ValueError(f"Некорректный формат суммы: {v}")
    return v


MoneyAmount = Annotated[str, Field(pattern=r"^-?\d+(\.\d{1,8})?$", examples=["1250.00"])]
CurrencyCode = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$", examples=["USD", "EUR", "RUB"])]
RiskLevel = str  # low, medium, high, unknown


class PageMeta(BaseModel):
    """Метаинформация о пагинации."""
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Детали ошибки по контракту OpenAPI."""
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    """Ошибка API."""
    error: ErrorDetail
