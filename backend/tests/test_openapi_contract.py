"""Tests that keep the FastAPI route surface aligned with the OpenAPI contract."""

from __future__ import annotations

import re
from pathlib import Path

from app.main import app

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def test_fastapi_routes_match_openapi_contract() -> None:
    contract_operations = _contract_operations()
    implemented_operations = _implemented_operations()

    assert implemented_operations == contract_operations


def test_openapi_contract_is_large_enough_to_guard_api_surface() -> None:
    contract_operations = _contract_operations()

    assert len({path for _, path in contract_operations}) == 46
    assert len(contract_operations) == 86


def _contract_operations() -> set[tuple[str, str]]:
    text = Path("../api-contract/openapi.yaml").read_text()
    operations: set[tuple[str, str]] = set()
    current_path: str | None = None

    for line in text.splitlines():
        path_match = re.match(r"^  (/[^:]+):\s*$", line)
        if path_match:
            current_path = _normalize_path(path_match.group(1))
            continue

        method_match = re.match(r"^    (get|post|put|patch|delete):\s*$", line)
        if method_match and current_path:
            operations.add((method_match.group(1).upper(), current_path))

    return operations


def _implemented_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for path, item in app.openapi()["paths"].items():
        normalized_path = _normalize_path(path.removeprefix("/api/v1") or "/")
        for method in item:
            if method.lower() in HTTP_METHODS:
                operations.add((method.upper(), normalized_path))
    return operations


def _normalize_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{id}", path)
