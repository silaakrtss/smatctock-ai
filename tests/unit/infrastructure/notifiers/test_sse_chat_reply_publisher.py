import asyncio

from src.infrastructure.notifiers.sse_chat_reply_publisher import (
    SseChatReplyPublisher,
)
from src.infrastructure.notifiers.sse_hub import SseHub


class TestSseChatReplyPublisher:
    async def test_publishes_chat_reply_event_with_type_and_payload(self):
        hub = SseHub()
        subscriber = hub.subscribe()
        publisher = SseChatReplyPublisher(sse_hub=hub)

        await publisher.publish(message_id="abc-123", content="Domates stoğu 8 adet.")

        event = await asyncio.wait_for(subscriber.get(), timeout=0.1)
        assert event == {
            "type": "chat_reply",
            "message_id": "abc-123",
            "content": "Domates stoğu 8 adet.",
        }
