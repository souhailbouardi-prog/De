"""Tests for empty-response fallback handling in GatewayRunner."""

import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _mock_dotenv(monkeypatch):
    """gateway.run imports dotenv at module level; stub it for tests."""
    fake = types.ModuleType("dotenv")
    fake.load_dotenv = lambda *a, **kw: None
    monkeypatch.setitem(sys.modules, "dotenv", fake)


@pytest.fixture()
def runner():
    from gateway.run import GatewayRunner

    return GatewayRunner.__new__(GatewayRunner)


class TestEmptyResponseFallback:
    def test_reasoning_only_message(self, runner):
        message = runner._build_empty_response_message({
            "empty_response_reasoning": "structured reasoning answer",
        })
        assert message == (
            "⚠️ The model produced internal reasoning but no visible response after all retries. "
            "Try again or rephrase your question."
        )

    def test_truly_empty_message(self, runner):
        message = runner._build_empty_response_message({})
        assert message == (
            "⚠️ The model returned no content after all retries. "
            "Try again or rephrase your question."
        )

    def test_response_fallback_detection_handles_new_and_legacy_forms(self, runner):
        assert runner._is_empty_response_fallback(
            {"response_is_empty_fallback": True},
            "⚠️ The model returned no content after all retries. Try again or rephrase your question.",
        )
        assert runner._is_empty_response_fallback({}, "(empty)")
        assert not runner._is_empty_response_fallback({}, "hello world")
