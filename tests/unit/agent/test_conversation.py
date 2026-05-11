from src.agent.conversation import Conversation
from src.agent.tools.tool_result import ToolResult
from src.application.ports.llm_client import (
    ChatMessage,
    LLMResponse,
    ToolCall,
)


class TestInitialState:
    def test_starts_with_system_and_user_messages(self):
        conversation = Conversation(
            system_prompt="Sen bir asistansın",
            messages=[ChatMessage(role="user", content="Selam")],
        )

        provider_messages = conversation.as_provider_messages()

        assert provider_messages[0].role == "system"
        assert provider_messages[0].content == "Sen bir asistansın"
        assert provider_messages[1].content == "Selam"


class TestAppendAssistant:
    def test_preserves_tool_calls_and_reasoning_details(self):
        conversation = Conversation(system_prompt="x", messages=[])
        response = LLMResponse(
            content=None,
            tool_calls=(ToolCall(id="c1", name="get_stock", arguments={"id": 1}),),
            reasoning_details={"thought_id": "abc", "trace": "..."},
        )

        conversation.append_assistant(response)

        assistant = conversation.as_provider_messages()[-1]
        assert assistant.role == "assistant"
        assert assistant.tool_calls == response.tool_calls
        # ADR-0005 § 5 + ADR-0009 § 2: TRUNCATE YASAK
        assert assistant.reasoning_details == {"thought_id": "abc", "trace": "..."}


class TestAppendToolResult:
    def test_appends_tool_role_with_serialized_payload(self):
        conversation = Conversation(system_prompt="x", messages=[])

        conversation.append_tool_result("c1", ToolResult.success({"stock": 40}))

        tool_message = conversation.as_provider_messages()[-1]
        assert tool_message.role == "tool"
        assert tool_message.tool_call_id == "c1"
        assert tool_message.content is not None
        assert "40" in tool_message.content

    def test_error_result_appended_as_tool_message_with_error_payload(self):
        conversation = Conversation(system_prompt="x", messages=[])

        conversation.append_tool_result("c1", ToolResult.error("yetersiz stok"))

        tool_message = conversation.as_provider_messages()[-1]
        assert tool_message.role == "tool"
        assert "yetersiz stok" in (tool_message.content or "")


class TestMultiTurnSequence:
    def test_full_round_preserves_order_and_no_truncation(self):
        conversation = Conversation(system_prompt="x", messages=[])
        conversation.append_user("Domates stoğu?")
        conversation.append_assistant(
            LLMResponse(
                content=None,
                tool_calls=(ToolCall(id="c1", name="get_stock", arguments={"name": "Domates"}),),
                reasoning_details={"step": 1},
            )
        )
        conversation.append_tool_result("c1", ToolResult.success({"stock": 40}))
        conversation.append_assistant(
            LLMResponse(
                content="Domates stoğu 40 adet.",
                tool_calls=(),
                reasoning_details={"step": 2},
            )
        )

        roles = [m.role for m in conversation.as_provider_messages()]
        assert roles == ["system", "user", "assistant", "tool", "assistant"]
        first_assistant = conversation.as_provider_messages()[2]
        assert first_assistant.reasoning_details == {"step": 1}
