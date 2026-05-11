from datetime import datetime, timezone

import pytest
from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.application.ports.product_repository import ProductRepository
from src.application.ports.stock_threshold_repository import StockThresholdRepository
from src.application.services.notification_service import NotificationService
from src.application.services.stock_service import ProductNotFoundError, StockService
from src.domain.notifications.notification import Notification, NotificationChannel
from src.domain.products.product import InsufficientStockError, Product
from src.domain.stock.stock_threshold import StockThreshold


def _dt() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


class _MemoryNotificationRepo(NotificationRepository):
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


class _CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


def _notification_service() -> NotificationService:
    return NotificationService(
        repository=_MemoryNotificationRepo(),
        notifier=_CollectingNotifier(),
        clock=_dt,
    )


class FakeProductRepository(ProductRepository):
    def __init__(self, products: list[Product]) -> None:
        self._items: dict[int, Product] = {p.id: p for p in products}

    async def get_by_id(self, product_id: int) -> Product | None:
        return self._items.get(product_id)

    async def get_by_name(self, name: str) -> Product | None:
        normalized = name.strip().lower()
        for product in self._items.values():
            if product.name.lower() == normalized:
                return product
        return None

    async def list_all(self) -> list[Product]:
        return list(self._items.values())

    async def save(self, product: Product) -> None:
        self._items[product.id] = product

    async def list_below_threshold(self) -> list[Product]:
        raise NotImplementedError


class FakeThresholdRepository(StockThresholdRepository):
    def __init__(self, thresholds: list[StockThreshold]) -> None:
        self._by_product: dict[int, StockThreshold] = {t.product_id: t for t in thresholds}

    async def get_for_product(self, product_id: int) -> StockThreshold | None:
        return self._by_product.get(product_id)

    async def list_all(self) -> list[StockThreshold]:
        return list(self._by_product.values())


class TestFindBelowThreshold:
    async def test_returns_only_products_below_their_threshold(self):
        products = [
            Product(id=1, name="Domates", stock=5),
            Product(id=2, name="Salatalık", stock=120),
            Product(id=3, name="Patates", stock=10),
        ]
        thresholds = [
            StockThreshold(product_id=1, min_quantity=10),
            StockThreshold(product_id=2, min_quantity=50),
            StockThreshold(product_id=3, min_quantity=20),
        ]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository(thresholds),
        )

        breached = await service.find_below_threshold()

        breached_ids = sorted(p.id for p in breached)
        assert breached_ids == [1, 3]

    async def test_products_without_threshold_are_skipped(self):
        products = [Product(id=1, name="Domates", stock=5)]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
        )

        breached = await service.find_below_threshold()

        assert breached == []


class TestAdjustStock:
    async def test_positive_delta_increments(self):
        products = [Product(id=1, name="Domates", stock=10)]
        repo = FakeProductRepository(products)
        service = StockService(products=repo, thresholds=FakeThresholdRepository([]))

        updated = await service.adjust_stock(product_id=1, delta=5)

        assert updated.stock == 15
        assert (await repo.get_by_id(1)).stock == 15  # type: ignore[union-attr]

    async def test_negative_delta_decrements(self):
        products = [Product(id=1, name="Domates", stock=10)]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
        )

        updated = await service.adjust_stock(product_id=1, delta=-3)

        assert updated.stock == 7

    async def test_insufficient_stock_propagates_domain_error(self):
        products = [Product(id=1, name="Domates", stock=2)]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
        )

        with pytest.raises(InsufficientStockError):
            await service.adjust_stock(product_id=1, delta=-5)

    async def test_unknown_product_raises_application_error(self):
        service = StockService(
            products=FakeProductRepository([]),
            thresholds=FakeThresholdRepository([]),
        )

        with pytest.raises(ProductNotFoundError):
            await service.adjust_stock(product_id=99, delta=1)

    async def test_zero_delta_rejected(self):
        products = [Product(id=1, name="Domates", stock=10)]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
        )

        with pytest.raises(ValueError, match="delta"):
            await service.adjust_stock(product_id=1, delta=0)


class TestGetByName:
    async def test_finds_product_case_insensitively(self):
        products = [Product(id=1, name="Domates", stock=40)]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
        )

        result = await service.get_by_name("domates")

        assert result.id == 1

    async def test_raises_when_unknown(self):
        service = StockService(
            products=FakeProductRepository([]),
            thresholds=FakeThresholdRepository([]),
        )

        with pytest.raises(ProductNotFoundError):
            await service.get_by_name("Patlıcan")


class TestCreateReorderDraft:
    async def test_dispatches_supplier_notification(self):
        products = [Product(id=1, name="Domates", stock=5)]
        notifications = _notification_service()
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
            notifications=notifications,
            supplier_recipient="@tedarik",
        )

        notification = await service.create_reorder_draft(product_id=1, quantity=50)

        assert notification.channel == NotificationChannel.TELEGRAM
        assert notification.recipient == "@tedarik"
        assert "Domates" in notification.body
        assert "50" in notification.body

    async def test_rejects_non_positive_quantity(self):
        products = [Product(id=1, name="Domates", stock=5)]
        service = StockService(
            products=FakeProductRepository(products),
            thresholds=FakeThresholdRepository([]),
            notifications=_notification_service(),
            supplier_recipient="@tedarik",
        )

        with pytest.raises(ValueError, match="quantity"):
            await service.create_reorder_draft(product_id=1, quantity=0)

    async def test_raises_when_product_missing(self):
        service = StockService(
            products=FakeProductRepository([]),
            thresholds=FakeThresholdRepository([]),
            notifications=_notification_service(),
            supplier_recipient="@tedarik",
        )

        with pytest.raises(ProductNotFoundError):
            await service.create_reorder_draft(product_id=99, quantity=10)
