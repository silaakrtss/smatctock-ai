from datetime import datetime, timedelta, timezone

import pytest
from src.domain.shipping.shipment import (
    AlreadyDeliveredError,
    Shipment,
    ShipmentStatus,
)


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class TestShipmentCreation:
    def test_creates_shipment_with_required_fields(self):
        shipment = Shipment(
            id=1,
            order_id=101,
            carrier="Aras",
            tracking_number="TRK-1",
            dispatched_at=_dt(2026, 5, 10, 9, 0),
            expected_delivery_at=_dt(2026, 5, 12, 18, 0),
        )

        assert shipment.status == ShipmentStatus.DISPATCHED
        assert shipment.delivered_at is None

    def test_tracking_number_cannot_be_empty(self):
        with pytest.raises(ValueError, match="tracking_number"):
            Shipment(
                id=1,
                order_id=101,
                carrier="Aras",
                tracking_number="",
                dispatched_at=_dt(2026, 5, 10, 9, 0),
                expected_delivery_at=_dt(2026, 5, 12, 18, 0),
            )


class TestIsDelayed:
    def test_delayed_when_expected_passed_and_not_delivered(self):
        expected = _dt(2026, 5, 10, 18, 0)
        shipment = _dispatched_with_expected(expected)

        assert shipment.is_delayed(now=expected + timedelta(hours=1)) is True

    def test_not_delayed_before_expected(self):
        expected = _dt(2026, 5, 12, 18, 0)
        shipment = _dispatched_with_expected(expected)

        assert shipment.is_delayed(now=expected - timedelta(hours=1)) is False

    def test_not_delayed_when_already_delivered(self):
        expected = _dt(2026, 5, 10, 18, 0)
        shipment = _dispatched_with_expected(expected)
        shipment.mark_delivered(_dt(2026, 5, 10, 17, 0))

        assert shipment.is_delayed(now=expected + timedelta(days=1)) is False


class TestMarkDelivered:
    def test_sets_status_and_timestamp(self):
        shipment = _dispatched_with_expected(_dt(2026, 5, 12, 18, 0))
        delivery_time = _dt(2026, 5, 12, 16, 30)

        shipment.mark_delivered(delivery_time)

        assert shipment.status == ShipmentStatus.DELIVERED
        assert shipment.delivered_at == delivery_time

    def test_rejects_double_delivery(self):
        shipment = _dispatched_with_expected(_dt(2026, 5, 12, 18, 0))
        shipment.mark_delivered(_dt(2026, 5, 12, 16, 30))

        with pytest.raises(AlreadyDeliveredError):
            shipment.mark_delivered(_dt(2026, 5, 12, 17, 0))


def _dispatched_with_expected(expected: datetime) -> Shipment:
    return Shipment(
        id=1,
        order_id=101,
        carrier="Aras",
        tracking_number="TRK-1",
        dispatched_at=expected - timedelta(days=2),
        expected_delivery_at=expected,
    )
