from datetime import datetime, timedelta, timezone

import pytest
from src.application.ports.shipment_repository import ShipmentRepository
from src.application.services.shipping_service import (
    ShipmentNotFoundError,
    ShippingService,
)
from src.domain.shipping.shipment import Shipment, ShipmentStatus


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _shipment(*, id: int, expected: datetime, status: ShipmentStatus | None = None) -> Shipment:
    return Shipment(
        id=id,
        order_id=100 + id,
        carrier="Aras",
        tracking_number=f"TRK-{id}",
        dispatched_at=expected - timedelta(days=2),
        expected_delivery_at=expected,
        status=status or ShipmentStatus.DISPATCHED,
    )


class FakeShipmentRepository(ShipmentRepository):
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items: dict[int, Shipment] = {s.id: s for s in shipments}

    async def get_by_id(self, shipment_id: int) -> Shipment | None:
        return self._items.get(shipment_id)

    async def list_active(self) -> list[Shipment]:
        return [s for s in self._items.values() if s.status == ShipmentStatus.DISPATCHED]

    async def save(self, shipment: Shipment) -> None:
        self._items[shipment.id] = shipment

    async def get_by_order(self, order_id: int) -> Shipment | None:
        for shipment in self._items.values():
            if shipment.order_id == order_id:
                return shipment
        return None


class TestFindDelayedShipments:
    async def test_returns_only_dispatched_past_expected(self):
        now = _dt(2026, 5, 12, 10, 0)
        shipments = [
            _shipment(id=1, expected=now - timedelta(hours=2)),
            _shipment(id=2, expected=now + timedelta(hours=2)),
            _shipment(
                id=3,
                expected=now - timedelta(days=1),
                status=ShipmentStatus.DELIVERED,
            ),
        ]
        service = ShippingService(shipments=FakeShipmentRepository(shipments))

        delayed = await service.find_delayed_shipments(now=now)

        assert [s.id for s in delayed] == [1]


class TestMarkDelivered:
    async def test_persists_delivered_state(self):
        shipment = _shipment(id=1, expected=_dt(2026, 5, 12, 18, 0))
        repo = FakeShipmentRepository([shipment])
        service = ShippingService(shipments=repo)

        result = await service.mark_delivered(1, at=_dt(2026, 5, 12, 17, 0))

        assert result.status == ShipmentStatus.DELIVERED
        stored = await repo.get_by_id(1)
        assert stored is not None
        assert stored.delivered_at == _dt(2026, 5, 12, 17, 0)

    async def test_unknown_shipment_raises(self):
        service = ShippingService(shipments=FakeShipmentRepository([]))

        with pytest.raises(ShipmentNotFoundError):
            await service.mark_delivered(99, at=_dt(2026, 5, 12, 17, 0))


class TestGetByOrder:
    async def test_returns_shipment_for_order(self):
        shipment = _shipment(id=1, expected=_dt(2026, 5, 12, 18, 0))
        service = ShippingService(shipments=FakeShipmentRepository([shipment]))

        result = await service.get_by_order(101)

        assert result.id == 1

    async def test_raises_when_no_shipment_for_order(self):
        service = ShippingService(shipments=FakeShipmentRepository([]))

        with pytest.raises(ShipmentNotFoundError):
            await service.get_by_order(404)
