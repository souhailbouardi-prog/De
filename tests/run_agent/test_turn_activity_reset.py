import time
from unittest.mock import MagicMock, patch

import pytest

from run_agent import AIAgent


class _StopTurn(Exception):
    pass


def _make_agent() -> AIAgent:
    with (
        patch("run_agent.get_tool_definitions", return_value=[]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        return AIAgent(
            api_key="test-key",
            provider="custom",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )


def test_run_conversation_resets_activity_before_startup_work():
    agent = _make_agent()
    agent._last_activity_ts = time.time() - 3600
    agent._current_tool = "terminal"

    def assert_activity_reset(_system_message=None):
        summary = agent.get_activity_summary()
        assert summary["seconds_since_activity"] < 5
        assert summary["current_tool"] is None
        raise _StopTurn

    agent._cleanup_dead_connections = MagicMock(return_value=False)
    agent._build_system_prompt = MagicMock(side_effect=assert_activity_reset)

    with pytest.raises(_StopTurn):
        agent.run_conversation("new message")
