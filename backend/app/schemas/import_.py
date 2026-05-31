"""Схемы для импорта транзакций."""

from uuid import UUID

from pydantic import BaseModel, Field


class TransactionImportItem(BaseModel):
    """Элемент импорта транзакции."""
    account_id: str
    category_id: str | None = None
    type: str
    amount: str
    currency: str
    transaction_datetime: str
    description: str | None = None
    merchant_id: str | None = None
    merchant_name: str | None = None
    geo_location: str | None = None
    recurring_transaction_id: str | None = None
    external_id: str
    tag_ids: list[str] | None = None


class TransactionImportRequest(BaseModel):
    """Запрос на импорт транзакций."""
    source: str | None = None
    items: list[TransactionImportItem] = Field(min_length=1, max_length=1000)


class TransactionImportResultItem(BaseModel):
    """Результат импорта одной транзакции."""
    status: str
    transaction_id: UUID | None = None
    external_id: str | None = None
    error: str | None = None


class TransactionImportResult(BaseModel):
    """Результат импорта."""
    created_count: int
    skipped_duplicate_count: int
    failed_count: int
    items: list[TransactionImportResultItem]
