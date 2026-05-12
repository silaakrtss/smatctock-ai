from datetime import datetime, timedelta, timezone

from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.application.ports.order_repository import OrderRepository
from src.application.ports.shipment_repository import ShipmentRepository
from src.application.services.notification_service import NotificationService
from src.application.services.order_service import OrderService
from src.application.services.shipping_service import ShippingService
from src.application.services.workflow_service import WorkflowService
from src.domain.notifications.notification import Notification
from src.domain.orders.order import Order
from src.domain.orders.order_status import OrderStatus
from src.domain.shipping.shipment import Shipment, ShipmentStatus


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class FakeOrderRepo(OrderRepository):
    def __init__(self, orders: list[Order]) -> None:
        self._items = {order.id: order for order in orders}

    async def get_by_id(self, order_id: int) -> Order | None:
        return self._items.get(order_id)

    async def list_all(self) -> list[Order]:
        return list(self._items.values())

    async def save(self, order: Order) -> None:
        self._items[order.id] = order

    async def list_pending_on(self, day: datetime) -> list[Order]:
        return [order for order in self._items.values() if order.status == OrderStatus.PREPARING]

    async def list_filtered(
        self,
        *,
        status: str | None = None,
        day: datetime | None = None,
        customer_name: str | None = None,
    ) -> list[Order]:
        result = list(self._items.values())
        if status is not None:
            result = [order for order in result if order.status.value == status]
        return result


class FakeShipmentRepo(ShipmentRepository):
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items = {shipment.id: shipment for shipment in shipments}

    async def get_by_id(self, shipment_id: int) -> Shipment | None:
        return self._items.get(shipment_id)

    async def list_active(self) -> list[Shipment]:
        return [
            shipment
            for shipment in self._items.values()
            if shipment.status == ShipmentStatus.DISPATCHED
        ]

    async def save(self, shipment: Shipment) -> None:
        self._items[shipment.id] = shipment

    async def get_by_order(self, order_id: int) -> Shipment | None:
        return next(
            (shipment for shipment in self._items.values() if shipment.order_id == order_id),
            None,
        )


class FakeNotificationRepo(NotificationRepository):
    def __init__(self) -> None:
        self.saved: list[Notification] = []
        self._next = 1

    async def save(self, notification: Notification) -> None:
        self.saved.append(notification)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return None

    async def next_id(self) -> int:
        value = self._next
        self._next += 1
        return value

    async def list_recent(self, limit: int = 20) -> list[Notification]:
        return self.saved[-limit:]


class CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


def _service(now: datetime) -> tuple[WorkflowService, CollectingNotifier]:
    orders = OrderService(
        orders=FakeOrderRepo(
            [
                Order(id=101, customer_name="Ali", created_at=now),
                Order(
                    id=102,
                    customer_name="Ayşe",
                    created_at=now,
                    status=OrderStatus.IN_SHIPPING,
                ),
            ]
        )
    )
    shipping = ShippingService(
        shipments=FakeShipmentRepo(
            [
                Shipment(
                    id=1,
                    order_id=102,
                    carrier="Aras",
                    tracking_number="TRK-102",
                    dispatched_at=now - timedelta(days=1),
                    expected_delivery_at=now - timedelta(hours=1),
                )
            ]
        )
    )
    notifier = CollectingNotifier()
    notifications = NotificationService(
        repository=FakeNotificationRepo(),
        notifier=notifier,
        clock=lambda: now,
    )
    service = WorkflowService(
        orders=orders,
        shipping=shipping,
        notifications=notifications,
        warehouse_recipient="@depo",
        courier_recipient="@kurye",
        manager_recipient="@manager",
    )
    return service, notifier


class TestWorkflowService:
    async def test_build_daily_plan_groups_tasks_by_role(self):
        service, _notifier = _service(_dt(2026, 5, 12, 8, 0))

        plan = await service.build_daily_plan(_dt(2026, 5, 12, 8, 0))

        assert plan.total_tasks == 3
        assert plan.packing_tasks[0].role == "warehouse"
        assert plan.shipping_tasks[0].priority == "urgent"
        assert plan.manager_tasks[0].related_order_id == 102

    async def test_dispatch_daily_plan_notifies_teams(self):
        service, notifier = _service(_dt(2026, 5, 12, 8, 0))

        notifications = await service.dispatch_daily_plan(_dt(2026, 5, 12, 8, 0))

        assert {notification.recipient for notification in notifications} == {
            "@depo",
            "@kurye",
            "@manager",
        }
        assert len(notifier.sent) == 3
