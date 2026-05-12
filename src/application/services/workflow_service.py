from dataclasses import dataclass
from datetime import datetime

from src.application.services.notification_service import (
    NotificationDraft,
    NotificationService,
)
from src.application.services.order_service import OrderService
from src.application.services.shipping_service import ShippingService
from src.domain.notifications.notification import Notification, NotificationChannel
from src.domain.orders.order import Order
from src.domain.shipping.shipment import Shipment


@dataclass(frozen=True)
class WorkflowTask:
    id: str
    role: str
    title: str
    detail: str
    priority: str
    related_order_id: int | None = None
    tracking_number: str | None = None


@dataclass(frozen=True)
class DailyWorkflowPlan:
    day: datetime
    packing_tasks: list[WorkflowTask]
    shipping_tasks: list[WorkflowTask]
    manager_tasks: list[WorkflowTask]

    @property
    def total_tasks(self) -> int:
        return len(self.packing_tasks) + len(self.shipping_tasks) + len(self.manager_tasks)


@dataclass
class WorkflowService:
    orders: OrderService
    shipping: ShippingService
    notifications: NotificationService
    warehouse_recipient: str
    courier_recipient: str
    manager_recipient: str
    channel: NotificationChannel = NotificationChannel.TELEGRAM

    async def build_daily_plan(self, day: datetime) -> DailyWorkflowPlan:
        preparing_orders = await self.orders.list(status="preparing")
        active_shipments = await self.shipping.list_active_shipments()
        delayed_shipments = await self.shipping.find_delayed_shipments(now=day)
        delayed_ids = {shipment.id for shipment in delayed_shipments}

        return DailyWorkflowPlan(
            day=day,
            packing_tasks=[
                _packing_task(order=order, index=index)
                for index, order in enumerate(preparing_orders, start=1)
            ],
            shipping_tasks=[
                _shipping_task(
                    shipment=shipment,
                    index=index,
                    is_delayed=shipment.id in delayed_ids,
                )
                for index, shipment in enumerate(active_shipments, start=1)
            ],
            manager_tasks=[
                _manager_task(shipment=shipment, index=index)
                for index, shipment in enumerate(delayed_shipments, start=1)
            ],
        )

    async def dispatch_daily_plan(self, day: datetime) -> list[Notification]:
        plan = await self.build_daily_plan(day)
        drafts = [
            NotificationDraft(
                channel=self.channel,
                recipient=self.warehouse_recipient,
                subject="Günlük depo görevleri",
                body=_render_task_message("Depo hazırlık listesi", plan.packing_tasks),
            ),
            NotificationDraft(
                channel=self.channel,
                recipient=self.courier_recipient,
                subject="Günlük kargo görevleri",
                body=_render_task_message("Kargo takip listesi", plan.shipping_tasks),
            ),
        ]
        if plan.manager_tasks:
            drafts.append(
                NotificationDraft(
                    channel=self.channel,
                    recipient=self.manager_recipient,
                    subject="Gecikme müdahale listesi",
                    body=_render_task_message("Yönetici aksiyon listesi", plan.manager_tasks),
                )
            )
        notifications: list[Notification] = []
        for draft in drafts:
            notifications.append(await self.notifications.dispatch(draft))
        return notifications


def _packing_task(*, order: Order, index: int) -> WorkflowTask:
    return WorkflowTask(
        id=f"pack-{order.id}",
        role="warehouse",
        title=f"#{order.id} siparişini hazırla",
        detail=f"{order.customer_name} için paketleme ve çıkış kontrolü yapılacak.",
        priority="normal" if index > 3 else "high",
        related_order_id=order.id,
    )


def _shipping_task(*, shipment: Shipment, index: int, is_delayed: bool) -> WorkflowTask:
    return WorkflowTask(
        id=f"ship-{shipment.id}",
        role="courier",
        title=f"#{shipment.order_id} kargosunu takip et",
        detail=(
            f"{shipment.carrier} / {shipment.tracking_number}; "
            f"beklenen teslim {shipment.expected_delivery_at.isoformat()}."
        ),
        priority="urgent" if is_delayed else ("high" if index <= 3 else "normal"),
        related_order_id=shipment.order_id,
        tracking_number=shipment.tracking_number,
    )


def _manager_task(*, shipment: Shipment, index: int) -> WorkflowTask:
    return WorkflowTask(
        id=f"delay-{shipment.id}",
        role="manager",
        title=f"#{shipment.order_id} gecikmesine müdahale et",
        detail=(
            f"{shipment.carrier} kargosu gecikti; takip numarası "
            f"{shipment.tracking_number}."
        ),
        priority="urgent" if index <= 3 else "high",
        related_order_id=shipment.order_id,
        tracking_number=shipment.tracking_number,
    )


def _render_task_message(title: str, tasks: list[WorkflowTask]) -> str:
    if not tasks:
        return f"{title}: bugün atanacak görev yok."
    lines = [f"{title}:"]
    for task in tasks:
        lines.append(f"- [{task.priority}] {task.title}: {task.detail}")
    return "\n".join(lines)
