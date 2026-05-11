from dataclasses import dataclass, field


class InsufficientStockError(Exception):
    pass


class InvalidQuantityError(ValueError):
    pass


@dataclass
class Product:
    id: int
    name: str
    stock: int = field(default=0)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty")
        if self.stock < 0:
            raise ValueError("Product stock cannot be negative")

    def decrement_stock(self, quantity: int) -> None:
        self._require_positive_quantity(quantity)
        if quantity > self.stock:
            raise InsufficientStockError(
                f"Stock {self.stock} insufficient for decrement {quantity}"
            )
        self.stock -= quantity

    def increment_stock(self, quantity: int) -> None:
        self._require_positive_quantity(quantity)
        self.stock += quantity

    def is_below_threshold(self, threshold: int) -> bool:
        return self.stock < threshold

    @staticmethod
    def _require_positive_quantity(quantity: int) -> None:
        if quantity <= 0:
            raise InvalidQuantityError(f"Quantity must be positive, got {quantity}")
