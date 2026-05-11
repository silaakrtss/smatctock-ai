from dataclasses import dataclass, field
from datetime import datetime

from src.domain.orders.order_status import OrderStatus, assert_transition_allowed


@dataclass
class Order:
    id: int
    customer_name: str
    created_at: datetime
    status: OrderStatus = field(default=OrderStatus.PREPARING)

    def __post_init__(self) -> None:
        if not self.customer_name or not self.customer_name.strip():
            raise ValueError("Order customer_name cannot be empty")

    def transition_to(self, target: OrderStatus) -> None:
        assert_transition_allowed(self.status, target)
        self.status = target
