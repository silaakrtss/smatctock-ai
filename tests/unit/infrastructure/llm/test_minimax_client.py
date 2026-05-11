from dataclasses import dataclass, field
from typing import Any

import pytest
from src.application.ports.llm_client import ChatMessage, ToolDefinition
from src.application.ports.llm_errors import LLMRateLimitError, LLMTransportError
from src.infrastructure.llm.minimax_client import MiniMaxLLMClient


@dataclass
class FakeMessage:
    content: str | None = None
    tool_calls: list[Any] = field(default_factory=list)


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]
    model_extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCallObject:
    id: str
    function: FakeFunction


class FakeCompletions:
    def __init__(
        self,
        *,
        responses: list[Any] | None = None,
        exceptions: list[Exception] | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._exceptions = list(exceptions or [])
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self._exceptions:
            raise self._exceptions.pop(0)
        return self._responses.pop(0)


class FakeChat:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions = completions


class FakeOpenAI:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = FakeChat(completions)


class FakeRateLimitError(Exception):
    pass


class FakeAPITimeoutError(Exception):
    pass


def _client(completions: FakeCompletions) -> MiniMaxLLMClient:
    return MiniMaxLLMClient(
        client=FakeOpenAI(completions),
        model="MiniMax-M2.7",
        rate_limit_exceptions=(FakeRateLimitError,),
        transport_exceptions=(FakeAPITimeoutError,),
        max_attempts=3,
        backoff_seconds=0.0,
    )


def _completion_with_text(text: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(message=FakeMessage(content=text))])


class TestChatBasicResponse:
    async def test_returns_assistant_text(self):
        completions = FakeCompletions(responses=[_completion_with_text("Merhaba")])
        client = _client(completions)

        response = await client.chat(
            messages=[ChatMessage(role="user", content="Selam")],
            tools=[],
        )

        assert response.content == "Merhaba"
        assert response.tool_calls == ()

    async def test_forwards_messages_and_tools_in_openai_format(self):
        completions = FakeCompletions(responses=[_completion_with_text("ok")])
        client = _client(completions)
        tools = [
            ToolDefinition(
                name="get_stock",
                description="Stok döner",
                parameters={"type": "object", "properties": {"id": {"type": "integer"}}},
            )
        ]

        await client.chat(
            messages=[
                ChatMessage(role="system", content="prompt"),
                ChatMessage(role="user", content="Domates stoğu?"),
            ],
            tools=tools,
        )

        sent = completions.calls[0]
        assert sent["model"] == "MiniMax-M2.7"
        assert sent["messages"] == [
            {"role": "system", "content": "prompt"},
            {"role": "user", "content": "Domates stoğu?"},
        ]
        assert sent["tools"][0]["function"]["name"] == "get_stock"


class TestToolCallParsing:
    async def test_extracts_tool_calls_from_response(self):
        completion = FakeCompletion(
            choices=[
                FakeChoice(
                    message=FakeMessage(
                        content=None,
                        tool_calls=[
                            FakeToolCallObject(
                                id="call_1",
                                function=FakeFunction(name="get_stock", arguments='{"id": 1}'),
                            )
                        ],
                    )
                )
            ]
        )
        client = _client(FakeCompletions(responses=[completion]))

        response = await client.chat(messages=[], tools=[])

        assert len(response.tool_calls) == 1
        call = response.tool_calls[0]
        assert call.id == "call_1"
        assert call.name == "get_stock"
        assert call.arguments == {"id": 1}


class TestErrorMapping:
    async def test_rate_limit_after_max_attempts_raises_port_error(self):
        completions = FakeCompletions(
            exceptions=[FakeRateLimitError(), FakeRateLimitError(), FakeRateLimitError()],
        )
        client = _client(completions)

        with pytest.raises(LLMRateLimitError):
            await client.chat(messages=[], tools=[])

        assert len(completions.calls) == 3

    async def test_recovers_after_one_transient_rate_limit(self):
        completions = FakeCompletions(
            responses=[_completion_with_text("ok")],
            exceptions=[FakeRateLimitError()],
        )
        client = _client(completions)

        response = await client.chat(messages=[], tools=[])

        assert response.content == "ok"
        assert len(completions.calls) == 2

    async def test_transport_error_maps_to_port_transport(self):
        completions = FakeCompletions(
            exceptions=[FakeAPITimeoutError(), FakeAPITimeoutError(), FakeAPITimeoutError()],
        )
        client = _client(completions)

        with pytest.raises(LLMTransportError):
            await client.chat(messages=[], tools=[])
