from collections.abc import Awaitable, Callable
from typing import Any

from src.agent.tools.tool_result import ToolResult

ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


class DuplicateToolError(Exception):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        if name in self._handlers:
            raise DuplicateToolError(f"Tool already registered: {name}")
        self._handlers[name] = handler

    def get(self, name: str) -> ToolHandler | None:
        return self._handlers.get(name)

    def names(self) -> list[str]:
        return list(self._handlers.keys())
