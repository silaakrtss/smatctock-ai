from dataclasses import dataclass

from src.agent.conversation import Conversation
from src.agent.tools.dispatcher import ToolDispatcher
from src.application.ports.llm_client import (
    ChatMessage,
    LLMClient,
    LLMResponse,
    ToolDefinition,
)

_DEFAULT_MAX_ITERATIONS = 8


class AgentLoopExceededError(Exception):
    def __init__(self, max_iterations: int, last_response: LLMResponse | None) -> None:
        super().__init__(f"Agent loop exceeded {max_iterations} iterations")
        self.max_iterations = max_iterations
        self.last_response = last_response


@dataclass
class AgentLoop:
    llm_client: LLMClient
    dispatcher: ToolDispatcher
    max_iterations: int = _DEFAULT_MAX_ITERATIONS

    async def run(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        conversation = Conversation(system_prompt=system_prompt, messages=list(messages))

        last_response: LLMResponse | None = None
        for _ in range(self.max_iterations):
            response = await self.llm_client.chat(
                messages=conversation.as_provider_messages(),
                tools=tools,
            )
            last_response = response
            conversation.append_assistant(response)

            if not response.tool_calls:
                return response

            await self._execute_tool_calls(conversation, response)

        raise AgentLoopExceededError(
            max_iterations=self.max_iterations,
            last_response=last_response,
        )

    async def _execute_tool_calls(self, conversation: Conversation, response: LLMResponse) -> None:
        for tool_call in response.tool_calls:
            result = await self.dispatcher.execute(tool_call)
            conversation.append_tool_result(tool_call.id, result)
