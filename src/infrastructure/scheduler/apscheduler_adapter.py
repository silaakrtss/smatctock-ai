from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.triggers.cron import CronTrigger as ApsCronTrigger

from src.application.ports.scheduler import CronTrigger, Scheduler


@dataclass
class ApschedulerAdapter(Scheduler):
    scheduler: AsyncScheduler

    async def start(self) -> None:
        await self.scheduler.start_in_background()

    async def stop(self) -> None:
        await self.scheduler.stop()

    async def add_job(
        self,
        func: Callable[[], Awaitable[None]],
        trigger: CronTrigger,
        *,
        job_id: str,
    ) -> None:
        await self.scheduler.add_schedule(
            func_or_task_id=func,
            trigger=_to_aps_trigger(trigger),
            id=job_id,
            conflict_policy=ConflictPolicy.replace,
        )


def _to_aps_trigger(trigger: CronTrigger) -> ApsCronTrigger:
    return ApsCronTrigger(
        minute=trigger.minute,
        hour=trigger.hour,
        day_of_week=trigger.day_of_week,
    )
