from datetime import datetime, timedelta, timezone

from src.infrastructure.notifiers.in_memory_chat_reply_cache import (
    InMemoryChatReplyCache,
)


def _at(seconds: int) -> datetime:
    return datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc) + timedelta(seconds=seconds)


class TestInMemoryChatReplyCache:
    async def test_get_returns_none_when_unknown(self):
        cache = InMemoryChatReplyCache(ttl_seconds=300, clock=lambda: _at(0))

        result = await cache.get("missing")

        assert result is None

    async def test_set_then_get_returns_content_within_ttl(self):
        current = _at(0)
        cache = InMemoryChatReplyCache(ttl_seconds=300, clock=lambda: current)

        await cache.set(message_id="abc", content="Domates stoğu 8.")
        current = _at(299)

        assert await cache.get("abc") == "Domates stoğu 8."

    async def test_get_returns_none_after_ttl_expires(self):
        current = _at(0)
        cache = InMemoryChatReplyCache(ttl_seconds=300, clock=lambda: current)

        await cache.set(message_id="abc", content="Domates stoğu 8.")
        current = _at(301)

        assert await cache.get("abc") is None
