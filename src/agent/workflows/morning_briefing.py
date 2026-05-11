from dataclasses import dataclass, field

from src.agent.loop import AgentLoop
from src.agent.prompts.loader import PromptLoader
from src.application.ports.llm_client import ToolDefinition
from src.application.services.notification_service import (
    NotificationDraft,
    NotificationService,
)
from src.domain.notifications.notification import Notification, NotificationChannel


@dataclass
class MorningBriefingWorkflow:
    agent_loop: AgentLoop
    prompt_loader: PromptLoader
    notifications: NotificationService
    manager_recipient: str
    manager_channel: NotificationChannel = NotificationChannel.TELEGRAM
    prompt_name: str = "system_morning_briefing"
    tools: list[ToolDefinition] = field(default_factory=list)

    async def run(self) -> Notification:
        system_prompt = self.prompt_loader.load(self.prompt_name)
        response = await self.agent_loop.run(
            messages=[],
            tools=self.tools,
            system_prompt=system_prompt,
        )
        body = response.content or "(brifing içeriği üretilemedi)"
        return await self.notifications.dispatch(
            NotificationDraft(
                channel=self.manager_channel,
                recipient=self.manager_recipient,
                subject="🌅 Sabah Brifingi",
                body=body,
            )
        )
