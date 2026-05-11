import pytest
from src.domain.stock.stock_threshold import StockThreshold


class TestStockThreshold:
    def test_creates_threshold_with_min_quantity(self):
        threshold = StockThreshold(product_id=1, min_quantity=10)

        assert threshold.product_id == 1
        assert threshold.min_quantity == 10

    def test_rejects_negative_min_quantity(self):
        with pytest.raises(ValueError, match="min_quantity"):
            StockThreshold(product_id=1, min_quantity=-1)

    def test_zero_min_quantity_allowed(self):
        threshold = StockThreshold(product_id=1, min_quantity=0)

        assert threshold.is_breached_by(0) is False

    def test_is_breached_when_stock_below(self):
        threshold = StockThreshold(product_id=1, min_quantity=10)

        assert threshold.is_breached_by(5) is True

    def test_not_breached_at_or_above_min(self):
        threshold = StockThreshold(product_id=1, min_quantity=10)

        assert threshold.is_breached_by(10) is False
        assert threshold.is_breached_by(15) is False
