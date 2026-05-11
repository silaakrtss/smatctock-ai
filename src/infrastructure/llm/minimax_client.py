import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from src.application.ports.llm_client import (
    ChatMessage,
    LLMClient,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)
from src.application.ports.llm_errors import (
    LLMRateLimitError,
    LLMResponseShapeError,
    LLMTransportError,
)

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_SECONDS = 0.5


@dataclass
class MiniMaxLLMClient(LLMClient):
    client: Any
    model: str
    rate_limit_exceptions: tuple[type[BaseException], ...]
    transport_exceptions: tuple[type[BaseException], ...]
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS
    backoff_seconds: float = _DEFAULT_BACKOFF_SECONDS
    _sleep: Any = field(default=asyncio.sleep)

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        completion = await self._call_with_retry(
            payload=_build_request_payload(self.model, messages, tools),
        )
        return _build_response(completion)

    async def _call_with_retry(self, payload: dict[str, Any]) -> Any:
        last_rate_limit: BaseException | None = None
        last_transport: BaseException | None = None
        for attempt in range(self.max_attempts):
            try:
                return await self.client.chat.completions.create(**payload)
            except self.rate_limit_exceptions as exc:
                last_rate_limit = exc
                await self._sleep_for(attempt)
            except self.transport_exceptions as exc:
                last_transport = exc
                await self._sleep_for(attempt)
        if last_rate_limit is not None:
            raise LLMRateLimitError("MiniMax rate limit") from last_rate_limit
        raise LLMTransportError("MiniMax transport error") from last_transport

    async def _sleep_for(self, attempt: int) -> None:
        delay = self.backoff_seconds * (2**attempt)
        if delay > 0:
            await self._sleep(delay)


def _build_request_payload(
    model: str,
    messages: list[ChatMessage],
    tools: list[ToolDefinition],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [_serialize_message(m) for m in messages],
    }
    if tools:
        payload["tools"] = [_serialize_tool(t) for t in tools]
    return payload


def _serialize_message(message: ChatMessage) -> dict[str, Any]:
    raw: dict[str, Any] = {"role": message.role}
    if message.content is not None:
        raw["content"] = message.content
    if message.tool_call_id is not None:
        raw["tool_call_id"] = message.tool_call_id
    if message.tool_calls:
        raw["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in message.tool_calls
        ]
    if message.reasoning_details:
        raw["reasoning_details"] = message.reasoning_details
    return raw


def _serialize_tool(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _build_response(completion: Any) -> LLMResponse:
    choice = _first_choice(completion)
    message = choice.message
    tool_calls = tuple(_parse_tool_call(raw) for raw in getattr(message, "tool_calls", []) or [])
    reasoning = _extract_reasoning_details(completion, message)
    return LLMResponse(
        content=getattr(message, "content", None),
        tool_calls=tool_calls,
        reasoning_details=reasoning,
    )


def _first_choice(completion: Any) -> Any:
    choices = getattr(completion, "choices", None)
    if not choices:
        raise LLMResponseShapeError("MiniMax response has no choices")
    return choices[0]


def _parse_tool_call(raw: Any) -> ToolCall:
    function = raw.function
    try:
        arguments = json.loads(function.arguments)
    except (TypeError, ValueError) as exc:
        raise LLMResponseShapeError(f"Invalid tool arguments JSON: {function.arguments!r}") from exc
    return ToolCall(id=raw.id, name=function.name, arguments=arguments)


def _extract_reasoning_details(completion: Any, message: Any) -> dict[str, Any]:
    raw = getattr(message, "reasoning_details", None)
    if raw is None:
        extra = getattr(completion, "model_extra", None)
        if isinstance(extra, dict):
            raw = extra.get("reasoning_details")
    if raw is None:
        return {}
    return dict(raw)
