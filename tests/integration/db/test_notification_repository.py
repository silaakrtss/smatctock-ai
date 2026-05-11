from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from src.infrastructure.db.repositories.notification_repository import (
    SqlAlchemyNotificationRepository,
)

pytestmark = pytest.mark.integration


def _dt(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _pending(repo_id: int) -> Notification:
    return Notification(
        id=repo_id,
        channel=NotificationChannel.TELEGRAM,
        recipient="@operator",
        subject="x",
        body="y",
        created_at=_dt(2026, 5, 11, 8, 0),
    )


async def test_save_and_get_by_id_roundtrip(session: AsyncSession):
    repo = SqlAlchemyNotificationRepository(session)
    notification = _pending(1)

    await repo.save(notification)
    await session.commit()

    fetched = await repo.get_by_id(1)
    assert fetched is not None
    assert fetched.channel == NotificationChannel.TELEGRAM
    assert fetched.status == NotificationStatus.PENDING


async def test_failed_status_and_reason_persist(session: AsyncSession):
    repo = SqlAlchemyNotificationRepository(session)
    notification = _pending(1)
    notification.mark_failed("transport")

    await repo.save(notification)
    await session.commit()

    fetched = await repo.get_by_id(1)
    assert fetched is not None
    assert fetched.status == NotificationStatus.FAILED
    assert fetched.failure_reason == "transport"


async def test_next_id_increments_from_max(session: AsyncSession):
    repo = SqlAlchemyNotificationRepository(session)
    assert await repo.next_id() == 1

    await repo.save(_pending(5))
    await session.commit()

    assert await repo.next_id() == 6
