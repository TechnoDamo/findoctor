"""Тесты управления транзакциями и тегами транзакций."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _get_account_id(test_client: AsyncClient, auth_headers: dict) -> str:
    resp = await test_client.get("/api/v1/reference/account-types")
    types_list = resp.json()
    atype_id = types_list[0]["id"] if types_list else "00000000-0000-0000-0000-000000000001"
    r = await test_client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": atype_id,
            "name": "Тестовый счёт",
            "currency": "RUB",
        },
        headers=auth_headers,
    )
    return r.json()["id"]


async def test_create_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    resp = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "expense",
            "amount": "1500.50",
            "currency": "RUB",
            "transaction_datetime": "2025-01-15T10:30:00Z",
            "description": "Покупка продуктов",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["type"] == "expense"
    assert data["amount"] == "1500.50"
    assert data["description"] == "Покупка продуктов"


async def test_list_transactions(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "income",
            "amount": "50000.00",
            "currency": "RUB",
            "transaction_datetime": "2025-01-10T09:00:00Z",
            "description": "Зарплата",
        },
        headers=auth_headers,
    )
    resp = await test_client.get("/api/v1/transactions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "meta" in data
    assert len(data["items"]) >= 1


async def test_get_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "expense",
            "amount": "500.00",
            "currency": "RUB",
            "transaction_datetime": "2025-01-20T12:00:00Z",
            "description": "Обед",
        },
        headers=auth_headers,
    )
    txn_id = r.json()["id"]
    resp = await test_client.get(f"/api/v1/transactions/{txn_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Обед"


async def test_update_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "expense",
            "amount": "200.00",
            "currency": "RUB",
            "transaction_datetime": "2025-01-01T00:00:00Z",
            "description": "Старое описание",
        },
        headers=auth_headers,
    )
    txn_id = r.json()["id"]
    resp = await test_client.patch(
        f"/api/v1/transactions/{txn_id}",
        json={"description": "Новое описание", "amount": "350.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Новое описание"
    assert data["amount"] == "350.00"


async def test_delete_transaction(test_client: AsyncClient, auth_headers: dict) -> None:
    account_id = await _get_account_id(test_client, auth_headers)
    r = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "expense",
            "amount": "100.00",
            "currency": "RUB",
            "transaction_datetime": "2025-01-01T00:00:00Z",
            "description": "Для удаления",
        },
        headers=auth_headers,
    )
    txn_id = r.json()["id"]
    resp = await test_client.delete(f"/api/v1/transactions/{txn_id}", headers=auth_headers)
    assert resp.status_code == 204


async def test_list_transactions_unauthorized(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/v1/transactions")
    assert resp.status_code == 401


class TestTransactionTags:
    async def test_attach_and_list_tags(self, test_client: AsyncClient, auth_headers: dict) -> None:
        account_id = await _get_account_id(test_client, auth_headers)
        r = await test_client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "type": "expense",
                "amount": "500.00",
                "currency": "RUB",
                "transaction_datetime": "2025-02-01T12:00:00Z",
            },
            headers=auth_headers,
        )
        txn_id = r.json()["id"]

        tag_r = await test_client.post(
            "/api/v1/tags",
            json={"name": "продукты"},
            headers=auth_headers,
        )
        tag_id = tag_r.json()["id"]

        resp = await test_client.post(
            f"/api/v1/transactions/{txn_id}/tags/{tag_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        resp2 = await test_client.get(
            f"/api/v1/transactions/{txn_id}/tags",
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        tags = resp2.json()["items"]
        assert len(tags) >= 1
        assert any(t["id"] == tag_id for t in tags)

    async def test_replace_tags(self, test_client: AsyncClient, auth_headers: dict) -> None:
        account_id = await _get_account_id(test_client, auth_headers)
        r = await test_client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "type": "expense",
                "amount": "500.00",
                "currency": "RUB",
                "transaction_datetime": "2025-02-10T12:00:00Z",
            },
            headers=auth_headers,
        )
        txn_id = r.json()["id"]

        tag1 = await test_client.post("/api/v1/tags", json={"name": "тег1"}, headers=auth_headers)
        tag2 = await test_client.post("/api/v1/tags", json={"name": "тег2"}, headers=auth_headers)
        tid1 = tag1.json()["id"]
        tid2 = tag2.json()["id"]

        resp = await test_client.put(
            f"/api/v1/transactions/{txn_id}/tags",
            json={"tag_ids": [tid1, tid2]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2

    async def test_detach_tag(self, test_client: AsyncClient, auth_headers: dict) -> None:
        account_id = await _get_account_id(test_client, auth_headers)
        r = await test_client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "type": "expense",
                "amount": "500.00",
                "currency": "RUB",
                "transaction_datetime": "2025-02-20T12:00:00Z",
            },
            headers=auth_headers,
        )
        txn_id = r.json()["id"]

        tag_r = await test_client.post("/api/v1/tags", json={"name": "врем"}, headers=auth_headers)
        tag_id = tag_r.json()["id"]

        await test_client.post(f"/api/v1/transactions/{txn_id}/tags/{tag_id}", headers=auth_headers)

        resp = await test_client.delete(
            f"/api/v1/transactions/{txn_id}/tags/{tag_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
