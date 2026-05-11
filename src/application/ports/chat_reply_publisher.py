from abc import ABC, abstractmethod


class ChatReplyPublisher(ABC):
    @abstractmethod
    async def publish(self, *, message_id: str, content: str) -> None: ...
