import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.application.ports.llm_client import ChatMessage, LLMResponse


@dataclass
class JsonlCallLogger:
    directory: Path
    clock: Callable[[], datetime]

    def record(
        self,
        *,
        provider: str,
        model: str,
        request_messages: list[ChatMessage],
        response: LLMResponse,
    ) -> None:
        now = self.clock()
        entry = {
            "timestamp": now.isoformat(),
            "provider": provider,
            "model": model,
            "request": [_serialize_message(m) for m in request_messages],
            "response": _serialize_response(response),
        }
        self._target_file(now).parent.mkdir(parents=True, exist_ok=True)
        with self._target_file(now).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _target_file(self, now: datetime) -> Path:
        return self.directory / f"{now.date().isoformat()}.jsonl"


def _serialize_message(message: ChatMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {"role": message.role}
    if message.content is not None:
        payload["content"] = message.content
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    if message.tool_calls:
        payload["tool_calls"] = [
            {"id": c.id, "name": c.name, "arguments": c.arguments} for c in message.tool_calls
        ]
    if message.reasoning_details:
        payload["reasoning_details"] = message.reasoning_details
    return payload


def _serialize_response(response: LLMResponse) -> dict[str, Any]:
    return {
        "content": response.content,
        "tool_calls": [
            {"id": c.id, "name": c.name, "arguments": c.arguments} for c in response.tool_calls
        ],
        "reasoning_details": response.reasoning_details,
    }
