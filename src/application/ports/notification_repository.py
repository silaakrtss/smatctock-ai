from abc import ABC, abstractmethod

from src.domain.notifications.notification import Notification


class NotificationRepository(ABC):
    @abstractmethod
    async def save(self, notification: Notification) -> None: ...

    @abstractmethod
    async def get_by_id(self, notification_id: int) -> Notification | None: ...

    @abstractmethod
    async def next_id(self) -> int: ...

    @abstractmethod
    async def list_recent(self, limit: int = 20) -> list[Notification]: ...
