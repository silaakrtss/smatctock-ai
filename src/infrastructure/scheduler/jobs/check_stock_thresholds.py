from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from src.application.services.notification_service import NotificationService
from src.application.services.stock_service import StockService
from src.domain.notifications.notification import NotificationChannel
from src.domain.products.product import Product


class _StockThresholdContext(Protocol):
    stock: StockService
    notifications: NotificationService
    manager_recipient: str
    manager_channel: NotificationChannel


@dataclass
class StockThresholdJobContext:
    stock: StockService
    notifications: NotificationService
    manager_recipient: str
    manager_channel: NotificationChannel = NotificationChannel.TELEGRAM


def build_check_stock_thresholds_job(
    context_factory: Callable[[], Awaitable[StockThresholdJobContext]],
) -> Callable[[], Awaitable[None]]:
    async def job() -> None:
        context = await context_factory()
        breached = await context.stock.find_below_threshold()
        for product in breached:
            threshold = await _resolve_threshold(context, product)
            await context.notifications.notify_stock_alert(
                product=product,
                min_quantity=threshold,
                channel=context.manager_channel,
                recipient=context.manager_recipient,
            )

    return job


async def _resolve_threshold(context: _StockThresholdContext, product: Product) -> int:
    threshold = await context.stock.thresholds.get_for_product(product.id)
    return threshold.min_quantity if threshold else 0
