from datetime import datetime, timezone

import pytest
from src.domain.orders.order import Order
from src.domain.orders.order_status import InvalidStateTransitionError, OrderStatus


def _now() -> datetime:
    return datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)


class TestOrderCreation:
    def test_creates_order_with_default_status(self):
        order = Order(id=101, customer_name="Ali", created_at=_now())

        assert order.id == 101
        assert order.customer_name == "Ali"
        assert order.status == OrderStatus.PREPARING

    def test_customer_name_cannot_be_empty(self):
        with pytest.raises(ValueError, match="customer_name"):
            Order(id=101, customer_name="", created_at=_now())


class TestOrderTransition:
    def test_transition_to_updates_status(self):
        order = Order(id=101, customer_name="Ali", created_at=_now())

        order.transition_to(OrderStatus.IN_SHIPPING)

        assert order.status == OrderStatus.IN_SHIPPING

    def test_transition_rejects_invalid_state(self):
        order = Order(
            id=101,
            customer_name="Ali",
            created_at=_now(),
            status=OrderStatus.DELIVERED,
        )

        with pytest.raises(InvalidStateTransitionError):
            order.transition_to(OrderStatus.PREPARING)
