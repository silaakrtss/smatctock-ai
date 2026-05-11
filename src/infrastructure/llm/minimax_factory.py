from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from src.infrastructure.llm.minimax_client import MiniMaxLLMClient


def build_minimax_client(
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: int,
) -> MiniMaxLLMClient:
    async_openai = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
    return MiniMaxLLMClient(
        client=async_openai,
        model=model,
        rate_limit_exceptions=(RateLimitError,),
        transport_exceptions=(APIConnectionError, APITimeoutError),
    )
