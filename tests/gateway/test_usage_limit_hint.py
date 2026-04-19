from types import SimpleNamespace
from unittest.mock import patch


def _make_runner():
    from gateway.run import GatewayRunner

    return object.__new__(GatewayRunner)


def test_usage_limit_hint_includes_live_limits_for_codex():
    runner = _make_runner()
    agent = SimpleNamespace(provider="openai-codex", base_url="https://chatgpt.com/backend-api/codex")

    with patch("hermes_cli.codex_limits.should_show_codex_limits", return_value=True), \
         patch("hermes_cli.codex_limits.get_codex_limits_text", return_value="Limits:\n5 hours: 0% remaining.\nResets in 0:12:00."):
        status_hint, action_hint = runner._format_usage_limit_status_hint(
            error_payload={"type": "usage_limit_reached", "resets_in_seconds": 700},
            agent=agent,
        )

    assert "Your plan limit has been reached." in status_hint
    assert "It resets in about 1h." in status_hint
    assert "Limits:" in status_hint
    assert action_hint == "Wait for one of the windows above to reset, or run /limits again later."


def test_usage_limit_hint_falls_back_to_limits_command_when_live_limits_unavailable():
    runner = _make_runner()

    with patch("hermes_cli.codex_limits.should_show_codex_limits", return_value=False):
        status_hint, action_hint = runner._format_usage_limit_status_hint(
            error_payload={"type": "usage_limit_reached"},
            agent=None,
        )

    assert "Wait for the next reset window." in status_hint
    assert "Run /limits" in status_hint
    assert action_hint == "Wait for one of the windows above to reset, or run /limits again later."
