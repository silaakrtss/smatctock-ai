from src.agent.tools.tool_result import ToolResult


class TestSuccess:
    def test_success_carries_payload(self):
        result = ToolResult.success({"stock": 40})

        assert result.is_error is False
        assert result.payload == {"stock": 40}
        assert result.error_message is None

    def test_success_to_model_string_serializes_payload(self):
        result = ToolResult.success({"stock": 40, "name": "Domates"})

        encoded = result.to_model_string()

        assert "stock" in encoded
        assert "40" in encoded


class TestError:
    def test_error_carries_message(self):
        result = ToolResult.error("Bilinmeyen tool")

        assert result.is_error is True
        assert result.error_message == "Bilinmeyen tool"
        assert result.payload is None

    def test_error_to_model_string_includes_message(self):
        result = ToolResult.error("Argüman hatası: id zorunlu")

        encoded = result.to_model_string()

        assert "Argüman hatası" in encoded
        assert "error" in encoded.lower()
