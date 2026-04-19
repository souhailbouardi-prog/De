from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_handle_limits_command_returns_live_limits_text():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    event = MagicMock()

    with patch("hermes_cli.codex_limits.get_codex_limits_text", return_value="Limits:\n5 hours: 35% remaining."):
        result = await runner._handle_limits_command(event)

    assert result == "Limits:\n5 hours: 35% remaining."


@pytest.mark.asyncio
async def test_handle_limits_command_returns_user_friendly_error():
    from gateway.run import GatewayRunner
    from hermes_cli.codex_limits import CodexLimitsError

    runner = object.__new__(GatewayRunner)
    event = MagicMock()

    with patch("hermes_cli.codex_limits.get_codex_limits_text", side_effect=CodexLimitsError("no token")):
        result = await runner._handle_limits_command(event)

    assert result == "no token"
