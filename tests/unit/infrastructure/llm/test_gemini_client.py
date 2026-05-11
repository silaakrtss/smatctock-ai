from dataclasses import dataclass
from typing import Any

import pytest
from src.application.ports.llm_client import ChatMessage, ToolDefinition
from src.application.ports.llm_errors import LLMRateLimitError, LLMTransportError
from src.infrastructure.llm.gemini_client import GeminiLLMClient


@dataclass
class FakeFunctionCall:
    name: str
    args: dict[str, Any]
    id: str | None = None


@dataclass
class FakePart:
    text: str | None = None
    function_call: FakeFunctionCall | None = None


@dataclass
class FakeContent:
    parts: list[FakePart]


@dataclass
class FakeCandidate:
    content: FakeContent


@dataclass
class FakeGenerationResponse:
    candidates: list[FakeCandidate]
    text: str | None = None


class FakeAsyncModels:
    def __init__(
        self,
        *,
        responses: list[FakeGenerationResponse] | None = None,
        exceptions: list[Exception] | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._exceptions = list(exceptions or [])
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, **kwargs: Any) -> FakeGenerationResponse:
        self.calls.append(kwargs)
        if self._exceptions:
            raise self._exceptions.pop(0)
        return self._responses.pop(0)


@dataclass
class FakeAio:
    models: FakeAsyncModels


@dataclass
class FakeGenAIClient:
    aio: FakeAio


class FakeRateLimitError(Exception):
    pass


class FakeTransportError(Exception):
    pass


def _client(models: FakeAsyncModels) -> GeminiLLMClient:
    return GeminiLLMClient(
        client=FakeGenAIClient(aio=FakeAio(models=models)),
        model="gemini-2.0-flash",
        rate_limit_exceptions=(FakeRateLimitError,),
        transport_exceptions=(FakeTransportError,),
        max_attempts=3,
        backoff_seconds=0.0,
    )


def _text_response(text: str) -> FakeGenerationResponse:
    return FakeGenerationResponse(
        candidates=[FakeCandidate(content=FakeContent(parts=[FakePart(text=text)]))],
        text=text,
    )


class TestChatBasicResponse:
    async def test_returns_assistant_text_and_empty_reasoning(self):
        models = FakeAsyncModels(responses=[_text_response("Merhaba")])
        client = _client(models)

        response = await client.chat(
            messages=[ChatMessage(role="user", content="Selam")],
            tools=[],
        )

        assert response.content == "Merhaba"
        assert response.tool_calls == ()
        assert response.reasoning_details == {}

    async def test_translates_system_message_to_system_instruction(self):
        models = FakeAsyncModels(responses=[_text_response("ok")])
        client = _client(models)

        await client.chat(
            messages=[
                ChatMessage(role="system", content="Türkçe yanıt ver"),
                ChatMessage(role="user", content="Selam"),
            ],
            tools=[],
        )

        sent = models.calls[0]
        assert sent["model"] == "gemini-2.0-flash"
        config = sent["config"]
        assert config["system_instruction"] == "Türkçe yanıt ver"
        assert sent["contents"][0]["role"] == "user"
        assert sent["contents"][0]["parts"][0]["text"] == "Selam"

    async def test_maps_tool_definition_to_function_declaration(self):
        models = FakeAsyncModels(responses=[_text_response("ok")])
        client = _client(models)
        tools = [
            ToolDefinition(
                name="get_stock",
                description="Stok",
                parameters={"type": "object", "properties": {}},
            )
        ]

        await client.chat(messages=[ChatMessage(role="user", content="x")], tools=tools)

        config = models.calls[0]["config"]
        function = config["tools"][0]["function_declarations"][0]
        assert function["name"] == "get_stock"


class TestToolCallParsing:
    async def test_extracts_tool_call_from_part(self):
        response = FakeGenerationResponse(
            candidates=[
                FakeCandidate(
                    content=FakeContent(
                        parts=[
                            FakePart(
                                function_call=FakeFunctionCall(name="get_stock", args={"id": 1})
                            )
                        ]
                    )
                )
            ]
        )
        client = _client(FakeAsyncModels(responses=[response]))

        result = await client.chat(messages=[], tools=[])

        assert len(result.tool_calls) == 1
        call = result.tool_calls[0]
        assert call.name == "get_stock"
        assert call.arguments == {"id": 1}


class TestErrorMapping:
    async def test_rate_limit_after_max_attempts_raises_port_error(self):
        models = FakeAsyncModels(
            exceptions=[FakeRateLimitError(), FakeRateLimitError(), FakeRateLimitError()],
        )
        client = _client(models)

        with pytest.raises(LLMRateLimitError):
            await client.chat(messages=[], tools=[])

        assert len(models.calls) == 3

    async def test_transport_error_maps_to_port_transport(self):
        models = FakeAsyncModels(
            exceptions=[FakeTransportError(), FakeTransportError(), FakeTransportError()],
        )
        client = _client(models)

        with pytest.raises(LLMTransportError):
            await client.chat(messages=[], tools=[])
