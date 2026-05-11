from datetime import datetime, timezone

import pytest
from src.agent.tools.handlers import register_default_tools
from src.agent.tools.registry import ToolRegistry
from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.application.ports.order_repository import OrderRepository
from src.application.ports.product_repository import ProductRepository
from src.application.ports.shipment_repository import ShipmentRepository
from src.application.ports.stock_threshold_repository import StockThresholdRepository
from src.application.services.notification_service import NotificationService
from src.application.services.order_service import OrderService
from src.application.services.shipping_service import ShippingService
from src.application.services.stock_service import StockService
from src.domain.notifications.notification import Notification
from src.domain.orders.order import Order
from src.domain.products.product import Product
from src.domain.shipping.shipment import Shipment, ShipmentStatus
from src.domain.stock.stock_threshold import StockThreshold


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class FakeProductRepo(ProductRepository):
    def __init__(self, products: list[Product]) -> None:
        self._items = {p.id: p for p in products}

    async def get_by_id(self, product_id: int) -> Product | None:
        return self._items.get(product_id)

    async def get_by_name(self, name: str) -> Product | None:
        normalized = name.strip().lower()
        for p in self._items.values():
            if p.name.lower() == normalized:
                return p
        return None

    async def list_all(self) -> list[Product]:
        return list(self._items.values())

    async def save(self, product: Product) -> None:
        self._items[product.id] = product

    async def list_below_threshold(self) -> list[Product]:
        return [p for p in self._items.values() if p.stock < 10]


class FakeThresholdRepo(StockThresholdRepository):
    async def get_for_product(self, product_id: int) -> StockThreshold | None:
        return None

    async def list_all(self) -> list[StockThreshold]:
        return []


class FakeOrderRepo(OrderRepository):
    def __init__(self, orders: list[Order]) -> None:
        self._items = {o.id: o for o in orders}

    async def get_by_id(self, order_id: int) -> Order | None:
        return self._items.get(order_id)

    async def list_all(self) -> list[Order]:
        return list(self._items.values())

    async def save(self, order: Order) -> None:
        self._items[order.id] = order

    async def list_pending_on(self, day: datetime) -> list[Order]:
        return []

    async def list_filtered(
        self,
        *,
        status: str | None = None,
        day: datetime | None = None,
        customer_name: str | None = None,
    ) -> list[Order]:
        return list(self._items.values())


class FakeShipmentRepo(ShipmentRepository):
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items = {s.id: s for s in shipments}

    async def get_by_id(self, shipment_id: int) -> Shipment | None:
        return self._items.get(shipment_id)

    async def list_active(self) -> list[Shipment]:
        return [s for s in self._items.values() if s.status == ShipmentStatus.DISPATCHED]

    async def save(self, shipment: Shipment) -> None:
        self._items[shipment.id] = shipment

    async def get_by_order(self, order_id: int) -> Shipment | None:
        for s in self._items.values():
            if s.order_id == order_id:
                return s
        return None


class FakeNotificationRepo(NotificationRepository):
    def __init__(self) -> None:
        self.saved: list[Notification] = []
        self._next = 1

    async def save(self, notification: Notification) -> None:
        for i, existing in enumerate(self.saved):
            if existing.id == notification.id:
                self.saved[i] = notification
                return
        self.saved.append(notification)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return next((n for n in self.saved if n.id == notification_id), None)

    async def next_id(self) -> int:
        value = self._next
        self._next += 1
        return value

    async def list_recent(self, limit: int = 20) -> list[Notification]:
        return list(self.saved[-limit:])


class CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


@pytest.fixture
def configured_registry():
    product_repo = FakeProductRepo(
        [Product(id=1, name="Domates", stock=5), Product(id=2, name="Salatalık", stock=120)]
    )
    notif_service = NotificationService(
        repository=FakeNotificationRepo(),
        notifier=CollectingNotifier(),
        clock=lambda: _dt(2026, 5, 11, 8, 0),
    )
    stock = StockService(
        products=product_repo,
        thresholds=FakeThresholdRepo(),
        notifications=notif_service,
        supplier_recipient="@tedarik",
    )
    orders = OrderService(
        orders=FakeOrderRepo(
            [Order(id=101, customer_name="Ali", created_at=_dt(2026, 5, 11, 9, 0))]
        )
    )
    shipment = Shipment(
        id=1,
        order_id=101,
        carrier="Aras",
        tracking_number="TRK-1",
        dispatched_at=_dt(2026, 5, 10, 9, 0),
        expected_delivery_at=_dt(2026, 5, 13, 18, 0),
    )
    shipping = ShippingService(shipments=FakeShipmentRepo([shipment]))

    registry = ToolRegistry()
    register_default_tools(
        registry=registry,
        stock=stock,
        orders=orders,
        shipping=shipping,
        notifications=notif_service,
    )
    return registry


class TestGetProductStockHandler:
    async def test_returns_stock_payload(self, configured_registry):
        handler = configured_registry.get("get_product_stock")
        assert handler is not None

        result = await handler({"product_name": "Domates"})

        assert result.payload == {"id": 1, "name": "Domates", "stock": 5}


class TestListOrdersHandler:
    async def test_returns_orders_payload(self, configured_registry):
        handler = configured_registry.get("list_orders")
        assert handler is not None

        result = await handler({})

        assert "orders" in (result.payload or {})


class TestGetShipmentStatusHandler:
    async def test_returns_shipment_payload(self, configured_registry):
        handler = configured_registry.get("get_shipment_status")
        assert handler is not None

        result = await handler({"order_id": 101})

        assert (result.payload or {}).get("order_id") == 101


class TestCreateReorderDraftHandler:
    async def test_creates_supplier_notification(self, configured_registry):
        handler = configured_registry.get("create_reorder_draft")
        assert handler is not None

        result = await handler({"product_id": 1, "quantity": 50})

        assert result.is_error is False
        assert (result.payload or {}).get("status") == "sent"


class TestRegistryListsAllEightTools:
    def test_eight_tools_registered(self, configured_registry):
        names = set(configured_registry.names())

        assert names == {
            "get_product_stock",
            "list_low_stock_products",
            "get_order_status",
            "list_orders",
            "get_shipment_status",
            "list_delayed_shipments",
            "notify_customer",
            "create_reorder_draft",
        }
