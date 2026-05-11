from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.infrastructure.composition import (
    AppContainer,
    build_container,
    dispose_container,
    register_scheduler_jobs,
)
from src.presentation.api.routes import ai_chat, notifications, orders, products, shipments
from src.presentation.api.routes import pages as pages_router
from src.presentation.config.settings import get_settings

_STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    container = await build_container(settings)
    app.state.container = container
    if settings.scheduler_enabled:
        await register_scheduler_jobs(container)
    try:
        yield
    finally:
        await dispose_container(container)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Kooperatif Operasyon Ajanı",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(products.router)
    app.include_router(orders.router)
    app.include_router(shipments.router)
    app.include_router(notifications.router)
    app.include_router(ai_chat.router)
    app.include_router(pages_router.router)

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

    return app


app = create_app()


def get_container(app: FastAPI) -> AppContainer:
    return app.state.container  # type: ignore[no-any-return]
