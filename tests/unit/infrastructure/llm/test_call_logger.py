import json
from datetime import datetime, timezone
from pathlib import Path

from src.application.ports.llm_client import ChatMessage, LLMResponse, ToolCall
from src.infrastructure.llm.call_logger import JsonlCallLogger


def _now() -> datetime:
    return datetime(2026, 5, 11, 8, 0, tzinfo=timezone.utc)


def _read_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


class TestJsonlCallLogger:
    def test_writes_one_jsonl_line_per_call(self, tmp_path: Path):
        logger = JsonlCallLogger(directory=tmp_path, clock=_now)

        logger.record(
            provider="minimax",
            model="MiniMax-M2.7",
            request_messages=[ChatMessage(role="user", content="merhaba")],
            response=LLMResponse(content="selam", tool_calls=()),
        )

        log_file = tmp_path / "2026-05-11.jsonl"
        assert log_file.exists()
        entries = _read_lines(log_file)
        assert len(entries) == 1
        entry = entries[0]
        assert entry["provider"] == "minimax"
        assert entry["model"] == "MiniMax-M2.7"
        assert entry["request"][0]["content"] == "merhaba"
        assert entry["response"]["content"] == "selam"

    def test_appends_to_same_day_file(self, tmp_path: Path):
        logger = JsonlCallLogger(directory=tmp_path, clock=_now)
        empty_response = LLMResponse(content=None, tool_calls=())

        logger.record(
            provider="minimax",
            model="m",
            request_messages=[ChatMessage(role="user", content="1")],
            response=empty_response,
        )
        logger.record(
            provider="minimax",
            model="m",
            request_messages=[ChatMessage(role="user", content="2")],
            response=empty_response,
        )

        entries = _read_lines(tmp_path / "2026-05-11.jsonl")
        assert [entry["request"][0]["content"] for entry in entries] == ["1", "2"]

    def test_serializes_tool_calls(self, tmp_path: Path):
        logger = JsonlCallLogger(directory=tmp_path, clock=_now)
        response = LLMResponse(
            content=None,
            tool_calls=(ToolCall(id="c1", name="get_stock", arguments={"id": 1}),),
            reasoning_details={"thought": "x"},
        )

        logger.record(
            provider="minimax",
            model="m",
            request_messages=[],
            response=response,
        )

        entries = _read_lines(tmp_path / "2026-05-11.jsonl")
        assert entries[0]["response"]["tool_calls"][0]["name"] == "get_stock"
        assert entries[0]["response"]["reasoning_details"] == {"thought": "x"}
