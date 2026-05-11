from datetime import datetime, timezone

import pytest
from src.domain.notifications.notification import (
    NotFailedError,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotPendingError,
)


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class TestNotificationCreation:
    def test_creates_pending_notification(self):
        notification = Notification(
            id=1,
            channel=NotificationChannel.TELEGRAM,
            recipient="@operator",
            subject="Stok uyarısı",
            body="Domates stoku eşik altında.",
            created_at=_dt(2026, 5, 11, 8, 0),
        )

        assert notification.status == NotificationStatus.PENDING
        assert notification.sent_at is None
        assert notification.failure_reason is None

    def test_recipient_cannot_be_empty(self):
        with pytest.raises(ValueError, match="recipient"):
            Notification(
                id=1,
                channel=NotificationChannel.SSE,
                recipient="",
                subject="x",
                body="y",
                created_at=_dt(2026, 5, 11, 8, 0),
            )

    def test_body_cannot_be_empty(self):
        with pytest.raises(ValueError, match="body"):
            Notification(
                id=1,
                channel=NotificationChannel.SSE,
                recipient="@user",
                subject="x",
                body="",
                created_at=_dt(2026, 5, 11, 8, 0),
            )


class TestMarkSent:
    def test_transitions_pending_to_sent(self):
        notification = _pending()

        notification.mark_sent(_dt(2026, 5, 11, 8, 1))

        assert notification.status == NotificationStatus.SENT
        assert notification.sent_at == _dt(2026, 5, 11, 8, 1)

    def test_rejects_when_not_pending(self):
        notification = _pending()
        notification.mark_failed("network")

        with pytest.raises(NotPendingError):
            notification.mark_sent(_dt(2026, 5, 11, 8, 1))


class TestMarkFailed:
    def test_transitions_pending_to_failed_with_reason(self):
        notification = _pending()

        notification.mark_failed("timeout")

        assert notification.status == NotificationStatus.FAILED
        assert notification.failure_reason == "timeout"

    def test_reason_cannot_be_empty(self):
        notification = _pending()

        with pytest.raises(ValueError, match="reason"):
            notification.mark_failed("")


class TestRetry:
    def test_failed_can_be_reset_to_pending(self):
        notification = _pending()
        notification.mark_failed("transient")

        notification.retry()

        assert notification.status == NotificationStatus.PENDING
        assert notification.failure_reason is None

    def test_rejects_retry_when_not_failed(self):
        notification = _pending()

        with pytest.raises(NotFailedError):
            notification.retry()


def _pending() -> Notification:
    return Notification(
        id=1,
        channel=NotificationChannel.TELEGRAM,
        recipient="@op",
        subject="x",
        body="y",
        created_at=_dt(2026, 5, 11, 8, 0),
    )
