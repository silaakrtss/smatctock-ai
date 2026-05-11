from src.presentation.config.settings import Settings


def test_settings_loads_with_defaults(monkeypatch):
    for key in [
        "MINIMAX_API_KEY",
        "GEMINI_API_KEY",
        "DATABASE_URL",
        "TELEGRAM_BOT_TOKEN",
        "AGENT_MAX_TOOL_ITERATIONS",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.minimax_model == "MiniMax-M2.7"
    assert settings.database_url.startswith("sqlite+aiosqlite")
    assert settings.agent_max_tool_iterations == 8


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_TOOL_ITERATIONS", "16")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.agent_max_tool_iterations == 16
    assert settings.minimax_api_key == "test-key"
