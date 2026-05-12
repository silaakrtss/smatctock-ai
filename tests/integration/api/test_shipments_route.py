from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from src.application.services.shipping_service import ShipmentNotFoundError
from src.domain.shipping.shipment import Shipment, ShipmentStatus
from src.presentation.api.dependencies import get_scope
from src.presentation.main import app


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class StubShippingService:
    def __init__(self) -> None:
        self.delivered_id: int | None = None
        self.shipments = [
            Shipment(
                id=1,
                order_id=101,
                carrier="Aras",
                tracking_number="TRK-101",
                dispatched_at=_dt(2026, 5, 10, 9, 0),
                expected_delivery_at=datetime.now(tz=timezone.utc) - timedelta(hours=2),
            ),
            Shipment(
                id=2,
                order_id=102,
                carrier="Yurtiçi",
                tracking_number="TRK-102",
                dispatched_at=_dt(2026, 5, 11, 9, 0),
                expected_delivery_at=datetime.now(tz=timezone.utc) + timedelta(hours=5),
            ),
        ]

    async def list_active_shipments(self) -> list[Shipment]:
        return self.shipments

    async def find_delayed_shipments(self, now: datetime) -> list[Shipment]:
        return [shipment for shipment in self.shipments if shipment.is_delayed(now=now)]

    async def get_by_order(self, order_id: int) -> Shipment:
        for shipment in self.shipments:
            if shipment.order_id == order_id:
                return shipment
        raise ShipmentNotFoundError(str(order_id))

    async def mark_delivered(self, shipment_id: int, at: datetime) -> Shipment:
        self.delivered_id = shipment_id
        for shipment in self.shipments:
            if shipment.id == shipment_id:
                shipment.status = ShipmentStatus.DELIVERED
                shipment.delivered_at = at
                return shipment
        raise ShipmentNotFoundError(str(shipment_id))


@pytest.fixture
def client_with_shipments():
    shipping = StubShippingService()
    scope = SimpleNamespace(shipping=shipping)

    async def override():
        yield scope

    app.dependency_overrides[get_scope] = override
    try:
        yield TestClient(app), shipping
    finally:
        app.dependency_overrides.pop(get_scope, None)


def test_active_shipments_returns_delay_signal(client_with_shipments):
    client, _shipping = client_with_shipments

    response = client.get("/shipments/active")

    assert response.status_code == 200
    payload = response.json()
    assert {shipment["order_id"] for shipment in payload} == {101, 102}
    assert payload[0]["is_delayed"] is True


def test_delayed_shipments_returns_only_late_items(client_with_shipments):
    client, _shipping = client_with_shipments

    response = client.get("/shipments/delayed")

    assert response.status_code == 200
    assert [shipment["order_id"] for shipment in response.json()] == [101]


def test_mark_delivered_updates_shipment(client_with_shipments):
    client, shipping = client_with_shipments

    response = client.post("/shipments/1/delivered")

    assert response.status_code == 200
    assert response.json()["status"] == "delivered"
    assert shipping.delivered_id == 1
