from datetime import datetime, timezone

from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier, NotifierError
from src.application.services.notification_service import (
    NotificationDraft,
    NotificationService,
)
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from src.domain.products.product import Product


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class FakeNotificationRepository(NotificationRepository):
    def __init__(self) -> None:
        self.saved: list[Notification] = []
        self._next_id = 1

    async def save(self, notification: Notification) -> None:
        for index, existing in enumerate(self.saved):
            if existing.id == notification.id:
                self.saved[index] = notification
                return
        self.saved.append(notification)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        for notification in self.saved:
            if notification.id == notification_id:
                return notification
        return None

    async def next_id(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


class CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


class FailingNotifier(Notifier):
    async def send(self, notification: Notification) -> None:
        raise NotifierError("transport failed")


def _draft() -> NotificationDraft:
    return NotificationDraft(
        channel=NotificationChannel.TELEGRAM,
        recipient="@operator",
        subject="Stok uyarısı",
        body="Domates eşik altında.",
    )


class TestDispatchNotification:
    async def test_persists_and_sends_on_success(self):
        repository = FakeNotificationRepository()
        notifier = CollectingNotifier()
        service = NotificationService(
            repository=repository,
            notifier=notifier,
            clock=lambda: _dt(2026, 5, 11, 8, 0),
        )

        result = await service.dispatch(_draft())

        assert result.status == NotificationStatus.SENT
        assert result.sent_at == _dt(2026, 5, 11, 8, 0)
        assert len(notifier.sent) == 1
        stored = await repository.get_by_id(result.id)
        assert stored is not None
        assert stored.status == NotificationStatus.SENT

    async def test_marks_failed_when_notifier_raises(self):
        repository = FakeNotificationRepository()
        service = NotificationService(
            repository=repository,
            notifier=FailingNotifier(),
            clock=lambda: _dt(2026, 5, 11, 8, 0),
        )

        result = await service.dispatch(_draft())

        assert result.status == NotificationStatus.FAILED
        assert result.failure_reason == "transport failed"
        stored = await repository.get_by_id(result.id)
        assert stored is not None
        assert stored.status == NotificationStatus.FAILED


class TestNotifyStockAlert:
    async def test_builds_notification_for_low_stock_product(self):
        repository = FakeNotificationRepository()
        notifier = CollectingNotifier()
        service = NotificationService(
            repository=repository,
            notifier=notifier,
            clock=lambda: _dt(2026, 5, 11, 8, 0),
        )
        product = Product(id=1, name="Domates", stock=3)

        result = await service.notify_stock_alert(
            product=product,
            min_quantity=10,
            channel=NotificationChannel.TELEGRAM,
            recipient="@operator",
        )

        assert "Domates" in result.body
        assert "3" in result.body
        assert "10" in result.body
        assert result.status == NotificationStatus.SENT
