from collections.abc import Awaitable, Callable

from src.agent.workflows.morning_briefing import MorningBriefingWorkflow


def build_morning_briefing_job(
    workflow_factory: Callable[[], Awaitable[MorningBriefingWorkflow]],
) -> Callable[[], Awaitable[None]]:
    async def job() -> None:
        workflow = await workflow_factory()
        await workflow.run()

    return job
