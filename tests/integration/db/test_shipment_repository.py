from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.orders.order import Order
from src.domain.shipping.shipment import Shipment, ShipmentStatus
from src.infrastructure.db.repositories.order_repository import (
    SqlAlchemyOrderRepository,
)
from src.infrastructure.db.repositories.shipment_repository import (
    SqlAlchemyShipmentRepository,
)

pytestmark = pytest.mark.integration


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


async def _create_order(session: AsyncSession, order_id: int) -> None:
    orders = SqlAlchemyOrderRepository(session)
    await orders.save(Order(id=order_id, customer_name="Ali", created_at=_dt(2026, 5, 10, 9, 0)))


def _make_shipment(
    *, shipment_id: int, order_id: int, status: ShipmentStatus | None = None
) -> Shipment:
    expected = _dt(2026, 5, 12, 18, 0)
    return Shipment(
        id=shipment_id,
        order_id=order_id,
        carrier="Aras",
        tracking_number=f"TRK-{shipment_id}",
        dispatched_at=expected - timedelta(days=2),
        expected_delivery_at=expected,
        status=status or ShipmentStatus.DISPATCHED,
    )


async def test_save_and_get_by_id_roundtrip(session: AsyncSession):
    await _create_order(session, 101)
    repo = SqlAlchemyShipmentRepository(session)
    await repo.save(_make_shipment(shipment_id=1, order_id=101))
    await session.commit()

    fetched = await repo.get_by_id(1)

    assert fetched is not None
    assert fetched.status == ShipmentStatus.DISPATCHED
    assert fetched.delivered_at is None


async def test_list_active_excludes_delivered(session: AsyncSession):
    await _create_order(session, 101)
    await _create_order(session, 102)
    repo = SqlAlchemyShipmentRepository(session)
    await repo.save(_make_shipment(shipment_id=1, order_id=101))
    delivered = _make_shipment(shipment_id=2, order_id=102, status=ShipmentStatus.DELIVERED)
    delivered.delivered_at = _dt(2026, 5, 12, 17, 0)
    await repo.save(delivered)
    await session.commit()

    active = await repo.list_active()

    assert [s.id for s in active] == [1]
