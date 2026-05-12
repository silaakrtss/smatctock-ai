from datetime import datetime, timezone

from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.application.ports.product_repository import ProductRepository
from src.application.ports.stock_threshold_repository import StockThresholdRepository
from src.application.services.notification_service import NotificationService
from src.application.services.stock_service import StockService
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
)
from src.domain.products.product import Product
from src.domain.stock.stock_threshold import StockThreshold
from src.infrastructure.scheduler.jobs.check_stock_thresholds import (
    StockThresholdJobContext,
    build_check_stock_thresholds_job,
)


def _dt() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


class _FakeProductRepo(ProductRepository):
    def __init__(self, products: list[Product]) -> None:
        self._items = {p.id: p for p in products}

    async def get_by_id(self, product_id: int) -> Product | None:
        return self._items.get(product_id)

    async def get_by_name(self, name: str) -> Product | None:
        return None

    async def list_all(self) -> list[Product]:
        return list(self._items.values())

    async def save(self, product: Product) -> None:
        self._items[product.id] = product

    async def list_below_threshold(self) -> list[Product]:
        raise NotImplementedError


class _FakeThresholdRepo(StockThresholdRepository):
    def __init__(self, thresholds: list[StockThreshold]) -> None:
        self._by_product = {t.product_id: t for t in thresholds}

    async def get_for_product(self, product_id: int) -> StockThreshold | None:
        return self._by_product.get(product_id)

    async def list_all(self) -> list[StockThreshold]:
        return list(self._by_product.values())

    async def save(self, threshold: StockThreshold) -> None:
        self._by_product[threshold.product_id] = threshold



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

    async def list_recent(self, limit: int = 20) -> list[Notification]:
        return list(self.saved[-limit:])


class _CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


def _make_context() -> tuple[StockThresholdJobContext, _CollectingNotifier]:
    products = _FakeProductRepo(
        [
            Product(id=1, name="Domates", stock=5),
            Product(id=2, name="Salatalık", stock=120),
            Product(id=3, name="Patates", stock=10),
        ]
    )
    thresholds = _FakeThresholdRepo(
        [
            StockThreshold(product_id=1, min_quantity=20),
            StockThreshold(product_id=2, min_quantity=50),
            StockThreshold(product_id=3, min_quantity=25),
        ]
    )
    notifier = _CollectingNotifier()
    notifications = NotificationService(
        repository=_FakeNotificationRepo(),
        notifier=notifier,
        clock=_dt,
    )
    context = StockThresholdJobContext(
        stock=StockService(products=products, thresholds=thresholds),
        notifications=notifications,
        manager_recipient="@manager",
        manager_channel=NotificationChannel.TELEGRAM,
    )
    return context, notifier


class TestCheckStockThresholdsJob:
    async def test_sends_alert_only_for_breached_products(self):
        context, notifier = _make_context()
        job = build_check_stock_thresholds_job(_async_returning(context))

        await job()

        assert len(notifier.sent) == 2
        product_names_in_subjects = {n.subject for n in notifier.sent}
        assert any("Domates" in subject for subject in product_names_in_subjects)
        assert any("Patates" in subject for subject in product_names_in_subjects)

    async def test_no_alerts_when_all_products_above_threshold(self):
        context, notifier = _make_context()
        # Stoğu artırarak hiçbirinin eşik altında olmadığı bir senaryo
        for product in await context.stock.products.list_all():
            product.stock = 1000
        job = build_check_stock_thresholds_job(_async_returning(context))

        await job()

        assert notifier.sent == []

    async def test_uses_configured_manager_recipient_and_channel(self):
        context, notifier = _make_context()
        job = build_check_stock_thresholds_job(_async_returning(context))

        await job()

        assert all(n.recipient == "@manager" for n in notifier.sent)
        assert all(n.channel == NotificationChannel.TELEGRAM for n in notifier.sent)


def _async_returning(context: StockThresholdJobContext):
    async def factory() -> StockThresholdJobContext:
        return context

    return factory
