"""Tests for agent/context_compressor.py — _generate_summary fallback fix."""

import inspect
import pytest


class TestGenerateSummaryFallback:
    """Verify the summary model fallback doesn't pass int as focus_topic."""

    def test_method_signature(self):
        """_generate_summary second param should be focus_topic (str|None), not budget."""
        from agent.context_compressor import ContextCompressor
        sig = inspect.signature(ContextCompressor._generate_summary)
        params = list(sig.parameters.values())
        # params[0] is self, params[1] is turns_to_summarize, params[2] is focus_topic
        assert len(params) >= 3
        focus_param = params[2]
        assert focus_param.name == "focus_topic"
        assert focus_param.default is None

    def test_fallback_call_uses_keyword(self):
        """Read the source to verify line 744 uses focus_topic=, not positional int."""
        import agent.context_compressor as mod
        source = inspect.getsource(mod)
        # The bug was: self._generate_summary(messages, summary_budget)
        # The fix is:  self._generate_summary(messages, focus_topic=focus_topic)
        assert "summary_budget" not in source.split("retry immediately")[0].split("_generate_summary(messages")[-1] or \
               "focus_topic=focus_topic" in source
        # Specifically check the fallback line
        for line in source.split("\n"):
            if "retry immediately" in line and "_generate_summary" in line:
                assert "focus_topic=focus_topic" in line, (
                    f"Fallback call should use keyword arg: {line.strip()}"
                )
                assert "summary_budget" not in line, (
                    f"Fallback call should not pass summary_budget: {line.strip()}"
                )
