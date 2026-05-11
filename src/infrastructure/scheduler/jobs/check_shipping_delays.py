from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from src.application.services.notification_service import (
    NotificationDraft,
    NotificationService,
)
from src.application.services.shipping_service import ShippingService
from src.domain.notifications.notification import NotificationChannel
from src.domain.shipping.shipment import Shipment


@dataclass
class ShippingDelayJobContext:
    shipping: ShippingService
    notifications: NotificationService
    manager_recipient: str
    now: Callable[[], datetime]
    manager_channel: NotificationChannel = NotificationChannel.TELEGRAM


def build_check_shipping_delays_job(
    context_factory: Callable[[], Awaitable[ShippingDelayJobContext]],
) -> Callable[[], Awaitable[None]]:
    async def job() -> None:
        context = await context_factory()
        delayed = await context.shipping.find_delayed_shipments(now=context.now())
        for shipment in delayed:
            await _notify_manager(context, shipment)

    return job


async def _notify_manager(context: ShippingDelayJobContext, shipment: Shipment) -> None:
    draft = NotificationDraft(
        channel=context.manager_channel,
        recipient=context.manager_recipient,
        subject=f"Kargo gecikme uyarısı: sipariş {shipment.order_id}",
        body=(
            f"Sipariş {shipment.order_id} kargo gecikmesinde "
            f"(taşıyıcı: {shipment.carrier}, takip: {shipment.tracking_number}). "
            f"Beklenen teslim: {shipment.expected_delivery_at.isoformat()}."
        ),
    )
    await context.notifications.dispatch(draft)
