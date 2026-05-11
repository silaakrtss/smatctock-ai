from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest
from src.application.ports.notifier import NotifierError
from src.domain.notifications.notification import Notification, NotificationChannel
from src.infrastructure.notifiers.telegram_notifier import TelegramNotifier


def _dt() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


@dataclass
class FakeResponse:
    status_code: int
    text: str = ""


@dataclass
class FakeHttpxClient:
    responses: list[FakeResponse] = field(default_factory=list)
    exceptions: list[Exception] = field(default_factory=list)
    posts: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    async def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
        self.posts.append((url, json))
        if self.exceptions:
            raise self.exceptions.pop(0)
        return self.responses.pop(0)


def _notification(subject: str = "Stok uyarısı: Domates") -> Notification:
    return Notification(
        id=1,
        channel=NotificationChannel.TELEGRAM,
        recipient="@manager",
        subject=subject,
        body="Stok eşik altında.",
        created_at=_dt(),
    )


def _notifier(client: FakeHttpxClient, *, token: str = "T", chat_id: str = "1") -> TelegramNotifier:
    return TelegramNotifier(
        client=client,
        bot_token=token,
        chat_id=chat_id,
        max_attempts=3,
        backoff_seconds=0.0,
    )


class TestTelegramNotifier:
    async def test_posts_message_with_markdown_format(self):
        client = FakeHttpxClient(responses=[FakeResponse(status_code=200)])
        notifier = _notifier(client)

        await notifier.send(_notification())

        assert len(client.posts) == 1
        url, payload = client.posts[0]
        assert "bot" in url
        assert "sendMessage" in url
        assert payload["chat_id"] == "1"
        assert payload["parse_mode"] == "MarkdownV2"
        assert "🔴" in payload["text"]

    async def test_noop_when_token_missing(self):
        client = FakeHttpxClient()
        notifier = _notifier(client, token="", chat_id="1")

        await notifier.send(_notification())

        assert client.posts == []

    async def test_noop_when_chat_id_missing(self):
        client = FakeHttpxClient()
        notifier = _notifier(client, token="T", chat_id="")

        await notifier.send(_notification())

        assert client.posts == []

    async def test_retries_on_5xx_then_raises_notifier_error(self):
        client = FakeHttpxClient(
            responses=[
                FakeResponse(status_code=500),
                FakeResponse(status_code=500),
                FakeResponse(status_code=500),
            ]
        )
        notifier = _notifier(client)

        with pytest.raises(NotifierError):
            await notifier.send(_notification())

        assert len(client.posts) == 3

    async def test_recovers_after_one_transient_5xx(self):
        client = FakeHttpxClient(
            responses=[FakeResponse(status_code=500), FakeResponse(status_code=200)]
        )
        notifier = _notifier(client)

        await notifier.send(_notification())

        assert len(client.posts) == 2

    async def test_escapes_markdown_special_chars(self):
        client = FakeHttpxClient(responses=[FakeResponse(status_code=200)])
        notifier = _notifier(client)

        await notifier.send(_notification(subject="Sipariş 101 (acil)"))

        text = client.posts[0][1]["text"]
        assert "\\(" in text
        assert "\\)" in text
