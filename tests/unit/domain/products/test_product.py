import pytest
from src.domain.products.product import (
    InsufficientStockError,
    InvalidQuantityError,
    Product,
)


class TestProductInvariants:
    def test_creates_product_with_valid_fields(self):
        product = Product(id=1, name="Domates", stock=40)

        assert product.id == 1
        assert product.name == "Domates"
        assert product.stock == 40

    def test_name_cannot_be_empty(self):
        with pytest.raises(ValueError, match="name"):
            Product(id=1, name="", stock=10)

    def test_name_cannot_be_whitespace(self):
        with pytest.raises(ValueError, match="name"):
            Product(id=1, name="   ", stock=10)

    def test_stock_cannot_be_negative(self):
        with pytest.raises(ValueError, match="stock"):
            Product(id=1, name="Domates", stock=-1)


class TestDecrementStock:
    def test_reduces_stock_by_quantity(self):
        product = Product(id=1, name="Domates", stock=40)

        product.decrement_stock(10)

        assert product.stock == 30

    def test_raises_when_quantity_exceeds_stock(self):
        product = Product(id=1, name="Domates", stock=5)

        with pytest.raises(InsufficientStockError):
            product.decrement_stock(10)

    def test_allows_exact_zeroing(self):
        product = Product(id=1, name="Domates", stock=5)

        product.decrement_stock(5)

        assert product.stock == 0

    def test_rejects_non_positive_quantity(self):
        product = Product(id=1, name="Domates", stock=5)

        with pytest.raises(InvalidQuantityError):
            product.decrement_stock(0)
        with pytest.raises(InvalidQuantityError):
            product.decrement_stock(-3)


class TestIncrementStock:
    def test_adds_quantity_to_stock(self):
        product = Product(id=1, name="Domates", stock=10)

        product.increment_stock(15)

        assert product.stock == 25

    def test_rejects_non_positive_quantity(self):
        product = Product(id=1, name="Domates", stock=10)

        with pytest.raises(InvalidQuantityError):
            product.increment_stock(0)
        with pytest.raises(InvalidQuantityError):
            product.increment_stock(-1)


class TestBelowThreshold:
    def test_returns_true_when_stock_below(self):
        product = Product(id=1, name="Domates", stock=5)

        assert product.is_below_threshold(10) is True

    def test_returns_false_when_stock_equal_or_above(self):
        product = Product(id=1, name="Domates", stock=10)

        assert product.is_below_threshold(10) is False
        assert product.is_below_threshold(5) is False
