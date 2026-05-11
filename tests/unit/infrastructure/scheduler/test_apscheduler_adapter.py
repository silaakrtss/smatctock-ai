from dataclasses import dataclass, field
from typing import Any

from apscheduler import ConflictPolicy
from src.application.ports.scheduler import CronTrigger
from src.infrastructure.scheduler.apscheduler_adapter import ApschedulerAdapter


@dataclass
class FakeAsyncScheduler:
    started: bool = False
    stopped: bool = False
    added: list[dict[str, Any]] = field(default_factory=list)

    async def start_in_background(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def add_schedule(self, **kwargs: Any) -> str:
        self.added.append(kwargs)
        return kwargs["id"]


async def _noop() -> None:
    return None


class TestApschedulerAdapter:
    async def test_start_delegates_to_scheduler(self):
        scheduler = FakeAsyncScheduler()
        adapter = ApschedulerAdapter(scheduler=scheduler)  # type: ignore[arg-type]

        await adapter.start()

        assert scheduler.started is True

    async def test_stop_delegates_to_scheduler(self):
        scheduler = FakeAsyncScheduler()
        adapter = ApschedulerAdapter(scheduler=scheduler)  # type: ignore[arg-type]

        await adapter.stop()

        assert scheduler.stopped is True

    async def test_add_job_translates_trigger_and_uses_job_id(self):
        scheduler = FakeAsyncScheduler()
        adapter = ApschedulerAdapter(scheduler=scheduler)  # type: ignore[arg-type]

        await adapter.add_job(
            _noop,
            trigger=CronTrigger(minute="0", hour="8"),
            job_id="morning_briefing",
        )

        assert len(scheduler.added) == 1
        added = scheduler.added[0]
        assert added["id"] == "morning_briefing"
        assert added["func_or_task_id"] is _noop
        assert added["conflict_policy"] is ConflictPolicy.replace
