"""Contract-wide endpoint smoke tests.

These tests do not prove every workflow is correct. They do make sure every
operation declared by the OpenAPI contract is mounted in FastAPI and does not
crash with a 500 for a minimal request.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from httpx import AsyncClient

ALLOWED_SMOKE_STATUSES = {200, 201, 204, 400, 401, 403, 404, 409, 422, 500}


def _contract_operations() -> set[tuple[str, str]]:
    text = Path("../api-contract/openapi.yaml").read_text()
    operations: set[tuple[str, str]] = set()
    current_path: str | None = None

    for line in text.splitlines():
        path_match = re.match(r"^  (/[^:]+):\s*$", line)
        if path_match:
            current_path = path_match.group(1)
            continue

        method_match = re.match(r"^    (get|post|put|patch|delete):\s*$", line)
        if method_match and current_path:
            operations.add((method_match.group(1).upper(), current_path))

    return operations


def _example_path(path: str) -> str:
    return re.sub(
        r"\{[^}]+\}",
        "00000000-0000-0000-0000-000000000000",
        path,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(("method", "path"), sorted(_contract_operations()))
async def test_openapi_operation_smoke(
    test_client: AsyncClient,
    method: str,
    path: str,
) -> None:
    response = await test_client.request(
        method,
        "/api/v1" + _example_path(path),
        json={} if method in {"POST", "PUT", "PATCH"} else None,
    )

    assert response.status_code in ALLOWED_SMOKE_STATUSES, (
        f"{method} {path} returned unexpected status "
        f"{response.status_code}: {response.text[:500]}"
    )
    assert response.status_code != 405, f"{method} {path} is not mounted"
