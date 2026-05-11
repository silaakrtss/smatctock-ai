from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier, NotifierError
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
)
from src.domain.products.product import Product


@dataclass(frozen=True)
class NotificationDraft:
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str


@dataclass
class NotificationService:
    repository: NotificationRepository
    notifier: Notifier
    clock: Callable[[], datetime]

    async def dispatch(self, draft: NotificationDraft) -> Notification:
        notification = await self._persist_pending(draft)
        try:
            await self.notifier.send(notification)
        except NotifierError as exc:
            notification.mark_failed(str(exc))
            await self.repository.save(notification)
            return notification

        notification.mark_sent(self.clock())
        await self.repository.save(notification)
        return notification

    async def notify_customer(
        self,
        *,
        order_id: int,
        recipient: str,
        message: str,
        channel: NotificationChannel,
    ) -> Notification:
        draft = NotificationDraft(
            channel=channel,
            recipient=recipient,
            subject=f"Sipariş {order_id} bilgilendirmesi",
            body=message,
        )
        return await self.dispatch(draft)

    async def notify_stock_alert(
        self,
        *,
        product: Product,
        min_quantity: int,
        channel: NotificationChannel,
        recipient: str,
    ) -> Notification:
        draft = NotificationDraft(
            channel=channel,
            recipient=recipient,
            subject=f"Stok uyarısı: {product.name}",
            body=(
                f"{product.name} stoku {product.stock} adet; "
                f"eşik {min_quantity} adetin altına düştü."
            ),
        )
        return await self.dispatch(draft)

    async def _persist_pending(self, draft: NotificationDraft) -> Notification:
        notification = Notification(
            id=await self.repository.next_id(),
            channel=draft.channel,
            recipient=draft.recipient,
            subject=draft.subject,
            body=draft.body,
            created_at=self.clock(),
        )
        await self.repository.save(notification)
        return notification
