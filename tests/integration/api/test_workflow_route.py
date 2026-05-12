from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from src.application.services.workflow_service import DailyWorkflowPlan, WorkflowTask
from src.domain.notifications.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from src.presentation.api.dependencies import get_scope
from src.presentation.main import app


class StubWorkflowService:
    def __init__(self) -> None:
        self.dispatched = False

    async def build_daily_plan(self, day: datetime) -> DailyWorkflowPlan:
        return DailyWorkflowPlan(
            day=day,
            packing_tasks=[
                WorkflowTask(
                    id="pack-101",
                    role="warehouse",
                    title="#101 siparişini hazırla",
                    detail="Ali için paketleme yapılacak.",
                    priority="high",
                    related_order_id=101,
                )
            ],
            shipping_tasks=[],
            manager_tasks=[],
        )

    async def dispatch_daily_plan(self, day: datetime) -> list[Notification]:
        self.dispatched = True
        return [
            Notification(
                id=1,
                channel=NotificationChannel.TELEGRAM,
                recipient="@depo",
                subject="Günlük depo görevleri",
                body="Depo hazırlık listesi",
                created_at=datetime(2026, 5, 12, 8, 0, tzinfo=timezone.utc),
                status=NotificationStatus.SENT,
            )
        ]


@pytest.fixture
def client_with_workflow():
    workflow = StubWorkflowService()
    scope = SimpleNamespace(workflow=workflow)

    async def override():
        yield scope

    app.dependency_overrides[get_scope] = override
    try:
        yield TestClient(app), workflow
    finally:
        app.dependency_overrides.pop(get_scope, None)


def test_daily_plan_returns_grouped_tasks(client_with_workflow):
    client, _workflow = client_with_workflow

    response = client.get("/workflow/daily-plan")

    assert response.status_code == 200
    assert response.json()["total_tasks"] == 1
    assert response.json()["packing_tasks"][0]["role"] == "warehouse"


def test_dispatch_daily_plan_returns_notifications(client_with_workflow):
    client, workflow = client_with_workflow

    response = client.post("/workflow/dispatch")

    assert response.status_code == 200
    assert response.json()[0]["recipient"] == "@depo"
    assert workflow.dispatched is True
