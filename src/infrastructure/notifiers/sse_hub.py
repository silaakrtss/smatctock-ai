import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SseHub:
    _subscribers: list[asyncio.Queue[dict[str, Any]]] = field(default_factory=list)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            await queue.put(event)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
