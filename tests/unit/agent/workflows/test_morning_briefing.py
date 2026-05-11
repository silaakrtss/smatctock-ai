from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.agent.loop import AgentLoop
from src.agent.prompts.loader import PromptLoader
from src.agent.tools.dispatcher import ToolDispatcher
from src.agent.tools.registry import ToolRegistry
from src.agent.workflows.morning_briefing import MorningBriefingWorkflow
from src.application.ports.llm_client import (
    ChatMessage,
    LLMClient,
    LLMResponse,
    ToolDefinition,
)
from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.application.services.notification_service import NotificationService
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)


def _dt() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


@dataclass
class _ScriptedLLM(LLMClient):
    response_text: str
    captured_system_prompts: list[str] = field(default_factory=list)

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        system_messages = [m for m in messages if m.role == "system"]
        if system_messages and system_messages[0].content:
            self.captured_system_prompts.append(system_messages[0].content)
        return LLMResponse(content=self.response_text, tool_calls=())


class _MemoryNotificationRepo(NotificationRepository):
    def __init__(self) -> None:
        self.saved: list[Notification] = []
        self._next = 1

    async def save(self, notification: Notification) -> None:
        for index, existing in enumerate(self.saved):
            if existing.id == notification.id:
                self.saved[index] = notification
                return
        self.saved.append(notification)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return next((n for n in self.saved if n.id == notification_id), None)

    async def next_id(self) -> int:
        value = self._next
        self._next += 1
        return value

    async def list_recent(self, limit: int = 20) -> list[Notification]:
        return list(self.saved[-limit:])


class _CollectingNotifier(Notifier):
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


def _make_workflow(
    tmp_path: Path, response_text: str
) -> tuple[MorningBriefingWorkflow, _ScriptedLLM]:
    (tmp_path / "system_morning_briefing.md").write_text(
        "# Sabah brifingi sistem promptu", encoding="utf-8"
    )
    llm = _ScriptedLLM(response_text=response_text)
    loop = AgentLoop(
        llm_client=llm,
        dispatcher=ToolDispatcher(registry=ToolRegistry(), definitions=[]),
    )
    notifications = NotificationService(
        repository=_MemoryNotificationRepo(),
        notifier=_CollectingNotifier(),
        clock=_dt,
    )
    workflow = MorningBriefingWorkflow(
        agent_loop=loop,
        prompt_loader=PromptLoader(directory=tmp_path),
        notifications=notifications,
        manager_recipient="@manager",
        manager_channel=NotificationChannel.TELEGRAM,
    )
    return workflow, llm


class TestMorningBriefingWorkflow:
    async def test_runs_loop_with_system_prompt_and_dispatches_notification(self, tmp_path: Path):
        workflow, llm = _make_workflow(tmp_path, "🌅 Bugün stok riskleri: yok.")

        notification = await workflow.run()

        assert llm.captured_system_prompts == ["# Sabah brifingi sistem promptu"]
        assert notification.status == NotificationStatus.SENT
        assert notification.recipient == "@manager"
        assert "stok riskleri" in notification.body

    async def test_falls_back_when_llm_returns_empty_content(self, tmp_path: Path):
        workflow, _ = _make_workflow(tmp_path, "")

        notification = await workflow.run()

        assert "brifing" in notification.body.lower()
