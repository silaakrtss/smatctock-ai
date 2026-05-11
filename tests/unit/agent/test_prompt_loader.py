from pathlib import Path

import pytest
from src.agent.prompts.loader import PromptLoader, PromptNotFoundError


class TestPromptLoader:
    def test_loads_existing_prompt_file(self, tmp_path: Path):
        (tmp_path / "system_chat.md").write_text("# Türkçe asistan", encoding="utf-8")
        loader = PromptLoader(directory=tmp_path)

        content = loader.load("system_chat")

        assert "Türkçe asistan" in content

    def test_raises_when_missing(self, tmp_path: Path):
        loader = PromptLoader(directory=tmp_path)

        with pytest.raises(PromptNotFoundError):
            loader.load("absent")

    def test_default_directory_finds_bundled_prompts(self):
        loader = PromptLoader()

        chat = loader.load("system_chat")
        morning = loader.load("system_morning_briefing")

        assert "Tool kullanım davranışı" in chat
        assert "Brifing" in morning or "Sabah" in morning
