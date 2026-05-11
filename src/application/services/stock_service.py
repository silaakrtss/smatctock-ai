from dataclasses import dataclass, field

from src.application.ports.product_repository import ProductRepository
from src.application.ports.stock_threshold_repository import StockThresholdRepository
from src.application.services.notification_service import (
    NotificationDraft,
    NotificationService,
)
from src.domain.notifications.notification import Notification, NotificationChannel
from src.domain.products.product import Product


class ProductNotFoundError(Exception):
    pass


class SupplierNotConfiguredError(Exception):
    pass


@dataclass
class StockService:
    products: ProductRepository
    thresholds: StockThresholdRepository
    notifications: NotificationService | None = field(default=None)
    supplier_recipient: str | None = field(default=None)

    async def find_below_threshold(self) -> list[Product]:
        all_products = await self.products.list_all()
        breached: list[Product] = []
        for product in all_products:
            threshold = await self.thresholds.get_for_product(product.id)
            if threshold is None:
                continue
            if threshold.is_breached_by(product.stock):
                breached.append(product)
        return breached

    async def get_by_name(self, name: str) -> Product:
        product = await self.products.get_by_name(name)
        if product is None:
            raise ProductNotFoundError(f"Product '{name}' not found")
        return product

    async def adjust_stock(self, product_id: int, delta: int) -> Product:
        if delta == 0:
            raise ValueError("delta must be non-zero")

        product = await self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")

        if delta > 0:
            product.increment_stock(delta)
        else:
            product.decrement_stock(-delta)

        await self.products.save(product)
        return product

    async def create_reorder_draft(self, product_id: int, quantity: int) -> Notification:
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        product = await self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")

        if self.notifications is None or self.supplier_recipient is None:
            raise SupplierNotConfiguredError(
                "StockService requires NotificationService and supplier_recipient "
                "for reorder drafts"
            )

        draft = NotificationDraft(
            channel=NotificationChannel.TELEGRAM,
            recipient=self.supplier_recipient,
            subject=f"Tedarik taslağı: {product.name}",
            body=(
                f"{product.name} için {quantity} adet sipariş hazırlanması "
                f"öneriliyor (güncel stok: {product.stock})."
            ),
        )
        return await self.notifications.dispatch(draft)
