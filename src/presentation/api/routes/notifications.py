import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from src.infrastructure.composition import AppContainer, RequestScope
from src.presentation.api.dependencies import get_container, get_scope
from src.presentation.api.schemas import NotificationRead

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

_KEEPALIVE_INTERVAL_SECONDS = 15.0


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
            while True:
                if await request.is_disconnected():
                    break

                get_task = asyncio.create_task(queue.get())
                done, _pending = await asyncio.wait({get_task}, timeout=_KEEPALIVE_INTERVAL_SECONDS)
                if get_task in done:
                    event = get_task.result()
                    payload = json.dumps(event, ensure_ascii=False)
                    yield f"data: {payload}\n\n".encode()
                else:
                    get_task.cancel()
                    yield b": keepalive\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            container.sse_hub.unsubscribe(queue)
            _logger.debug(
                "SSE bağlantısı kapandı; aktif aboneler=%d",
                container.sse_hub.subscriber_count,
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
