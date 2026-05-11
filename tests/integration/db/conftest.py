from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from src.infrastructure.db.engine import build_async_engine
from src.infrastructure.db.mappings import configure_mappings
from src.infrastructure.db.session import build_session_factory
from src.infrastructure.db.tables import metadata


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    configure_mappings()
    engine = build_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return build_session_factory(engine)


@pytest_asyncio.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
