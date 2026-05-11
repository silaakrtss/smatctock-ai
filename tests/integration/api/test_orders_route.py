from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from src.domain.orders.order import Order
from src.domain.orders.order_status import OrderStatus
from src.presentation.api.dependencies import get_scope
from src.presentation.main import app


def _order(order_id: int, customer: str, status: OrderStatus) -> Order:
    return Order(
        id=order_id,
        customer_name=customer,
        created_at=datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc),
        status=status,
    )


class StubOrderService:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders
        self.last_status: str | None = None

    async def list(self, *, status: str | None = None, **_: object) -> list[Order]:
        self.last_status = status
        if status is None:
            return list(self._orders)
        return [o for o in self._orders if o.status.value == status]


@pytest.fixture
def stub_orders():
    return [
        _order(1, "Ali", OrderStatus.PREPARING),
        _order(2, "Ayşe", OrderStatus.IN_SHIPPING),
        _order(3, "Mehmet", OrderStatus.DELIVERED),
    ]


@pytest.fixture
def client_with_orders(stub_orders):
    service = StubOrderService(stub_orders)
    scope = SimpleNamespace(orders=service)

    async def override():
        yield scope

    app.dependency_overrides[get_scope] = override
    try:
        yield TestClient(app), service
    finally:
        app.dependency_overrides.pop(get_scope, None)


def test_list_orders_without_status_returns_all(client_with_orders):
    client, service = client_with_orders

    response = client.get("/orders")

    assert response.status_code == 200
    assert {o["id"] for o in response.json()} == {1, 2, 3}
    assert service.last_status is None


def test_list_orders_filters_by_delivered_status(client_with_orders):
    client, service = client_with_orders

    response = client.get("/orders", params={"status": "delivered"})

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [3]
    assert service.last_status == "delivered"


def test_list_orders_filters_by_preparing_status(client_with_orders):
    client, _ = client_with_orders

    response = client.get("/orders", params={"status": "preparing"})

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [1]
