import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from src.infrastructure.composition import AppContainer, RequestScope
from src.presentation.api.dependencies import get_container, get_scope
from src.presentation.api.schemas import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_recent(
    limit: int = 20, scope: RequestScope = Depends(get_scope)
) -> list[NotificationRead]:
    notifications = await scope.notification_repo.list_recent(limit=limit)
    return [NotificationRead.from_domain(n) for n in notifications]


@router.get("/stream")
async def stream_notifications(
    request: Request,
    container: AppContainer = Depends(get_container),
) -> StreamingResponse:
    queue = container.sse_hub.subscribe()

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield b": keepalive\n\n"
                    continue
                payload = json.dumps(event, ensure_ascii=False)
                yield f"data: {payload}\n\n".encode()
        finally:
            container.sse_hub.unsubscribe(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
