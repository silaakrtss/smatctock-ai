from dataclasses import dataclass, field

from src.agent.tools.tool_result import ToolResult
from src.application.ports.llm_client import ChatMessage, LLMResponse


@dataclass
class Conversation:
    system_prompt: str
    messages: list[ChatMessage] = field(default_factory=list)

    def append_user(self, content: str) -> None:
        self.messages.append(ChatMessage(role="user", content=content))

    def append_assistant(self, response: LLMResponse) -> None:
        self.messages.append(
            ChatMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
                reasoning_details=response.reasoning_details,
            )
        )

    def append_tool_result(self, tool_call_id: str, result: ToolResult) -> None:
        self.messages.append(
            ChatMessage(
                role="tool",
                content=result.to_model_string(),
                tool_call_id=tool_call_id,
            )
        )

    def as_provider_messages(self) -> list[ChatMessage]:
        return [ChatMessage(role="system", content=self.system_prompt), *self.messages]
