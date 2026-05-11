from abc import ABC, abstractmethod

from src.domain.notifications.notification import Notification


class NotifierError(Exception):
    pass


class Notifier(ABC):
    @abstractmethod
    async def send(self, notification: Notification) -> None: ...
