from src.presentation.api.response_sanitizer import strip_reasoning_blocks


class TestStripReasoningBlocks:
    def test_removes_think_block_and_preserves_body(self):
        raw = "<think>plan</think>\n\nDomates stoğu 8 adet."

        cleaned = strip_reasoning_blocks(raw)

        assert "<think>" not in cleaned
        assert "plan" not in cleaned
        assert "Domates stoğu 8 adet." in cleaned

    def test_removes_multiline_think_block(self):
        raw = "<think>\nMulti-line reasoning here.\nStep 1, step 2.\n</think>\n\nCevap: 12 adet."

        cleaned = strip_reasoning_blocks(raw)

        assert "reasoning" not in cleaned
        assert cleaned == "Cevap: 12 adet."

    def test_keeps_content_without_think_blocks(self):
        cleaned = strip_reasoning_blocks("Düz cevap.")

        assert cleaned == "Düz cevap."

    def test_collapses_excess_blank_lines(self):
        raw = "<think>x</think>\n\n\n\n\nGerçek cevap."

        cleaned = strip_reasoning_blocks(raw)

        assert "\n\n\n" not in cleaned
        assert cleaned == "Gerçek cevap."

    def test_case_insensitive_block_tag(self):
        raw = "<THINK>x</THINK>Cevap"

        cleaned = strip_reasoning_blocks(raw)

        assert cleaned == "Cevap"
