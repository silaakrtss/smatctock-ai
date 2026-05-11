from dataclasses import dataclass
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.order_repository import OrderRepository
from src.domain.orders.order import Order
from src.domain.orders.order_status import OrderStatus
from src.infrastructure.db.tables import orders_table


@dataclass
class SqlAlchemyOrderRepository(OrderRepository):
    session: AsyncSession

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(select(Order).where(orders_table.c.id == order_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Order]:
        result = await self.session.execute(select(Order))
        return list(result.scalars().all())

    async def save(self, order: Order) -> None:
        await self.session.merge(order)

    async def list_pending_on(self, day: datetime) -> list[Order]:
        start, end = _day_bounds(day)
        stmt = (
            select(Order)
            .where(orders_table.c.status == OrderStatus.PREPARING)
            .where(orders_table.c.created_at >= start)
            .where(orders_table.c.created_at < end)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


def _day_bounds(reference: datetime) -> tuple[datetime, datetime]:
    start = datetime.combine(reference.date(), time.min, tzinfo=reference.tzinfo)
    return start, start + timedelta(days=1)
