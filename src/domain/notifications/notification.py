from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NotPendingError(Exception):
    pass


class NotFailedError(Exception):
    pass


class NotificationChannel(str, Enum):
    TELEGRAM = "telegram"
    SSE = "sse"
    EMAIL = "email"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class Notification:
    id: int
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    created_at: datetime
    status: NotificationStatus = field(default=NotificationStatus.PENDING)
    sent_at: datetime | None = field(default=None)
    failure_reason: str | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.recipient or not self.recipient.strip():
            raise ValueError("Notification recipient cannot be empty")
        if not self.body or not self.body.strip():
            raise ValueError("Notification body cannot be empty")

    def mark_sent(self, at: datetime) -> None:
        if self.status != NotificationStatus.PENDING:
            raise NotPendingError(
                f"Notification {self.id} is {self.status.value}, cannot mark sent"
            )
        self.status = NotificationStatus.SENT
        self.sent_at = at

    def mark_failed(self, reason: str) -> None:
        if not reason or not reason.strip():
            raise ValueError("Notification failure reason cannot be empty")
        if self.status != NotificationStatus.PENDING:
            raise NotPendingError(
                f"Notification {self.id} is {self.status.value}, cannot mark failed"
            )
        self.status = NotificationStatus.FAILED
        self.failure_reason = reason

    def retry(self) -> None:
        if self.status != NotificationStatus.FAILED:
            raise NotFailedError(f"Notification {self.id} is {self.status.value}, cannot retry")
        self.status = NotificationStatus.PENDING
        self.failure_reason = None
