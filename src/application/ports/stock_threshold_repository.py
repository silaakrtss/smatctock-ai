from abc import ABC, abstractmethod

from src.domain.stock.stock_threshold import StockThreshold


class StockThresholdRepository(ABC):
    @abstractmethod
    async def get_for_product(self, product_id: int) -> StockThreshold | None: ...

    @abstractmethod
    async def list_all(self) -> list[StockThreshold]: ...

    @abstractmethod
    async def save(self, threshold: StockThreshold) -> None: ...
