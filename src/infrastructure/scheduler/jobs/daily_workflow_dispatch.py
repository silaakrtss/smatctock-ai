from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from src.application.services.workflow_service import WorkflowService


@dataclass
class DailyWorkflowJobContext:
    workflow: WorkflowService
    now: Callable[[], datetime]


def build_daily_workflow_dispatch_job(
    context_factory: Callable[[], Awaitable[DailyWorkflowJobContext]],
) -> Callable[[], Awaitable[None]]:
    async def job() -> None:
        context = await context_factory()
        await context.workflow.dispatch_daily_plan(context.now())

    return job
