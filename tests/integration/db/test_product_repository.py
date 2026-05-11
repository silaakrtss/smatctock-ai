import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.products.product import Product
from src.domain.stock.stock_threshold import StockThreshold
from src.infrastructure.db.repositories.product_repository import (
    SqlAlchemyProductRepository,
)
from src.infrastructure.db.repositories.stock_threshold_repository import (
    SqlAlchemyStockThresholdRepository,
)

pytestmark = pytest.mark.integration


async def test_save_and_get_by_id(session: AsyncSession):
    repo = SqlAlchemyProductRepository(session)
    await repo.save(Product(id=1, name="Domates", stock=40))
    await session.commit()

    fetched = await repo.get_by_id(1)

    assert fetched is not None
    assert fetched.name == "Domates"
    assert fetched.stock == 40


async def test_get_by_id_returns_none_when_missing(session: AsyncSession):
    repo = SqlAlchemyProductRepository(session)

    assert await repo.get_by_id(404) is None


async def test_list_all_returns_inserted_products(session: AsyncSession):
    repo = SqlAlchemyProductRepository(session)
    await repo.save(Product(id=1, name="Domates", stock=40))
    await repo.save(Product(id=2, name="Salatalık", stock=120))
    await session.commit()

    items = await repo.list_all()

    ids = sorted(p.id for p in items)
    assert ids == [1, 2]


async def test_list_below_threshold_joins_threshold_table(session: AsyncSession):
    products = SqlAlchemyProductRepository(session)
    thresholds = SqlAlchemyStockThresholdRepository(session)
    await products.save(Product(id=1, name="Domates", stock=5))
    await products.save(Product(id=2, name="Salatalık", stock=120))
    await products.save(Product(id=3, name="Patates", stock=10))
    await thresholds.save(StockThreshold(product_id=1, min_quantity=10))
    await thresholds.save(StockThreshold(product_id=2, min_quantity=50))
    await thresholds.save(StockThreshold(product_id=3, min_quantity=20))
    await session.commit()

    breached = await products.list_below_threshold()

    ids = sorted(p.id for p in breached)
    assert ids == [1, 3]
