from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.application.ports.llm_client import LLMResponse
from src.presentation.api.dependencies import get_scope
from src.presentation.main import app


class StubAgentLoop:
    def __init__(self, answer: str) -> None:
        self._answer = answer

    async def run(self, **_: object) -> LLMResponse:
        return LLMResponse(content=self._answer, tool_calls=[])


class StubPromptLoader:
    def load(self, name: str) -> str:
        return "stub system prompt"


@pytest.fixture
def stub_scope():
    publisher = SimpleNamespace(publish=AsyncMock())
    scope = SimpleNamespace(
        agent_loop=StubAgentLoop("Domates stoğu 8 adet."),
        prompt_loader=StubPromptLoader(),
        chat_reply_publisher=publisher,
    )

    async def override():
        yield scope

    app.dependency_overrides[get_scope] = override
    try:
        yield scope, publisher
    finally:
        app.dependency_overrides.pop(get_scope, None)


def test_ai_chat_publishes_reply_to_sse_when_message_id_given(stub_scope):
    _scope, publisher = stub_scope
    client = TestClient(app)

    response = client.post(
        "/ai-chat",
        json={"message": "Domates stoğu?", "message_id": "abc-123"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Domates stoğu 8 adet."
    publisher.publish.assert_awaited_once_with(
        message_id="abc-123", content="Domates stoğu 8 adet."
    )


def test_ai_chat_skips_publish_when_no_message_id(stub_scope):
    _scope, publisher = stub_scope
    client = TestClient(app)

    response = client.post("/ai-chat", json={"message": "Domates stoğu?"})

    assert response.status_code == 200
    publisher.publish.assert_not_awaited()
