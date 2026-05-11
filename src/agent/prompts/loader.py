from dataclasses import dataclass
from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parent


class PromptNotFoundError(Exception):
    pass


@dataclass
class PromptLoader:
    directory: Path = _PROMPT_DIR

    def load(self, name: str) -> str:
        path = self.directory / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(f"Prompt not found: {name} (looked at {path})")
        return path.read_text(encoding="utf-8")
