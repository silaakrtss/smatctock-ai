from collections.abc import AsyncIterator

from fastapi import Request

from src.infrastructure.composition import AppContainer, RequestScope


def get_container(request: Request) -> AppContainer:
    container: AppContainer = request.app.state.container
    return container


async def get_scope(request: Request) -> AsyncIterator[RequestScope]:
    container = get_container(request)
    async with container.session_factory() as session:
        scope = await container.build_request_scope(session)
        try:
            yield scope
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
