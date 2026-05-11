from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.shipment_repository import ShipmentRepository
from src.domain.shipping.shipment import Shipment, ShipmentStatus
from src.infrastructure.db.tables import shipments_table


@dataclass
class SqlAlchemyShipmentRepository(ShipmentRepository):
    session: AsyncSession

    async def get_by_id(self, shipment_id: int) -> Shipment | None:
        result = await self.session.execute(
            select(Shipment).where(shipments_table.c.id == shipment_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Shipment]:
        stmt = select(Shipment).where(shipments_table.c.status == ShipmentStatus.DISPATCHED)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, shipment: Shipment) -> None:
        await self.session.merge(shipment)
