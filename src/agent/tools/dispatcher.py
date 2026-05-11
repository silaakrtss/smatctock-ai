from dataclasses import dataclass
from typing import Any

from src.agent.tools.registry import ToolRegistry
from src.agent.tools.tool_result import ToolResult
from src.application.ports.llm_client import ToolCall, ToolDefinition


@dataclass
class ToolDispatcher:
    registry: ToolRegistry
    definitions: list[ToolDefinition]

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        handler = self.registry.get(tool_call.name)
        if handler is None:
            return ToolResult.error(f"Bilinmeyen tool: {tool_call.name}")

        validation_error = self._validate_arguments(tool_call.name, tool_call.arguments)
        if validation_error is not None:
            return ToolResult.error(f"Argüman hatası: {validation_error}")

        try:
            return await handler(tool_call.arguments)
        except Exception as exc:
            return ToolResult.error(f"Tool yürütme hatası: {exc}")

    def _validate_arguments(self, name: str, arguments: dict[str, Any]) -> str | None:
        schema = self._schema_for(name)
        if schema is None:
            return None
        required = schema.get("required", [])
        missing = [field for field in required if field not in arguments]
        if missing:
            return f"zorunlu alan eksik: {', '.join(missing)}"
        return None

    def _schema_for(self, name: str) -> dict[str, Any] | None:
        for definition in self.definitions:
            if definition.name == name:
                return definition.parameters
        return None
