from dataclasses import dataclass

from src.application.ports.product_repository import ProductRepository
from src.application.ports.stock_threshold_repository import StockThresholdRepository
from src.domain.products.product import Product


class ProductNotFoundError(Exception):
    pass


@dataclass
class StockService:
    products: ProductRepository
    thresholds: StockThresholdRepository

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
