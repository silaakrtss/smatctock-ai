from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AlreadyDeliveredError(Exception):
    pass


class ShipmentStatus(str, Enum):
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"


@dataclass
class Shipment:
    id: int
    order_id: int
    carrier: str
    tracking_number: str
    dispatched_at: datetime
    expected_delivery_at: datetime
    status: ShipmentStatus = field(default=ShipmentStatus.DISPATCHED)
    delivered_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.tracking_number or not self.tracking_number.strip():
            raise ValueError("Shipment tracking_number cannot be empty")
        if not self.carrier or not self.carrier.strip():
            raise ValueError("Shipment carrier cannot be empty")

    def is_delayed(self, now: datetime) -> bool:
        if self.status == ShipmentStatus.DELIVERED:
            return False
        return now > self.expected_delivery_at

    def mark_delivered(self, at: datetime) -> None:
        if self.status == ShipmentStatus.DELIVERED:
            raise AlreadyDeliveredError(f"Shipment {self.id} already delivered")
        self.status = ShipmentStatus.DELIVERED
        self.delivered_at = at
