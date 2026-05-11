from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def build_async_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url, echo=False, future=True)
    _enable_sqlite_pragmas(engine.sync_engine)
    return engine


def _enable_sqlite_pragmas(sync_engine: Engine) -> None:
    @event.listens_for(sync_engine, "connect")
    def _set_pragmas(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
