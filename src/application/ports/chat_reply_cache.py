from abc import ABC, abstractmethod


class ChatReplyCache(ABC):
    @abstractmethod
    async def set(self, *, message_id: str, content: str) -> None: ...

    @abstractmethod
    async def get(self, message_id: str) -> str | None: ...
