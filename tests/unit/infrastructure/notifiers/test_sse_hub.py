import asyncio

from src.infrastructure.notifiers.sse_hub import SseHub


class TestSseHub:
    async def test_publish_delivers_event_to_all_subscribers(self):
        hub = SseHub()
        queue_a = hub.subscribe()
        queue_b = hub.subscribe()

        await hub.publish({"type": "notification", "id": 1})

        event_a = await asyncio.wait_for(queue_a.get(), timeout=0.1)
        event_b = await asyncio.wait_for(queue_b.get(), timeout=0.1)
        assert event_a == {"type": "notification", "id": 1}
        assert event_b == {"type": "notification", "id": 1}

    async def test_unsubscribe_stops_delivery(self):
        hub = SseHub()
        queue = hub.subscribe()
        hub.unsubscribe(queue)

        await hub.publish({"type": "notification", "id": 1})

        assert queue.qsize() == 0

    def test_subscriber_count_reflects_active_subscriptions(self):
        hub = SseHub()
        queue = hub.subscribe()
        hub.subscribe()

        assert hub.subscriber_count == 2

        hub.unsubscribe(queue)
        assert hub.subscriber_count == 1
