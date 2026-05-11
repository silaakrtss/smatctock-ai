from dataclasses import dataclass


@dataclass(frozen=True)
class StockThreshold:
    product_id: int
    min_quantity: int

    def __post_init__(self) -> None:
        if self.min_quantity < 0:
            raise ValueError("StockThreshold min_quantity cannot be negative")

    def is_breached_by(self, stock: int) -> bool:
        return stock < self.min_quantity
