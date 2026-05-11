import re

_THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)
_MULTIPLE_BLANKS_PATTERN = re.compile(r"\n{3,}")


def strip_reasoning_blocks(content: str) -> str:
    """LLM'in user-facing yanıtından <think>...</think> bloklarını çıkarır.

    ADR-0005 § 5 conversation state'inde reasoning bloklarının TAM korunmasını
    şart koşar (tool-calling chain için kritik). Bu yardımcı YALNIZCA dış
    sunuma giderken çağrılır; state üzerinde etki etmez.
    """
    without_blocks = _THINK_BLOCK_PATTERN.sub("", content)
    collapsed = _MULTIPLE_BLANKS_PATTERN.sub("\n\n", without_blocks)
    return collapsed.strip()
