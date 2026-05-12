from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from src.application.services.stock_service import StockInventoryItem
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from src.domain.products.product import Product
from src.domain.stock.stock_threshold import StockThreshold
from src.presentation.api.dependencies import get_scope
from src.presentation.main import app


class StubStockService:
    def __init__(self) -> None:
        self.adjusted: tuple[int, int] | None = None
        self.reordered: tuple[int, int] | None = None

    async def inventory_overview(self) -> list[StockInventoryItem]:
        return [
            StockInventoryItem(
                product=Product(id=1, name="Domates", stock=8),
                threshold=StockThreshold(product_id=1, min_quantity=20),
                status="low",
                suggested_reorder_quantity=32,
            ),
            StockInventoryItem(
                product=Product(id=2, name="Salatalık", stock=120),
                threshold=StockThreshold(product_id=2, min_quantity=40),
                status="ok",
                suggested_reorder_quantity=0,
            ),
        ]

    async def adjust_stock(self, product_id: int, delta: int) -> Product:
        self.adjusted = (product_id, delta)
        return Product(id=product_id, name="Domates", stock=40)

    async def create_reorder_draft(self, product_id: int, quantity: int) -> Notification:
        self.reordered = (product_id, quantity)
        return Notification(
            id=7,
            channel=NotificationChannel.TELEGRAM,
            recipient="@tedarik",
            subject="Tedarik taslağı: Domates",
            body="Domates için 32 adet sipariş hazırlanması öneriliyor.",
            created_at=datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc),
            status=NotificationStatus.SENT,
        )


@pytest.fixture
def client_with_inventory():
    stock = StubStockService()
    scope = SimpleNamespace(stock=stock)

    async def override():
        yield scope

    app.dependency_overrides[get_scope] = override
    try:
        yield TestClient(app), stock
    finally:
        app.dependency_overrides.pop(get_scope, None)


def test_inventory_overview_marks_low_stock_and_suggestions(client_with_inventory):
    client, _stock = client_with_inventory

    response = client.get("/inventory")

    assert response.status_code == 200
    assert response.json()[0] == {
        "id": 1,
        "name": "Domates",
        "stock": 8,
        "min_quantity": 20,
        "status": "low",
        "suggested_reorder_quantity": 32,
    }


def test_adjust_stock_updates_product(client_with_inventory):
    client, stock = client_with_inventory

    response = client.post("/inventory/1/adjust", json={"delta": 32})

    assert response.status_code == 200
    assert response.json()["stock"] == 40
    assert stock.adjusted == (1, 32)


def test_reorder_draft_uses_suggested_quantity_when_omitted(client_with_inventory):
    client, stock = client_with_inventory

    response = client.post("/inventory/1/reorder-draft", json={})

    assert response.status_code == 200
    assert response.json()["recipient"] == "@tedarik"
    assert stock.reordered == (1, 32)


def test_low_stock_endpoint_filters_only_low_and_out_items(client_with_inventory):
    client, _stock = client_with_inventory

    response = client.get("/inventory/low-stock")

    assert response.status_code == 200
    items = response.json()
    # Salatalık (status=ok) filtrelenmeli, sadece Domates (status=low) dönmeli
    assert len(items) == 1
    assert items[0]["name"] == "Domates"
    assert items[0]["status"] == "low"
