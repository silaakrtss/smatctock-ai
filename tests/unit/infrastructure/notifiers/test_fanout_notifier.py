from datetime import datetime, timezone

from src.application.ports.notifier import Notifier
from src.domain.notifications.notification import Notification, NotificationChannel
from src.infrastructure.notifiers.fanout_notifier import FanoutNotifier


def _dt() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


class _RecordingNotifier(Notifier):
    def __init__(self, name: str) -> None:
        self.name = name
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        self.sent.append(notification)


class _FailingNotifier(Notifier):
    def __init__(self) -> None:
        self.attempts: int = 0

    async def send(self, notification: Notification) -> None:
        self.attempts += 1
        raise RuntimeError("boom")


def _notification() -> Notification:
    return Notification(
        id=1,
        channel=NotificationChannel.TELEGRAM,
        recipient="@op",
        subject="x",
        body="y",
        created_at=_dt(),
    )


class TestFanoutNotifier:
    async def test_delivers_to_every_notifier(self):
        a = _RecordingNotifier("a")
        b = _RecordingNotifier("b")
        fanout = FanoutNotifier(notifiers=[a, b])

        await fanout.send(_notification())

        assert len(a.sent) == 1
        assert len(b.sent) == 1

    async def test_one_failing_notifier_does_not_block_others(self):
        failing = _FailingNotifier()
        succeeding = _RecordingNotifier("ok")
        fanout = FanoutNotifier(notifiers=[failing, succeeding])

        await fanout.send(_notification())

        assert failing.attempts == 1
        assert len(succeeding.sent) == 1

    async def test_all_failing_does_not_raise(self):
        fanout = FanoutNotifier(notifiers=[_FailingNotifier(), _FailingNotifier()])

        await fanout.send(_notification())
