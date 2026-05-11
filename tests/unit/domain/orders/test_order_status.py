import pytest
from src.domain.orders.order_status import (
    InvalidStateTransitionError,
    OrderStatus,
    assert_transition_allowed,
)


class TestOrderStatusTransitions:
    def test_preparing_to_in_shipping_allowed(self):
        assert_transition_allowed(OrderStatus.PREPARING, OrderStatus.IN_SHIPPING)

    def test_in_shipping_to_delivered_allowed(self):
        assert_transition_allowed(OrderStatus.IN_SHIPPING, OrderStatus.DELIVERED)

    def test_preparing_to_cancelled_allowed(self):
        assert_transition_allowed(OrderStatus.PREPARING, OrderStatus.CANCELLED)

    def test_delivered_to_preparing_rejected(self):
        with pytest.raises(InvalidStateTransitionError):
            assert_transition_allowed(OrderStatus.DELIVERED, OrderStatus.PREPARING)

    def test_cancelled_is_terminal(self):
        with pytest.raises(InvalidStateTransitionError):
            assert_transition_allowed(OrderStatus.CANCELLED, OrderStatus.IN_SHIPPING)

    def test_delivered_is_terminal(self):
        with pytest.raises(InvalidStateTransitionError):
            assert_transition_allowed(OrderStatus.DELIVERED, OrderStatus.CANCELLED)
