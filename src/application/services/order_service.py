from dataclasses import dataclass
from datetime import datetime

from src.application.ports.order_repository import OrderRepository
from src.domain.orders.order import Order
from src.domain.orders.order_status import OrderStatus


class OrderNotFoundError(Exception):
    pass


@dataclass
class OrderService:
    orders: OrderRepository

    async def get_order(self, order_id: int) -> Order:
        order = await self.orders.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found")
        return order

    async def list_pending_orders(self, day: datetime) -> list[Order]:
        return await self.orders.list_pending_on(day)

    async def transition_order_status(self, order_id: int, target: OrderStatus) -> Order:
        order = await self.get_order(order_id)
        order.transition_to(target)
        await self.orders.save(order)
        return order

    async def list(
        self,
        *,
        status: str | None = None,
        day: datetime | None = None,
        customer_name: str | None = None,
    ) -> list[Order]:
        return await self.orders.list_filtered(status=status, day=day, customer_name=customer_name)
