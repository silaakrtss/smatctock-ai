from abc import ABC, abstractmethod

from src.domain.products.product import Product


class ProductRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product | None: ...

    @abstractmethod
    async def list_all(self) -> list[Product]: ...

    @abstractmethod
    async def save(self, product: Product) -> None: ...

    @abstractmethod
    async def list_below_threshold(self) -> list[Product]: ...
