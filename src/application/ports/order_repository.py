from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.orders.order import Order


class OrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None: ...

    @abstractmethod
    async def list_all(self) -> list[Order]: ...

    @abstractmethod
    async def save(self, order: Order) -> None: ...

    @abstractmethod
    async def list_pending_on(self, day: datetime) -> list[Order]: ...

    @abstractmethod
    async def list_filtered(
        self,
        *,
        status: str | None = None,
        day: datetime | None = None,
        customer_name: str | None = None,
    ) -> list[Order]: ...
