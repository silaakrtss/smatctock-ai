from datetime import datetime, timezone

from pydantic import BaseModel, Field

from src.application.services.stock_service import StockInventoryItem
from src.application.services.workflow_service import DailyWorkflowPlan, WorkflowTask
from src.domain.notifications.notification import Notification
from src.domain.orders.order import Order
from src.domain.products.product import Product
from src.domain.shipping.shipment import Shipment


class AiChatRequest(BaseModel):
    message: str = Field(min_length=1)
    message_id: str | None = None


class AiChatResponse(BaseModel):
    answer: str


class ProductRead(BaseModel):
    id: int
    name: str
    stock: int

    @classmethod
    def from_domain(cls, product: Product) -> "ProductRead":
        return cls(id=product.id, name=product.name, stock=product.stock)


class InventoryItemRead(BaseModel):
    id: int
    name: str
    stock: int
    min_quantity: int | None
    status: str
    suggested_reorder_quantity: int

    @classmethod
    def from_service(cls, item: StockInventoryItem) -> "InventoryItemRead":
        return cls(
            id=item.product.id,
            name=item.product.name,
            stock=item.product.stock,
            min_quantity=item.min_quantity,
            status=item.status,
            suggested_reorder_quantity=item.suggested_reorder_quantity,
        )


class StockAdjustmentRequest(BaseModel):
    delta: int


class ReorderDraftRequest(BaseModel):
    quantity: int | None = None


class OrderRead(BaseModel):
    id: int
    customer_name: str
    status: str
    created_at: datetime

    @classmethod
    def from_domain(cls, order: Order) -> "OrderRead":
        return cls(
            id=order.id,
            customer_name=order.customer_name,
            status=order.status.value,
            created_at=order.created_at,
        )


class ShipmentRead(BaseModel):
    id: int
    order_id: int
    carrier: str
    tracking_number: str
    status: str
    expected_delivery_at: datetime
    delivered_at: datetime | None

    @classmethod
    def from_domain(cls, shipment: Shipment) -> "ShipmentRead":
        return cls(
            id=shipment.id,
            order_id=shipment.order_id,
            carrier=shipment.carrier,
            tracking_number=shipment.tracking_number,
            status=shipment.status.value,
            expected_delivery_at=shipment.expected_delivery_at,
            delivered_at=shipment.delivered_at,
        )


class ShipmentOverviewRead(BaseModel):
    id: int
    order_id: int
    carrier: str
    tracking_number: str
    status: str
    expected_delivery_at: datetime
    delivered_at: datetime | None
    is_delayed: bool
    minutes_until_expected: int

    @classmethod
    def from_domain(cls, shipment: Shipment, *, now: datetime) -> "ShipmentOverviewRead":
        expected_delivery_at = _as_utc(shipment.expected_delivery_at)
        delivered_at = _as_utc(shipment.delivered_at) if shipment.delivered_at else None
        current_time = _as_utc(now)
        delta = expected_delivery_at - current_time
        return cls(
            id=shipment.id,
            order_id=shipment.order_id,
            carrier=shipment.carrier,
            tracking_number=shipment.tracking_number,
            status=shipment.status.value,
            expected_delivery_at=expected_delivery_at,
            delivered_at=delivered_at,
            is_delayed=shipment.is_delayed(now=current_time),
            minutes_until_expected=int(delta.total_seconds() // 60),
        )


class NotificationRead(BaseModel):
    id: int
    channel: str
    recipient: str
    subject: str
    body: str
    created_at: datetime
    status: str

    @classmethod
    def from_domain(cls, notification: Notification) -> "NotificationRead":
        return cls(
            id=notification.id,
            channel=notification.channel.value,
            recipient=notification.recipient,
            subject=notification.subject,
            body=notification.body,
            created_at=notification.created_at,
            status=notification.status.value,
        )


class WorkflowTaskRead(BaseModel):
    id: str
    role: str
    title: str
    detail: str
    priority: str
    related_order_id: int | None
    tracking_number: str | None

    @classmethod
    def from_service(cls, task: WorkflowTask) -> "WorkflowTaskRead":
        return cls(
            id=task.id,
            role=task.role,
            title=task.title,
            detail=task.detail,
            priority=task.priority,
            related_order_id=task.related_order_id,
            tracking_number=task.tracking_number,
        )


class DailyWorkflowPlanRead(BaseModel):
    day: datetime
    total_tasks: int
    packing_tasks: list[WorkflowTaskRead]
    shipping_tasks: list[WorkflowTaskRead]
    manager_tasks: list[WorkflowTaskRead]

    @classmethod
    def from_service(cls, plan: DailyWorkflowPlan) -> "DailyWorkflowPlanRead":
        return cls(
            day=plan.day,
            total_tasks=plan.total_tasks,
            packing_tasks=[WorkflowTaskRead.from_service(task) for task in plan.packing_tasks],
            shipping_tasks=[WorkflowTaskRead.from_service(task) for task in plan.shipping_tasks],
            manager_tasks=[WorkflowTaskRead.from_service(task) for task in plan.manager_tasks],
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
