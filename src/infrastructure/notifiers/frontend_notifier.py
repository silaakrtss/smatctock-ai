from dataclasses import dataclass

from src.application.ports.notification_repository import NotificationRepository
from src.application.ports.notifier import Notifier
from src.domain.notifications.notification import Notification
from src.infrastructure.notifiers.sse_hub import SseHub


@dataclass
class FrontendNotifier(Notifier):
    repository: NotificationRepository
    sse_hub: SseHub

    async def send(self, notification: Notification) -> None:
        await self.repository.save(notification)
        await self.sse_hub.publish(_serialize(notification))


def _serialize(notification: Notification) -> dict[str, object]:
    return {
        "id": notification.id,
        "channel": notification.channel.value,
        "recipient": notification.recipient,
        "subject": notification.subject,
        "body": notification.body,
        "created_at": notification.created_at.isoformat(),
        "status": notification.status.value,
    }
