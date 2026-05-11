import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.shipping_service import ShippingService
from src.application.services.stock_service import StockService
from src.infrastructure.db.repositories.product_repository import (
    SqlAlchemyProductRepository,
)
from src.infrastructure.db.repositories.shipment_repository import (
    SqlAlchemyShipmentRepository,
)
from src.infrastructure.db.repositories.stock_threshold_repository import (
    SqlAlchemyStockThresholdRepository,
)
from src.infrastructure.db.seed import seed_dev_data

pytestmark = pytest.mark.integration


async def test_seed_creates_below_threshold_products(session: AsyncSession):
    await seed_dev_data(session)
    await session.commit()
    service = StockService(
        products=SqlAlchemyProductRepository(session),
        thresholds=SqlAlchemyStockThresholdRepository(session),
    )

    breached = await service.find_below_threshold()

    breached_names = sorted(p.name for p in breached)
    assert breached_names == ["Domates", "Patates"]


async def test_seed_creates_active_shipment(session: AsyncSession):
    await seed_dev_data(session)
    await session.commit()
    service = ShippingService(shipments=SqlAlchemyShipmentRepository(session))

    active = await service.shipments.list_active()

    assert [s.id for s in active] == [1]
