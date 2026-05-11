"""Dev seed CLI.

Kullanım:
    python -m src.infrastructure.db.seed_cli
    make seed

Settings'teki DATABASE_URL'i okur, mapping'leri yükler, seed_dev_data'yı
çağırır ve commit eder. Production'da çağrılmamalı; ADR-0006 § 5
seed'in yalnızca dev/test için olduğunu söyler.
"""

import asyncio

from src.infrastructure.db.engine import build_async_engine
from src.infrastructure.db.mappings import configure_mappings
from src.infrastructure.db.seed import seed_dev_data
from src.infrastructure.db.session import build_session_factory
from src.presentation.config.settings import get_settings


async def _run() -> None:
    settings = get_settings()
    configure_mappings()
    engine = build_async_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    try:
        async with session_factory() as session:
            await seed_dev_data(session)
            await session.commit()
        print(f"seed ok → {settings.database_url}")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
