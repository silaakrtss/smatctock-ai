from datetime import datetime

from pydantic import BaseModel, Field

from src.application.services.stock_service import StockInventoryItem
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
