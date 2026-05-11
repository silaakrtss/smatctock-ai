from dataclasses import dataclass
from typing import Any

import pytest
from src.agent.loop import AgentLoop, AgentLoopExceededError
from src.agent.tools.dispatcher import ToolDispatcher
from src.agent.tools.registry import ToolRegistry
from src.agent.tools.tool_result import ToolResult
from src.application.ports.llm_client import (
    ChatMessage,
    LLMClient,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)


@dataclass
class _ScriptedLLM(LLMClient):
    responses: list[LLMResponse]
    requests: list[list[ChatMessage]]

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.requests.append(list(messages))
        if not self.responses:
            raise AssertionError("LLM ran out of scripted responses")
        return self.responses.pop(0)


def _llm(responses: list[LLMResponse]) -> _ScriptedLLM:
    return _ScriptedLLM(responses=list(responses), requests=[])


def _dispatcher(handler_payload: dict[str, Any]) -> ToolDispatcher:
    registry = ToolRegistry()

    async def _handler(args: dict[str, Any]) -> ToolResult:
        return ToolResult.success({"echo": args, **handler_payload})

    registry.register("get_stock", _handler)
    return ToolDispatcher(
        registry=registry,
        definitions=[
            ToolDefinition(
                name="get_stock",
                description="x",
                parameters={"type": "object", "properties": {}, "required": []},
            )
        ],
    )


class TestSingleTurnNoTools:
    async def test_returns_response_immediately(self):
        llm = _llm([LLMResponse(content="Merhaba", tool_calls=())])
        loop = AgentLoop(llm_client=llm, dispatcher=_dispatcher({}))

        result = await loop.run(
            messages=[ChatMessage(role="user", content="Selam")],
            tools=[],
            system_prompt="x",
        )

        assert result.content == "Merhaba"
        assert len(llm.requests) == 1


class TestToolCallRound:
    async def test_executes_tool_and_loops_to_final_answer(self):
        tool_call_response = LLMResponse(
            content=None,
            tool_calls=(ToolCall(id="c1", name="get_stock", arguments={"name": "Domates"}),),
            reasoning_details={"step": 1},
        )
        final_response = LLMResponse(content="Stok 40 adet.", tool_calls=())
        llm = _llm([tool_call_response, final_response])
        loop = AgentLoop(llm_client=llm, dispatcher=_dispatcher({"stock": 40}))

        result = await loop.run(
            messages=[ChatMessage(role="user", content="Domates stoğu?")],
            tools=[],
            system_prompt="x",
        )

        assert result.content == "Stok 40 adet."
        assert len(llm.requests) == 2
        second_request = llm.requests[1]
        # Reasoning details + tool result mesaj geçmişinde KORUNUR
        assistant_msg = next(m for m in second_request if m.role == "assistant")
        assert assistant_msg.reasoning_details == {"step": 1}
        tool_msg = next(m for m in second_request if m.role == "tool")
        assert "40" in (tool_msg.content or "")


class TestMaxIterations:
    async def test_raises_when_loop_exceeds_limit(self):
        infinite_tool_response = LLMResponse(
            content=None,
            tool_calls=(ToolCall(id="cN", name="get_stock", arguments={}),),
        )
        llm = _llm([infinite_tool_response] * 8)
        loop = AgentLoop(
            llm_client=llm,
            dispatcher=_dispatcher({}),
            max_iterations=3,
        )

        with pytest.raises(AgentLoopExceededError):
            await loop.run(
                messages=[ChatMessage(role="user", content="x")],
                tools=[],
                system_prompt="x",
            )

        assert len(llm.requests) == 3
