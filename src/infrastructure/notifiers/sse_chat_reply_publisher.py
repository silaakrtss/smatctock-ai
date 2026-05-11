from dataclasses import dataclass

from src.application.ports.chat_reply_publisher import ChatReplyPublisher
from src.infrastructure.notifiers.sse_hub import SseHub


@dataclass
class SseChatReplyPublisher(ChatReplyPublisher):
    sse_hub: SseHub

    async def publish(self, *, message_id: str, content: str) -> None:
        await self.sse_hub.publish(
            {
                "type": "chat_reply",
                "message_id": message_id,
                "content": content,
            }
        )
