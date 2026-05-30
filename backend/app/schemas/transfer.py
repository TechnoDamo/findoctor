"""Схемы для переводов между счетами."""

from pydantic import BaseModel

from app.schemas.common import CurrencyCode, MoneyAmount, PageMeta
from app.schemas.transaction import Transaction


class TransferCreate(BaseModel):
    """Запрос на создание перевода."""
    from_account_id: str
    to_account_id: str
    amount: MoneyAmount
    currency: CurrencyCode
    transaction_datetime: str
    description: str | None = None
    category_id: str | None = None
    external_id: str | None = None


class TransferUpdate(BaseModel):
    """Запрос на обновление перевода."""
    from_account_id: str | None = None
    to_account_id: str | None = None
    amount: MoneyAmount | None = None
    currency: CurrencyCode | None = None
    transaction_datetime: str | None = None
    description: str | None = None
    category_id: str | None = None


class Transfer(BaseModel):
    """Перевод с полной информацией."""
    id: str
    user_id: str
    from_account_id: str
    to_account_id: str
    amount: str
    currency: str
    transaction_datetime: str
    description: str | None = None
    from_transaction_id: str
    to_transaction_id: str
    from_transaction: Transaction | None = None
    to_transaction: Transaction | None = None


class TransferPage(BaseModel):
    """Страница переводов."""
    items: list[Transfer]
    meta: PageMeta
