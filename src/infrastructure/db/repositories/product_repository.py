from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.product_repository import ProductRepository
from src.domain.products.product import Product
from src.infrastructure.db.tables import products_table, stock_thresholds_table


@dataclass
class SqlAlchemyProductRepository(ProductRepository):
    session: AsyncSession

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product).where(products_table.c.id == product_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Product]:
        result = await self.session.execute(select(Product))
        return list(result.scalars().all())

    async def save(self, product: Product) -> None:
        await self.session.merge(product)

    async def list_below_threshold(self) -> list[Product]:
        join = products_table.join(
            stock_thresholds_table,
            products_table.c.id == stock_thresholds_table.c.product_id,
        )
        stmt = (
            select(Product)
            .select_from(join)
            .where(products_table.c.stock < stock_thresholds_table.c.min_quantity)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
