from dataclasses import dataclass
from datetime import datetime

from src.application.ports.shipment_repository import ShipmentRepository
from src.domain.shipping.shipment import Shipment


class ShipmentNotFoundError(Exception):
    pass


@dataclass
class ShippingService:
    shipments: ShipmentRepository

    async def find_delayed_shipments(self, now: datetime) -> list[Shipment]:
        active = await self.shipments.list_active()
        return [s for s in active if s.is_delayed(now=now)]

    async def mark_delivered(self, shipment_id: int, at: datetime) -> Shipment:
        shipment = await self.shipments.get_by_id(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")
        shipment.mark_delivered(at)
        await self.shipments.save(shipment)
        return shipment
