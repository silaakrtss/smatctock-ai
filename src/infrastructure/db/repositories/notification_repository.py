from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.notification_repository import NotificationRepository
from src.domain.notifications.notification import Notification
from src.infrastructure.db.tables import notifications_table


@dataclass
class SqlAlchemyNotificationRepository(NotificationRepository):
    session: AsyncSession

    async def save(self, notification: Notification) -> None:
        await self.session.merge(notification)

    async def get_by_id(self, notification_id: int) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(notifications_table.c.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def next_id(self) -> int:
        result = await self.session.execute(select(func.max(notifications_table.c.id)))
        current_max = result.scalar()
        return (current_max or 0) + 1

    async def list_recent(self, limit: int = 20) -> list[Notification]:
        stmt = select(Notification).order_by(notifications_table.c.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
