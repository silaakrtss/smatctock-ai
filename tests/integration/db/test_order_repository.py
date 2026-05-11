from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.orders.order import Order
from src.domain.orders.order_status import OrderStatus
from src.infrastructure.db.repositories.order_repository import (
    SqlAlchemyOrderRepository,
)

pytestmark = pytest.mark.integration


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


async def test_save_persists_status_as_string(session: AsyncSession):
    repo = SqlAlchemyOrderRepository(session)
    await repo.save(Order(id=101, customer_name="Ali", created_at=_dt(2026, 5, 11, 9, 0)))
    await session.commit()

    fetched = await repo.get_by_id(101)

    assert fetched is not None
    assert fetched.status == OrderStatus.PREPARING


async def test_status_transition_persists(session: AsyncSession):
    repo = SqlAlchemyOrderRepository(session)
    order = Order(id=101, customer_name="Ali", created_at=_dt(2026, 5, 11, 9, 0))
    await repo.save(order)
    await session.commit()

    order.transition_to(OrderStatus.IN_SHIPPING)
    await repo.save(order)
    await session.commit()

    fetched = await repo.get_by_id(101)
    assert fetched is not None
    assert fetched.status == OrderStatus.IN_SHIPPING


async def test_list_pending_on_filters_by_day_and_status(session: AsyncSession):
    repo = SqlAlchemyOrderRepository(session)
    target_day = _dt(2026, 5, 11, 9, 0)
    await repo.save(Order(id=1, customer_name="Ali", created_at=target_day))
    await repo.save(
        Order(
            id=2,
            customer_name="Ayşe",
            created_at=target_day,
            status=OrderStatus.IN_SHIPPING,
        )
    )
    await repo.save(Order(id=3, customer_name="Mehmet", created_at=_dt(2026, 5, 10, 9, 0)))
    await session.commit()

    pending = await repo.list_pending_on(target_day)

    assert [o.id for o in pending] == [1]
