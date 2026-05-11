import asyncio
from dataclasses import dataclass, field
from typing import Any

from src.application.ports.llm_client import (
    ChatMessage,
    LLMClient,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)
from src.application.ports.llm_errors import LLMRateLimitError, LLMTransportError

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_SECONDS = 0.5


@dataclass
class GeminiLLMClient(LLMClient):
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
        request = _build_request(self.model, messages, tools)
        response = await self._call_with_retry(request)
        return _build_response(response)

    async def _call_with_retry(self, request: dict[str, Any]) -> Any:
        last_rate_limit: BaseException | None = None
        last_transport: BaseException | None = None
        for attempt in range(self.max_attempts):
            try:
                return await self.client.aio.models.generate_content(**request)
            except self.rate_limit_exceptions as exc:
                last_rate_limit = exc
                await self._sleep_for(attempt)
            except self.transport_exceptions as exc:
                last_transport = exc
                await self._sleep_for(attempt)
        if last_rate_limit is not None:
            raise LLMRateLimitError("Gemini rate limit") from last_rate_limit
        raise LLMTransportError("Gemini transport error") from last_transport

    async def _sleep_for(self, attempt: int) -> None:
        delay = self.backoff_seconds * (2**attempt)
        if delay > 0:
            await self._sleep(delay)


def _build_request(
    model: str,
    messages: list[ChatMessage],
    tools: list[ToolDefinition],
) -> dict[str, Any]:
    system_instruction, contents = _split_system_and_contents(messages)
    config: dict[str, Any] = {}
    if system_instruction is not None:
        config["system_instruction"] = system_instruction
    if tools:
        config["tools"] = [
            {"function_declarations": [_serialize_tool(t) for t in tools]},
        ]
    return {"model": model, "contents": contents, "config": config}


def _split_system_and_contents(
    messages: list[ChatMessage],
) -> tuple[str | None, list[dict[str, Any]]]:
    system_chunks: list[str] = []
    contents: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "system" and message.content:
            system_chunks.append(message.content)
            continue
        contents.append(_serialize_message(message))
    system_instruction = "\n\n".join(system_chunks) if system_chunks else None
    return system_instruction, contents


def _serialize_message(message: ChatMessage) -> dict[str, Any]:
    role = "model" if message.role == "assistant" else message.role
    parts: list[dict[str, Any]] = []
    if message.content is not None:
        parts.append({"text": message.content})
    for tool_call in message.tool_calls:
        parts.append({"function_call": {"name": tool_call.name, "args": tool_call.arguments}})
    return {"role": role, "parts": parts}


def _serialize_tool(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }


def _build_response(response: Any) -> LLMResponse:
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(candidate.content, "parts", []) or []:
            text = getattr(part, "text", None)
            if text:
                text_parts.append(text)
            function_call = getattr(part, "function_call", None)
            if function_call is not None:
                tool_calls.append(_parse_function_call(function_call))
    content = "".join(text_parts) if text_parts else None
    return LLMResponse(content=content, tool_calls=tuple(tool_calls), reasoning_details={})


def _parse_function_call(function_call: Any) -> ToolCall:
    call_id = getattr(function_call, "id", None) or f"gemini-{function_call.name}"
    args = dict(function_call.args) if function_call.args else {}
    return ToolCall(id=call_id, name=function_call.name, arguments=args)
