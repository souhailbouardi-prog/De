"""Tests for Mistral API compatibility helpers in AIAgent."""
import pytest
from unittest.mock import MagicMock


def _make_agent_stub(base_url: str):
    """Create a minimal stub with _base_url_lower set."""
    from run_agent import AIAgent
    stub = object.__new__(AIAgent)
    stub._base_url_lower = base_url.lower() if base_url else ""
    return stub


class TestNeedsMistralRewrite:
    def test_mistral_url_returns_true(self):
        agent = _make_agent_stub("https://api.mistral.ai/v1")
        assert agent._needs_mistral_tool_id_rewrite() is True

    def test_openai_url_returns_false(self):
        agent = _make_agent_stub("https://api.openai.com/v1")
        assert agent._needs_mistral_tool_id_rewrite() is False

    def test_empty_url_returns_false(self):
        agent = _make_agent_stub("")
        assert agent._needs_mistral_tool_id_rewrite() is False


class TestRewriteToolIds:
    def test_rewrites_long_ids_to_9_chars(self):
        from run_agent import AIAgent
        messages = [
            {"role": "assistant", "tool_calls": [
                {"id": "call_1234567890abcdef", "function": {"name": "test"}}
            ]},
            {"role": "tool", "tool_call_id": "call_1234567890abcdef", "content": "ok"},
        ]
        AIAgent._rewrite_tool_ids_for_mistral(messages)
        new_id = messages[0]["tool_calls"][0]["id"]
        assert len(new_id) == 9
        assert new_id.isalnum()
        assert messages[1]["tool_call_id"] == new_id

    def test_preserves_valid_9char_ids(self):
        from run_agent import AIAgent
        messages = [
            {"role": "assistant", "tool_calls": [
                {"id": "abcde1234", "function": {"name": "test"}}
            ]},
            {"role": "tool", "tool_call_id": "abcde1234", "content": "ok"},
        ]
        AIAgent._rewrite_tool_ids_for_mistral(messages)
        assert messages[0]["tool_calls"][0]["id"] == "abcde1234"

    def test_no_tool_calls_returns_unchanged(self):
        from run_agent import AIAgent
        messages = [{"role": "user", "content": "hello"}]
        AIAgent._rewrite_tool_ids_for_mistral(messages)
        assert messages == [{"role": "user", "content": "hello"}]


class TestSupportsReasoningContent:
    def test_mistral_returns_false(self):
        agent = _make_agent_stub("https://api.mistral.ai/v1")
        assert agent._supports_reasoning_content_field() is False

    def test_non_mistral_returns_true(self):
        agent = _make_agent_stub("https://openrouter.ai/api/v1")
        assert agent._supports_reasoning_content_field() is True
        agent2 = _make_agent_stub("https://api.example.com/v1")
        assert agent2._supports_reasoning_content_field() is True
