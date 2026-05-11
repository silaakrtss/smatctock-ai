import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_creates_all_expected_tables(engine: AsyncEngine):
    async with engine.connect() as conn:
        table_names = await conn.run_sync(lambda sync: inspect(sync).get_table_names())

    assert set(table_names) == {
        "products",
        "orders",
        "shipments",
        "notifications",
        "stock_thresholds",
    }
