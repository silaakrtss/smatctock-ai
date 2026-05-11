from enum import Enum


class InvalidStateTransitionError(Exception):
    pass


class OrderStatus(str, Enum):
    PREPARING = "preparing"
    IN_SHIPPING = "in_shipping"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PREPARING: frozenset({OrderStatus.IN_SHIPPING, OrderStatus.CANCELLED}),
    OrderStatus.IN_SHIPPING: frozenset({OrderStatus.DELIVERED, OrderStatus.CANCELLED}),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


def assert_transition_allowed(current: OrderStatus, target: OrderStatus) -> None:
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransitionError(
            f"Cannot transition from {current.value} to {target.value}"
        )
