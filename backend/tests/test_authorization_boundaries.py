"""Проверки изоляции пользовательских финансовых данных."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _register(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "boundaryTest123",
            "base_currency": "RUB",
            "timezone": "Europe/Moscow",
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _account_type_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/reference/account-types")
    assert response.status_code == 200, response.text
    return response.json()[0]["id"]


async def _asset_type_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/reference/asset-types")
    assert response.status_code == 200, response.text
    return response.json()[0]["id"]


async def _create_account(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.post(
        "/api/v1/accounts",
        json={
            "account_type_id": await _account_type_id(client),
            "name": "Граничный счёт",
            "currency": "RUB",
            "opening_balance": "10000.00",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_account_object_routes_are_user_scoped(test_client: AsyncClient) -> None:
    owner = await _register(test_client, "owner.account@example.com")
    stranger = await _register(test_client, "stranger.account@example.com")
    account_id = await _create_account(test_client, owner)

    assert (await test_client.get(f"/api/v1/accounts/{account_id}", headers=stranger)).status_code == 404
    assert (
        await test_client.patch(
            f"/api/v1/accounts/{account_id}",
            json={"name": "Чужое имя"},
            headers=stranger,
        )
    ).status_code == 404
    assert (await test_client.delete(f"/api/v1/accounts/{account_id}", headers=stranger)).status_code == 404
    assert (await test_client.get(f"/api/v1/accounts/{account_id}", headers=owner)).status_code == 200


async def test_transaction_and_tag_routes_are_user_scoped(test_client: AsyncClient) -> None:
    owner = await _register(test_client, "owner.txn@example.com")
    stranger = await _register(test_client, "stranger.txn@example.com")
    account_id = await _create_account(test_client, owner)

    txn_response = await test_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "type": "expense",
            "amount": "500.00",
            "currency": "RUB",
            "transaction_datetime": "2026-01-10T10:00:00Z",
            "description": "Проверка границ",
        },
        headers=owner,
    )
    assert txn_response.status_code == 201, txn_response.text
    txn_id = txn_response.json()["id"]

    tag_response = await test_client.post("/api/v1/tags", json={"name": "личное"}, headers=owner)
    assert tag_response.status_code == 201, tag_response.text
    tag_id = tag_response.json()["id"]

    assert (await test_client.get(f"/api/v1/transactions/{txn_id}", headers=stranger)).status_code == 404
    assert (
        await test_client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={"description": "чужая правка"},
            headers=stranger,
        )
    ).status_code == 404
    assert (
        await test_client.post(
            f"/api/v1/transactions/{txn_id}/tags/{tag_id}",
            headers=stranger,
        )
    ).status_code == 404
    assert (await test_client.get(f"/api/v1/tags/{tag_id}", headers=stranger)).status_code == 404
    assert (await test_client.get(f"/api/v1/transactions/{txn_id}", headers=owner)).status_code == 200


async def test_assets_goals_and_conversations_are_user_scoped(test_client: AsyncClient) -> None:
    owner = await _register(test_client, "owner.domain@example.com")
    stranger = await _register(test_client, "stranger.domain@example.com")

    asset = await test_client.post(
        "/api/v1/assets",
        json={
            "asset_type_id": await _asset_type_id(test_client),
            "name": "Квартира",
            "estimated_value": "12000000.00",
            "currency": "RUB",
        },
        headers=owner,
    )
    assert asset.status_code == 201, asset.text
    asset_id = asset.json()["id"]

    goal = await test_client.post(
        "/api/v1/goals",
        json={"name": "Резерв", "target_amount": "300000.00", "current_amount": "100000.00"},
        headers=owner,
    )
    assert goal.status_code == 201, goal.text
    goal_id = goal.json()["id"]

    conversation = await test_client.post(
        "/api/v1/ai/chat/conversations",
        json={"title": "Личный диалог"},
        headers=owner,
    )
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]

    assert (await test_client.get(f"/api/v1/assets/{asset_id}", headers=stranger)).status_code == 404
    assert (await test_client.get(f"/api/v1/goals/{goal_id}", headers=stranger)).status_code == 404
    assert (
        await test_client.get(
            f"/api/v1/ai/chat/conversations/{conversation_id}",
            headers=stranger,
        )
    ).status_code == 404
