from src.agent.tools.dispatcher import ToolDispatcher
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.tool_result import ToolResult
from src.application.ports.llm_client import ToolCall, ToolDefinition


def _definition(name: str, required: list[str] | None = None) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description="x",
        parameters={
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": required or [],
        },
    )


async def _success_handler(args: dict[str, object]) -> ToolResult:
    return ToolResult.success({"echo": args})


async def _raising_handler(args: dict[str, object]) -> ToolResult:
    raise RuntimeError("boom")


def _dispatcher(
    registry: ToolRegistry,
    definitions: list[ToolDefinition],
) -> ToolDispatcher:
    return ToolDispatcher(registry=registry, definitions=definitions)


class TestUnknownTool:
    async def test_returns_error_result(self):
        dispatcher = _dispatcher(ToolRegistry(), [])

        result = await dispatcher.execute(ToolCall(id="c1", name="missing", arguments={}))

        assert result.is_error is True
        assert "Bilinmeyen" in (result.error_message or "")


class TestArgumentValidation:
    async def test_rejects_missing_required(self):
        registry = ToolRegistry()
        registry.register("get_stock", _success_handler)
        dispatcher = _dispatcher(registry, [_definition("get_stock", required=["id"])])

        result = await dispatcher.execute(ToolCall(id="c1", name="get_stock", arguments={}))

        assert result.is_error is True
        assert "id" in (result.error_message or "")


class TestSuccessfulCall:
    async def test_returns_handler_payload(self):
        registry = ToolRegistry()
        registry.register("get_stock", _success_handler)
        dispatcher = _dispatcher(registry, [_definition("get_stock")])

        result = await dispatcher.execute(ToolCall(id="c1", name="get_stock", arguments={"id": 1}))

        assert result.is_error is False
        assert result.payload == {"echo": {"id": 1}}


class TestHandlerException:
    async def test_wraps_exception_into_error_result(self):
        registry = ToolRegistry()
        registry.register("get_stock", _raising_handler)
        dispatcher = _dispatcher(registry, [_definition("get_stock")])

        result = await dispatcher.execute(ToolCall(id="c1", name="get_stock", arguments={"id": 1}))

        assert result.is_error is True
        assert "boom" in (result.error_message or "")
