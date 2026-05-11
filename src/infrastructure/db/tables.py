from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

from src.domain.notifications.notification import (
    NotificationChannel,
    NotificationStatus,
)
from src.domain.orders.order_status import OrderStatus
from src.domain.shipping.shipment import ShipmentStatus
from src.infrastructure.db.enum_type import StrEnumType

metadata = MetaData()

products_table = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(200), nullable=False),
    Column("stock", Integer, nullable=False, default=0),
)

orders_table = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("customer_name", String(200), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("status", StrEnumType(OrderStatus), nullable=False),
)

shipments_table = Table(
    "shipments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("carrier", String(120), nullable=False),
    Column("tracking_number", String(120), nullable=False),
    Column("dispatched_at", DateTime(timezone=True), nullable=False),
    Column("expected_delivery_at", DateTime(timezone=True), nullable=False),
    Column("status", StrEnumType(ShipmentStatus), nullable=False),
    Column("delivered_at", DateTime(timezone=True), nullable=True),
)

notifications_table = Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("channel", StrEnumType(NotificationChannel), nullable=False),
    Column("recipient", String(200), nullable=False),
    Column("subject", String(200), nullable=False),
    Column("body", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("status", StrEnumType(NotificationStatus), nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=True),
    Column("failure_reason", String, nullable=True),
)

stock_thresholds_table = Table(
    "stock_thresholds",
    metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("min_quantity", Integer, nullable=False),
)
