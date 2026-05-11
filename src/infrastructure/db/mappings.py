from sqlalchemy.orm import registry

from src.domain.notifications.notification import Notification
from src.domain.orders.order import Order
from src.domain.products.product import Product
from src.domain.shipping.shipment import Shipment
from src.domain.stock.stock_threshold import StockThreshold
from src.infrastructure.db.tables import (
    notifications_table,
    orders_table,
    products_table,
    shipments_table,
    stock_thresholds_table,
)

mapper_registry = registry()


def configure_mappings() -> None:
    if _already_configured():
        return

    mapper_registry.map_imperatively(Product, products_table)
    mapper_registry.map_imperatively(Order, orders_table)
    mapper_registry.map_imperatively(Shipment, shipments_table)
    mapper_registry.map_imperatively(Notification, notifications_table)
    mapper_registry.map_imperatively(StockThreshold, stock_thresholds_table)


def _already_configured() -> bool:
    return any(m.class_ is Product for m in mapper_registry.mappers)
