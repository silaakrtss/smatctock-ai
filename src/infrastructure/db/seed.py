from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from src.domain.orders.order import Order
from src.domain.orders.order_status import OrderStatus
from src.domain.products.product import Product
from src.domain.shipping.shipment import Shipment, ShipmentStatus
from src.domain.stock.stock_threshold import StockThreshold
from src.infrastructure.db.repositories.notification_repository import (
    SqlAlchemyNotificationRepository,
)
from src.infrastructure.db.repositories.order_repository import (
    SqlAlchemyOrderRepository,
)
from src.infrastructure.db.repositories.product_repository import (
    SqlAlchemyProductRepository,
)
from src.infrastructure.db.repositories.shipment_repository import (
    SqlAlchemyShipmentRepository,
)
from src.infrastructure.db.repositories.stock_threshold_repository import (
    SqlAlchemyStockThresholdRepository,
)


async def seed_dev_data(session: AsyncSession) -> None:
    await _seed_products_and_thresholds(session)
    await _seed_orders_and_shipments(session)


async def _seed_products_and_thresholds(session: AsyncSession) -> None:
    products = SqlAlchemyProductRepository(session)
    thresholds = SqlAlchemyStockThresholdRepository(session)
    catalogue = [
        (Product(id=1, name="Domates", stock=8), StockThreshold(product_id=1, min_quantity=20)),
        (Product(id=2, name="Salatalık", stock=120), StockThreshold(product_id=2, min_quantity=40)),
        (Product(id=3, name="Patates", stock=15), StockThreshold(product_id=3, min_quantity=25)),
    ]
    for product, threshold in catalogue:
        await products.save(product)
        await thresholds.save(threshold)


async def _seed_orders_and_shipments(session: AsyncSession) -> None:
    orders = SqlAlchemyOrderRepository(session)
    shipments = SqlAlchemyShipmentRepository(session)
    today = datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc)

    await orders.save(Order(id=101, customer_name="Ali", created_at=today))
    await orders.save(
        Order(
            id=102,
            customer_name="Ayşe",
            created_at=today - timedelta(days=1),
            status=OrderStatus.IN_SHIPPING,
        )
    )
    await orders.save(
        Order(
            id=103,
            customer_name="Mehmet",
            created_at=today - timedelta(days=2),
            status=OrderStatus.DELIVERED,
        )
    )

    expected = today + timedelta(days=1)
    await shipments.save(
        Shipment(
            id=1,
            order_id=102,
            carrier="Aras",
            tracking_number="TRK-102",
            dispatched_at=today - timedelta(hours=12),
            expected_delivery_at=expected,
            status=ShipmentStatus.DISPATCHED,
        )
    )


async def seed_pending_notification(session: AsyncSession) -> Notification:
    repo = SqlAlchemyNotificationRepository(session)
    notification = Notification(
        id=await repo.next_id(),
        channel=NotificationChannel.TELEGRAM,
        recipient="@operator",
        subject="Stok uyarısı: Domates",
        body="Domates stoku eşik altında.",
        created_at=datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc),
        status=NotificationStatus.PENDING,
    )
    await repo.save(notification)
    return notification
