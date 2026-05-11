import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    payload: dict[str, Any] | None
    error_message: str | None

    @classmethod
    def success(cls, payload: dict[str, Any]) -> "ToolResult":
        return cls(payload=payload, error_message=None)

    @classmethod
    def error(cls, message: str) -> "ToolResult":
        return cls(payload=None, error_message=message)

    @property
    def is_error(self) -> bool:
        return self.error_message is not None

    def to_model_string(self) -> str:
        if self.is_error:
            return json.dumps({"error": self.error_message}, ensure_ascii=False)
        return json.dumps(self.payload, ensure_ascii=False)
