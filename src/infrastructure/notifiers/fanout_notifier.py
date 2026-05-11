import asyncio
import logging
from dataclasses import dataclass

from src.application.ports.notifier import Notifier
from src.domain.notifications.notification import Notification

_logger = logging.getLogger(__name__)


@dataclass
class FanoutNotifier(Notifier):
    notifiers: list[Notifier]

    async def send(self, notification: Notification) -> None:
        results = await asyncio.gather(
            *(self._send_safely(notifier, notification) for notifier in self.notifiers),
            return_exceptions=False,
        )
        del results

    async def _send_safely(self, notifier: Notifier, notification: Notification) -> None:
        try:
            await notifier.send(notification)
        except Exception as exc:
            _logger.warning(
                "Fanout: %s failed for notification %s: %s",
                notifier.__class__.__name__,
                notification.id,
                exc,
            )
