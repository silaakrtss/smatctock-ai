from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.stock_threshold_repository import StockThresholdRepository
from src.domain.stock.stock_threshold import StockThreshold
from src.infrastructure.db.tables import stock_thresholds_table


@dataclass
class SqlAlchemyStockThresholdRepository(StockThresholdRepository):
    session: AsyncSession

    async def get_for_product(self, product_id: int) -> StockThreshold | None:
        result = await self.session.execute(
            select(StockThreshold).where(stock_thresholds_table.c.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[StockThreshold]:
        result = await self.session.execute(select(StockThreshold))
        return list(result.scalars().all())

    async def save(self, threshold: StockThreshold) -> None:
        await self.session.merge(threshold)
