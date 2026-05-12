from fastapi import APIRouter, Depends, HTTPException

from src.agent.loop import AgentLoopExceededError
from src.agent.tools.definitions import TOOL_DEFINITIONS
from src.application.ports.llm_client import ChatMessage
from src.application.ports.llm_errors import LLMRateLimitError, LLMTransportError
from src.infrastructure.composition import RequestScope
from src.presentation.api.dependencies import get_scope
from src.presentation.api.response_sanitizer import strip_reasoning_blocks
from src.presentation.api.schemas import AiChatRequest, AiChatResponse

router = APIRouter(tags=["ai-chat"])


@router.post("/ai-chat", response_model=AiChatResponse)
async def ai_chat(
    request: AiChatRequest, scope: RequestScope = Depends(get_scope)
) -> AiChatResponse:
    system_prompt = scope.prompt_loader.load("system_chat")
    try:
        response = await scope.agent_loop.run(
            messages=[ChatMessage(role="user", content=request.message)],
            tools=TOOL_DEFINITIONS,
            system_prompt=system_prompt,
        )
    except AgentLoopExceededError as exc:
        raise HTTPException(
            status_code=422,
            detail="İsteğinizi tam çözemedim, biraz daha spesifik sorabilir misiniz?",
        ) from exc
    except LLMRateLimitError as exc:
        raise HTTPException(
            status_code=503, detail="LLM kotası doldu, lütfen biraz sonra tekrar deneyin."
        ) from exc
    except LLMTransportError as exc:
        raise HTTPException(
            status_code=503, detail="LLM servisine ulaşılamadı, lütfen tekrar deneyin."
        ) from exc

    answer = strip_reasoning_blocks(response.content or "") or "(yanıt üretilemedi)"

    if request.message_id:
        await scope.chat_reply_cache.set(message_id=request.message_id, content=answer)
        await scope.chat_reply_publisher.publish(message_id=request.message_id, content=answer)

    return AiChatResponse(answer=answer)


@router.get("/ai-chat/replies/{message_id}", response_model=AiChatResponse)
async def get_chat_reply(
    message_id: str, scope: RequestScope = Depends(get_scope)
) -> AiChatResponse:
    content = await scope.chat_reply_cache.get(message_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Cevap bulunamadı veya süresi doldu.")
    return AiChatResponse(answer=content)
