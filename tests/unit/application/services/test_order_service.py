from datetime import datetime, timezone

import pytest
from src.application.ports.order_repository import OrderRepository
from src.application.services.order_service import OrderNotFoundError, OrderService
from src.domain.orders.order import Order
from src.domain.orders.order_status import InvalidStateTransitionError, OrderStatus


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class FakeOrderRepository(OrderRepository):
    def __init__(self, orders: list[Order]) -> None:
        self._items: dict[int, Order] = {o.id: o for o in orders}

    async def get_by_id(self, order_id: int) -> Order | None:
        return self._items.get(order_id)

    async def list_all(self) -> list[Order]:
        return list(self._items.values())

    async def save(self, order: Order) -> None:
        self._items[order.id] = order

    async def list_pending_on(self, day: datetime) -> list[Order]:
        target_date = day.date()
        return [
            o
            for o in self._items.values()
            if o.status == OrderStatus.PREPARING and o.created_at.date() == target_date
        ]

    async def list_filtered(
        self,
        *,
        status: str | None = None,
        day: datetime | None = None,
        customer_name: str | None = None,
    ) -> list[Order]:
        results = list(self._items.values())
        if status is not None:
            results = [o for o in results if o.status.value == status]
        if day is not None:
            results = [o for o in results if o.created_at.date() == day.date()]
        if customer_name is not None:
            normalized = customer_name.lower()
            results = [o for o in results if o.customer_name.lower() == normalized]
        return results


class TestGetOrder:
    async def test_returns_order_when_exists(self):
        order = Order(id=101, customer_name="Ali", created_at=_dt(2026, 5, 11, 9, 0))
        service = OrderService(orders=FakeOrderRepository([order]))

        result = await service.get_order(101)

        assert result.id == 101

    async def test_raises_when_missing(self):
        service = OrderService(orders=FakeOrderRepository([]))

        with pytest.raises(OrderNotFoundError):
            await service.get_order(404)


class TestListPendingOrders:
    async def test_returns_only_preparing_for_given_day(self):
        target = _dt(2026, 5, 11, 9, 0)
        orders = [
            Order(id=1, customer_name="Ali", created_at=target),
            Order(
                id=2,
                customer_name="Ayşe",
                created_at=target,
                status=OrderStatus.IN_SHIPPING,
            ),
            Order(id=3, customer_name="Mehmet", created_at=_dt(2026, 5, 10, 9, 0)),
        ]
        service = OrderService(orders=FakeOrderRepository(orders))

        pending = await service.list_pending_orders(target)

        assert [o.id for o in pending] == [1]


class TestTransitionOrderStatus:
    async def test_persists_new_status(self):
        order = Order(id=1, customer_name="Ali", created_at=_dt(2026, 5, 11, 9, 0))
        repo = FakeOrderRepository([order])
        service = OrderService(orders=repo)

        result = await service.transition_order_status(1, OrderStatus.IN_SHIPPING)

        assert result.status == OrderStatus.IN_SHIPPING
        stored = await repo.get_by_id(1)
        assert stored is not None
        assert stored.status == OrderStatus.IN_SHIPPING

    async def test_invalid_transition_propagates(self):
        order = Order(
            id=1,
            customer_name="Ali",
            created_at=_dt(2026, 5, 11, 9, 0),
            status=OrderStatus.DELIVERED,
        )
        service = OrderService(orders=FakeOrderRepository([order]))

        with pytest.raises(InvalidStateTransitionError):
            await service.transition_order_status(1, OrderStatus.PREPARING)

    async def test_unknown_order_raises(self):
        service = OrderService(orders=FakeOrderRepository([]))

        with pytest.raises(OrderNotFoundError):
            await service.transition_order_status(99, OrderStatus.IN_SHIPPING)


class TestListOrders:
    async def test_filters_by_status_and_customer(self):
        target = _dt(2026, 5, 11, 9, 0)
        orders = [
            Order(id=1, customer_name="Ali", created_at=target),
            Order(
                id=2,
                customer_name="Ali",
                created_at=target,
                status=OrderStatus.IN_SHIPPING,
            ),
            Order(id=3, customer_name="Ayşe", created_at=target),
        ]
        service = OrderService(orders=FakeOrderRepository(orders))

        result = await service.list(status="preparing", customer_name="Ali")

        assert [o.id for o in result] == [1]

    async def test_no_filters_returns_all(self):
        orders = [
            Order(id=1, customer_name="Ali", created_at=_dt(2026, 5, 11, 9, 0)),
            Order(id=2, customer_name="Ayşe", created_at=_dt(2026, 5, 10, 9, 0)),
        ]
        service = OrderService(orders=FakeOrderRepository(orders))

        result = await service.list()

        assert {o.id for o in result} == {1, 2}
