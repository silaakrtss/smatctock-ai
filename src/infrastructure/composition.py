from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.agent.loop import AgentLoop
from src.agent.prompts.loader import PromptLoader
from src.agent.tools.dispatcher import ToolDispatcher
from src.agent.tools.registry import ToolRegistry
from src.application.ports.llm_client import LLMClient
from src.application.ports.notifier import Notifier
from src.application.ports.scheduler import CronTrigger, Scheduler
from src.infrastructure.db.engine import build_async_engine
from src.infrastructure.db.mappings import configure_mappings
from src.infrastructure.db.session import build_session_factory
from src.infrastructure.llm.gemini_factory import build_gemini_client
from src.infrastructure.llm.minimax_factory import build_minimax_client
from src.infrastructure.notifiers.fanout_notifier import FanoutNotifier
from src.infrastructure.notifiers.frontend_notifier import FrontendNotifier
from src.infrastructure.notifiers.sse_hub import SseHub
from src.infrastructure.notifiers.telegram_notifier import TelegramNotifier
from src.presentation.config.settings import Settings


@dataclass
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    llm_client: LLMClient
    sse_hub: SseHub
    telegram_http: httpx.AsyncClient
    prompt_loader: PromptLoader
    scheduler: Scheduler | None = field(default=None)

    async def build_request_scope(self, session: AsyncSession) -> "RequestScope":
        from src.agent.tools.definitions import TOOL_DEFINITIONS
        from src.agent.tools.handlers import register_default_tools
        from src.application.services.notification_service import NotificationService
        from src.application.services.order_service import OrderService
        from src.application.services.shipping_service import ShippingService
        from src.application.services.stock_service import StockService
        from src.infrastructure.db.repositories.notification_repository import (
            SqlAlchemyNotificationRepository,
        )
        from src.infrastructure.db.repositories.order_repository import (
            SqlAlchemyOrderRepository,
        )
        from src.infrastructure.db.repositories.product_repository import (
            SqlAlchemyProductRepository,
        )
        from src.infrastructure.db.repositories.shipment_repository import (
            SqlAlchemyShipmentRepository,
        )
        from src.infrastructure.db.repositories.stock_threshold_repository import (
            SqlAlchemyStockThresholdRepository,
        )

        notification_repo = SqlAlchemyNotificationRepository(session)
        notifier = _build_fanout_notifier(
            settings=self.settings,
            notification_repo=notification_repo,
            sse_hub=self.sse_hub,
            http_client=self.telegram_http,
        )
        notifications = NotificationService(
            repository=notification_repo,
            notifier=notifier,
            clock=_utcnow,
        )
        stock = StockService(
            products=SqlAlchemyProductRepository(session),
            thresholds=SqlAlchemyStockThresholdRepository(session),
            notifications=notifications,
            supplier_recipient=self.settings.supplier_recipient,
        )
        orders = OrderService(orders=SqlAlchemyOrderRepository(session))
        shipping = ShippingService(shipments=SqlAlchemyShipmentRepository(session))

        registry = ToolRegistry()
        register_default_tools(
            registry=registry,
            stock=stock,
            orders=orders,
            shipping=shipping,
            notifications=notifications,
        )
        dispatcher = ToolDispatcher(registry=registry, definitions=TOOL_DEFINITIONS)
        loop = AgentLoop(
            llm_client=self.llm_client,
            dispatcher=dispatcher,
            max_iterations=self.settings.agent_max_tool_iterations,
        )

        return RequestScope(
            session=session,
            stock=stock,
            orders=orders,
            shipping=shipping,
            notifications=notifications,
            notification_repo=notification_repo,
            agent_loop=loop,
            prompt_loader=self.prompt_loader,
            sse_hub=self.sse_hub,
        )


@dataclass
class RequestScope:
    session: AsyncSession
    stock: Any
    orders: Any
    shipping: Any
    notifications: Any
    notification_repo: Any
    agent_loop: AgentLoop
    prompt_loader: PromptLoader
    sse_hub: SseHub


async def build_container(settings: Settings) -> AppContainer:
    configure_mappings()
    engine = build_async_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    llm_client = _build_llm_client(settings)
    telegram_http = httpx.AsyncClient(timeout=10.0)

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        llm_client=llm_client,
        sse_hub=SseHub(),
        telegram_http=telegram_http,
        prompt_loader=PromptLoader(),
    )


async def dispose_container(container: AppContainer) -> None:
    if container.scheduler is not None:
        await container.scheduler.stop()
    await container.telegram_http.aclose()
    await container.engine.dispose()


async def register_scheduler_jobs(container: AppContainer) -> None:
    from apscheduler import AsyncScheduler

    from src.infrastructure.scheduler.apscheduler_adapter import ApschedulerAdapter
    from src.infrastructure.scheduler.jobs.check_shipping_delays import (
        ShippingDelayJobContext,
        build_check_shipping_delays_job,
    )
    from src.infrastructure.scheduler.jobs.check_stock_thresholds import (
        StockThresholdJobContext,
        build_check_stock_thresholds_job,
    )

    scheduler = ApschedulerAdapter(scheduler=AsyncScheduler())
    container.scheduler = scheduler
    await scheduler.start()
    settings = container.settings

    async def stock_context() -> StockThresholdJobContext:
        async with container.session_factory() as session:
            scope = await container.build_request_scope(session)
            return StockThresholdJobContext(
                stock=scope.stock,
                notifications=scope.notifications,
                manager_recipient=settings.manager_recipient,
            )

    async def shipping_context() -> ShippingDelayJobContext:
        async with container.session_factory() as session:
            scope = await container.build_request_scope(session)
            return ShippingDelayJobContext(
                shipping=scope.shipping,
                notifications=scope.notifications,
                manager_recipient=settings.manager_recipient,
                now=_utcnow,
            )

    await scheduler.add_job(
        build_check_stock_thresholds_job(stock_context),
        trigger=_parse_cron(settings.scheduler_stock_check_cron),
        job_id="check_stock_thresholds",
    )
    await scheduler.add_job(
        build_check_shipping_delays_job(shipping_context),
        trigger=_parse_cron(settings.scheduler_shipping_check_cron),
        job_id="check_shipping_delays",
    )


def _build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "gemini":
        return build_gemini_client(
            api_key=settings.google_api_key,
            model=settings.gemini_model,
        )
    return build_minimax_client(
        api_key=settings.minimax_api_key,
        base_url=settings.minimax_base_url,
        model=settings.minimax_model,
        timeout_seconds=settings.minimax_timeout_seconds,
    )


def _build_fanout_notifier(
    *,
    settings: Settings,
    notification_repo: Any,
    sse_hub: SseHub,
    http_client: httpx.AsyncClient,
) -> Notifier:
    telegram = TelegramNotifier(
        client=http_client,
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )
    frontend = FrontendNotifier(repository=notification_repo, sse_hub=sse_hub)
    return FanoutNotifier(notifiers=[telegram, frontend])


def _parse_cron(expression: str) -> CronTrigger:
    parts = expression.split()
    if len(parts) < 5:
        return CronTrigger()
    minute, hour, _day_of_month, _month, day_of_week = parts[:5]
    return CronTrigger(minute=minute, hour=hour, day_of_week=day_of_week)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
