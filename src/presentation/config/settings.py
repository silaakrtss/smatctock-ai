from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["minimax", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: LLMProvider = Field(default="minimax")

    minimax_api_key: str = Field(default="")
    minimax_model: str = Field(default="MiniMax-M2.7")
    minimax_base_url: str = Field(default="https://api.minimax.io/v1")
    minimax_timeout_seconds: int = Field(default=30)

    google_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")
    gemini_timeout_seconds: int = Field(default=30)

    database_url: str = Field(default="sqlite+aiosqlite:///./data/app.db")

    scheduler_stock_check_cron: str = Field(default="0 * * * *")
    scheduler_shipping_check_cron: str = Field(default="0 * * * *")
    scheduler_morning_briefing_cron: str = Field(default="0 8 * * *")

    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")

    agent_max_tool_iterations: int = Field(default=8)

    chat_reply_cache_ttl_seconds: int = Field(default=300)

    manager_recipient: str = Field(default="@manager")
    supplier_recipient: str = Field(default="@tedarik")

    scheduler_enabled: bool = Field(default=False)


def get_settings() -> Settings:
    return Settings()
