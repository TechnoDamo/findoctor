"""Тесты аналитики: дашборд, снимки, денежный поток, капитал."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_get_dashboard_summary(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.get("/api/v1/analytics/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "currency" in data
    assert "net_worth" in data
    assert "monthly_income" in data
    assert "monthly_expenses" in data


async def test_list_snapshots(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.get("/api/v1/analytics/snapshots", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


async def test_recalculate_snapshots(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.post(
        "/api/v1/analytics/snapshots/recalculate",
        json={"from_": "2025-01-01", "to": "2025-06-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "queued"
    assert "job_id" in data


async def test_get_cash_flow(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.get("/api/v1/analytics/cash-flow", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "currency" in data
    assert "items" in data


async def test_get_net_worth(test_client: AsyncClient, auth_headers: dict) -> None:
    resp = await test_client.get("/api/v1/analytics/net-worth", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "currency" in data
    assert "items" in data


async def test_dashboard_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 401
