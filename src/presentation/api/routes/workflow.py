from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.schemas import DailyWorkflowPlanRead, NotificationRead

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/daily-plan", response_model=DailyWorkflowPlanRead)
async def daily_plan(scope: RequestScope = Depends(get_scope)) -> DailyWorkflowPlanRead:
    plan = await scope.workflow.build_daily_plan(_utcnow())
    return DailyWorkflowPlanRead.from_service(plan)


@router.post("/dispatch", response_model=list[NotificationRead])
async def dispatch_daily_plan(
    scope: RequestScope = Depends(get_scope),
) -> list[NotificationRead]:
    notifications = await scope.workflow.dispatch_daily_plan(_utcnow())
    return [NotificationRead.from_domain(notification) for notification in notifications]


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
