from datetime import datetime, timedelta, timezone

from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.application.ports.shipment_repository import ShipmentRepository
from src.application.services.notification_service import NotificationService
from src.application.services.shipping_service import ShippingService
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
)
from src.domain.shipping.shipment import Shipment, ShipmentStatus
from src.infrastructure.scheduler.jobs.check_shipping_delays import (
    ShippingDelayJobContext,
    build_check_shipping_delays_job,
)


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class _FakeShipmentRepo(ShipmentRepository):
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items = {s.id: s for s in shipments}

    async def get_by_id(self, shipment_id: int) -> Shipment | None:
        return self._items.get(shipment_id)

    async def list_active(self) -> list[Shipment]:
        return [s for s in self._items.values() if s.status == ShipmentStatus.DISPATCHED]

    async def save(self, shipment: Shipment) -> None:
        self._items[shipment.id] = shipment

    async def get_by_order(self, order_id: int) -> Shipment | None:
        return None


class _FakeNotificationRepo(NotificationRepository):
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


class _CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


def _make_context(
    now: datetime,
    shipments: list[Shipment],
) -> tuple[ShippingDelayJobContext, _CollectingNotifier]:
    notifier = _CollectingNotifier()
    notifications = NotificationService(
        repository=_FakeNotificationRepo(),
        notifier=notifier,
        clock=lambda: now,
    )
    context = ShippingDelayJobContext(
        shipping=ShippingService(shipments=_FakeShipmentRepo(shipments)),
        notifications=notifications,
        manager_recipient="@manager",
        now=lambda: now,
        manager_channel=NotificationChannel.TELEGRAM,
    )
    return context, notifier


def _shipment(*, shipment_id: int, expected: datetime) -> Shipment:
    return Shipment(
        id=shipment_id,
        order_id=100 + shipment_id,
        carrier="Aras",
        tracking_number=f"TRK-{shipment_id}",
        dispatched_at=expected - timedelta(days=2),
        expected_delivery_at=expected,
    )


class TestCheckShippingDelaysJob:
    async def test_sends_one_notification_per_delayed_shipment(self):
        now = _dt(2026, 5, 12, 10, 0)
        shipments = [
            _shipment(shipment_id=1, expected=now - timedelta(hours=2)),
            _shipment(shipment_id=2, expected=now + timedelta(hours=2)),
        ]
        context, notifier = _make_context(now, shipments)
        job = build_check_shipping_delays_job(_async_returning(context))

        await job()

        assert len(notifier.sent) == 1
        assert "101" in notifier.sent[0].subject

    async def test_no_notifications_when_nothing_delayed(self):
        now = _dt(2026, 5, 12, 10, 0)
        shipments = [_shipment(shipment_id=1, expected=now + timedelta(hours=2))]
        context, notifier = _make_context(now, shipments)
        job = build_check_shipping_delays_job(_async_returning(context))

        await job()

        assert notifier.sent == []


def _async_returning(context: ShippingDelayJobContext):
    async def factory() -> ShippingDelayJobContext:
        return context

    return factory
