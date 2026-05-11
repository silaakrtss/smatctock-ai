import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from src.application.ports.notifier import Notifier, NotifierError
from src.domain.notifications.notification import Notification

_logger = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_SECONDS = 0.25
_MARKDOWN_V2_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"


@dataclass
class TelegramNotifier(Notifier):
    client: Any
    bot_token: str
    chat_id: str
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS
    backoff_seconds: float = _DEFAULT_BACKOFF_SECONDS
    _sleep: Any = field(default=asyncio.sleep)

    async def send(self, notification: Notification) -> None:
        if not self._is_configured():
            _logger.warning(
                "Telegram disabled: bot_token or chat_id missing (skipping notification %s)",
                notification.id,
            )
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self._format_message(notification),
            "parse_mode": "MarkdownV2",
        }
        await self._post_with_retry(url, payload)

    def _is_configured(self) -> bool:
        return bool(self.bot_token) and bool(self.chat_id)

    def _format_message(self, notification: Notification) -> str:
        emoji = _category_emoji(notification.subject)
        subject = _escape_markdown_v2(notification.subject)
        body = _escape_markdown_v2(notification.body)
        return f"{emoji} *{subject}*\n{body}"

    async def _post_with_retry(self, url: str, payload: dict[str, Any]) -> None:
        last_error: BaseException | None = None
        for attempt in range(self.max_attempts):
            try:
                response = await self.client.post(url, json=payload)
            except Exception as exc:
                last_error = exc
                await self._wait_before_retry(attempt)
                continue

            if _is_success(response):
                return
            last_error = NotifierError(
                f"Telegram HTTP {getattr(response, 'status_code', '?')}: "
                f"{getattr(response, 'text', '')}"
            )
            await self._wait_before_retry(attempt)

        assert last_error is not None
        raise NotifierError("Telegram send failed") from last_error

    async def _wait_before_retry(self, attempt: int) -> None:
        delay = self.backoff_seconds * (3**attempt)
        if delay > 0:
            await self._sleep(delay)


def _is_success(response: Any) -> bool:
    status = getattr(response, "status_code", None)
    return status is not None and 200 <= int(status) < 300


def _escape_markdown_v2(text: str) -> str:
    return "".join(
        f"\\{character}" if character in _MARKDOWN_V2_ESCAPE_CHARS else character
        for character in text
    )


def _category_emoji(subject: str) -> str:
    lowered = subject.lower()
    if "stok" in lowered:
        return "🔴"
    if "kargo" in lowered or "gecik" in lowered:
        return "⚠️"
    if "brifing" in lowered or "sabah" in lowered:
        return "☀️"
    if "sipariş" in lowered:
        return "📦"
    return "📨"
