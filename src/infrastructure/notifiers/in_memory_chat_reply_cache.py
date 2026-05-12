from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.application.ports.chat_reply_cache import ChatReplyCache


@dataclass
class _CacheEntry:
    content: str
    expires_at: datetime


@dataclass
class InMemoryChatReplyCache(ChatReplyCache):
    ttl_seconds: int
    clock: Callable[[], datetime]
    _entries: dict[str, _CacheEntry] = field(default_factory=dict)

    async def set(self, *, message_id: str, content: str) -> None:
        self._purge_expired()
        expires_at = self.clock() + timedelta(seconds=self.ttl_seconds)
        self._entries[message_id] = _CacheEntry(content=content, expires_at=expires_at)

    async def get(self, message_id: str) -> str | None:
        entry = self._entries.get(message_id)
        if entry is None:
            return None
        if entry.expires_at <= self.clock():
            del self._entries[message_id]
            return None
        return entry.content

    def _purge_expired(self) -> None:
        now = self.clock()
        expired = [mid for mid, entry in self._entries.items() if entry.expires_at <= now]
        for mid in expired:
            del self._entries[mid]
