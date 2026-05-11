import asyncio
from datetime import datetime, timezone

from src.application.ports.notification_repository import NotificationRepository
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from src.infrastructure.notifiers.frontend_notifier import FrontendNotifier
from src.infrastructure.notifiers.sse_hub import SseHub


def _dt() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


class _MemoryNotificationRepo(NotificationRepository):
    def __init__(self) -> None:
        self.saved: list[Notification] = []
        self._next = 1

    async def save(self, notification: Notification) -> None:
        for index, existing in enumerate(self.saved):
            if existing.id == notification.id:
                self.saved[index] = notification
                return
        self.saved.append(notification)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return next((n for n in self.saved if n.id == notification_id), None)

    async def next_id(self) -> int:
        value = self._next
        self._next += 1
        return value


def _notification() -> Notification:
    return Notification(
        id=1,
        channel=NotificationChannel.SSE,
        recipient="customer-1",
        subject="Sipariş kargoda",
        body="Siparişiniz yola çıktı.",
        created_at=_dt(),
        status=NotificationStatus.PENDING,
    )


class TestFrontendNotifier:
    async def test_persists_notification_and_publishes_event(self):
        repository = _MemoryNotificationRepo()
        hub = SseHub()
        subscriber = hub.subscribe()
        notifier = FrontendNotifier(repository=repository, sse_hub=hub)

        await notifier.send(_notification())

        stored = await repository.get_by_id(1)
        assert stored is not None
        event = await asyncio.wait_for(subscriber.get(), timeout=0.1)
        assert event["id"] == 1
        assert event["subject"] == "Sipariş kargoda"
