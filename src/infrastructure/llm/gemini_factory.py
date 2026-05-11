from google import genai
from google.genai import errors

from src.infrastructure.llm.gemini_client import GeminiLLMClient


def build_gemini_client(
    *,
    api_key: str,
    model: str,
) -> GeminiLLMClient:
    client = genai.Client(api_key=api_key)
    return GeminiLLMClient(
        client=client,
        model=model,
        rate_limit_exceptions=(errors.APIError,),
        transport_exceptions=(errors.ServerError,),
    )
