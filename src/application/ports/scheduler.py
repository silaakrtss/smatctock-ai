from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CronTrigger:
    minute: str = "0"
    hour: str = "*"
    day_of_week: str = "*"


class Scheduler(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    def add_job(
        self,
        func: Callable[[], Awaitable[None]],
        trigger: CronTrigger,
        *,
        job_id: str,
    ) -> None: ...
