from abc import ABC, abstractmethod

from src.domain.shipping.shipment import Shipment


class ShipmentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, shipment_id: int) -> Shipment | None: ...

    @abstractmethod
    async def list_active(self) -> list[Shipment]: ...

    @abstractmethod
    async def save(self, shipment: Shipment) -> None: ...
