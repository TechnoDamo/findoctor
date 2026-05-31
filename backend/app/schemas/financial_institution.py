"""Схемы для финансовых организаций."""

from uuid import UUID

from pydantic import BaseModel, Field


class FinancialInstitutionCreate(BaseModel):
    """Запрос на создание финансовой организации."""
    name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(None, min_length=2, max_length=2)
    website_url: str | None = None
    logo_url: str | None = None
    integration_key: str | None = None
    provider_type_ids: list[str] = []


class FinancialInstitutionUpdate(BaseModel):
    """Запрос на обновление финансовой организации."""
    name: str | None = None
    country: str | None = None
    website_url: str | None = None
    logo_url: str | None = None
    integration_key: str | None = None
    risk_level: str | None = None
    is_active: bool | None = None
    provider_type_ids: list[str] | None = None


class FinancialInstitution(BaseModel):
    """Финансовая организация."""
    id: UUID
    name: str
    country: str | None = None
    website_url: str | None = None
    logo_url: str | None = None
    integration_key: str | None = None
    risk_level: str = "unknown"
    is_active: bool = True
    provider_type_ids: list[str] = []


class FinancialInstitutionList(BaseModel):
    """Список финансовых организаций."""
    items: list[FinancialInstitution]
