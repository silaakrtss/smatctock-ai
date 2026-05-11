import pytest
from src.agent.tools.registry import DuplicateToolError, ToolRegistry
from src.agent.tools.tool_result import ToolResult


async def _stock_handler(args: dict[str, object]) -> ToolResult:
    return ToolResult.success({"args": args})


class TestToolRegistry:
    def test_registers_and_retrieves_handler(self):
        registry = ToolRegistry()

        registry.register("get_product_stock", _stock_handler)

        assert registry.get("get_product_stock") is _stock_handler

    def test_unknown_name_returns_none(self):
        registry = ToolRegistry()

        assert registry.get("missing") is None

    def test_duplicate_registration_raises(self):
        registry = ToolRegistry()
        registry.register("get_product_stock", _stock_handler)

        with pytest.raises(DuplicateToolError):
            registry.register("get_product_stock", _stock_handler)

    def test_names_lists_registered_tools(self):
        registry = ToolRegistry()
        registry.register("a", _stock_handler)
        registry.register("b", _stock_handler)

        assert set(registry.names()) == {"a", "b"}
