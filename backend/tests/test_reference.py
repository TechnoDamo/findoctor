"""Тесты справочных данных: типы, категории, продавцы."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


class TestReferenceTypes:
    async def test_list_account_types(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/reference/account-types")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_list_asset_types(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/reference/asset-types")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_list_liability_types(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/reference/liability-types")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_list_provider_types(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/reference/provider-types")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestCategories:
    async def test_create_category(self, test_client: AsyncClient) -> None:
        resp = await test_client.post(
            "/api/v1/reference/categories",
            json={"type": "expense", "name": "Продукты"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "Продукты"
        assert data["type"] == "expense"
        assert "id" in data

    async def test_list_categories(self, test_client: AsyncClient) -> None:
        await test_client.post(
            "/api/v1/reference/categories",
            json={"type": "expense", "name": "Транспорт"},
        )
        resp = await test_client.get("/api/v1/reference/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_categories_filter_by_type(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/reference/categories?type=expense")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_get_category(self, test_client: AsyncClient) -> None:
        r = await test_client.post(
            "/api/v1/reference/categories",
            json={"type": "income", "name": "Зарплата"},
        )
        cat_id = r.json()["id"]
        resp = await test_client.get(f"/api/v1/reference/categories/{cat_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Зарплата"

    async def test_update_category(self, test_client: AsyncClient) -> None:
        r = await test_client.post(
            "/api/v1/reference/categories",
            json={"type": "expense", "name": "Старое имя"},
        )
        cat_id = r.json()["id"]
        resp = await test_client.patch(
            f"/api/v1/reference/categories/{cat_id}",
            json={"name": "Новое имя"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Новое имя"

    async def test_delete_category(self, test_client: AsyncClient) -> None:
        r = await test_client.post(
            "/api/v1/reference/categories",
            json={"type": "expense", "name": "Для удаления"},
        )
        cat_id = r.json()["id"]
        resp = await test_client.delete(f"/api/v1/reference/categories/{cat_id}")
        assert resp.status_code == 204

    async def test_get_category_not_found(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/reference/categories/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestMerchants:
    async def test_create_merchant(self, test_client: AsyncClient) -> None:
        resp = await test_client.post(
            "/api/v1/merchants",
            json={"name": "Пятёрочка"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "Пятёрочка"
        assert "id" in data

    async def test_list_merchants(self, test_client: AsyncClient) -> None:
        await test_client.post(
            "/api/v1/merchants",
            json={"name": "Магнит"},
        )
        resp = await test_client.get("/api/v1/merchants")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_search_merchants_by_query(self, test_client: AsyncClient) -> None:
        await test_client.post(
            "/api/v1/merchants",
            json={"name": "Лента"},
        )
        resp = await test_client.get("/api/v1/merchants?q=Лент")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1

    async def test_get_merchant(self, test_client: AsyncClient) -> None:
        r = await test_client.post(
            "/api/v1/merchants",
            json={"name": "Дикси"},
        )
        merchant_id = r.json()["id"]
        resp = await test_client.get(f"/api/v1/merchants/{merchant_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Дикси"

    async def test_update_merchant(self, test_client: AsyncClient) -> None:
        r = await test_client.post(
            "/api/v1/merchants",
            json={"name": "Старый Магнит"},
        )
        merchant_id = r.json()["id"]
        resp = await test_client.patch(
            f"/api/v1/merchants/{merchant_id}",
            json={"name": "Новый Магнит", "country": "RU", "risk_level": "low"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Новый Магнит"
        assert data["country"] == "RU"
        assert data["risk_level"] == "low"

    async def test_delete_merchant(self, test_client: AsyncClient) -> None:
        r = await test_client.post(
            "/api/v1/merchants",
            json={"name": "Удаляемый"},
        )
        merchant_id = r.json()["id"]
        resp = await test_client.delete(f"/api/v1/merchants/{merchant_id}")
        assert resp.status_code == 204

    async def test_get_merchant_not_found(self, test_client: AsyncClient) -> None:
        resp = await test_client.get("/api/v1/merchants/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
