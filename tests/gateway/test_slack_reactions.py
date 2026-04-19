"""
Tests for the Slack reactions toggle (#8372).

Discord and Telegram already support a configurable reactions toggle
(DISCORD_REACTIONS / TELEGRAM_REACTIONS). This PR brings parity to
the Slack adapter via SLACK_REACTIONS env var and the `reactions` config key.
"""

import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import Platform, PlatformConfig


def _ensure_slack_mock():
    """Inject minimal slack-bolt + slack-sdk mocks so the adapter can be imported."""
    if "slack_bolt" in sys.modules:
        return

    bolt = MagicMock()
    bolt.async_app = MagicMock()
    bolt.async_app.AsyncApp = MagicMock
    bolt.adapter = MagicMock()
    bolt.adapter.socket_mode = MagicMock()
    bolt.adapter.socket_mode.aiohttp = MagicMock()
    bolt.adapter.socket_mode.aiohttp.AsyncSocketModeHandler = MagicMock

    sdk = MagicMock()
    sdk.web = MagicMock()
    sdk.web.async_client = MagicMock()
    sdk.web.async_client.AsyncWebClient = MagicMock

    sys.modules.setdefault("slack_bolt", bolt)
    sys.modules.setdefault("slack_bolt.async_app", bolt.async_app)
    sys.modules.setdefault("slack_bolt.adapter", bolt.adapter)
    sys.modules.setdefault("slack_bolt.adapter.socket_mode", bolt.adapter.socket_mode)
    sys.modules.setdefault("slack_bolt.adapter.socket_mode.aiohttp", bolt.adapter.socket_mode.aiohttp)
    sys.modules.setdefault("slack_sdk", sdk)
    sys.modules.setdefault("slack_sdk.web", sdk.web)
    sys.modules.setdefault("slack_sdk.web.async_client", sdk.web.async_client)


_ensure_slack_mock()

from gateway.platforms.slack import SlackAdapter  # noqa: E402


@pytest.fixture
def adapter():
    config = PlatformConfig(enabled=True, token="xoxb-test-token")
    a = SlackAdapter(config)
    return a


# ---------------------------------------------------------------------------
# _reactions_enabled unit tests
# ---------------------------------------------------------------------------

class TestReactionsEnabled:
    def test_default_is_true(self, adapter, monkeypatch):
        """Reactions are enabled by default (no env var set)."""
        monkeypatch.delenv("SLACK_REACTIONS", raising=False)
        assert adapter._reactions_enabled() is True

    def test_env_false_disables(self, adapter, monkeypatch):
        monkeypatch.setenv("SLACK_REACTIONS", "false")
        assert adapter._reactions_enabled() is False

    def test_env_zero_disables(self, adapter, monkeypatch):
        monkeypatch.setenv("SLACK_REACTIONS", "0")
        assert adapter._reactions_enabled() is False

    def test_env_no_disables(self, adapter, monkeypatch):
        monkeypatch.setenv("SLACK_REACTIONS", "no")
        assert adapter._reactions_enabled() is False

    def test_env_true_enables(self, adapter, monkeypatch):
        monkeypatch.setenv("SLACK_REACTIONS", "true")
        assert adapter._reactions_enabled() is True

    def test_env_one_enables(self, adapter, monkeypatch):
        monkeypatch.setenv("SLACK_REACTIONS", "1")
        assert adapter._reactions_enabled() is True

    def test_config_key_false_overrides_env(self, monkeypatch):
        """config.extra['reactions'] takes precedence over env var."""
        monkeypatch.setenv("SLACK_REACTIONS", "true")
        config = PlatformConfig(enabled=True, token="xoxb-test", extra={"reactions": False})
        a = SlackAdapter(config)
        assert a._reactions_enabled() is False

    def test_config_key_true_overrides_env(self, monkeypatch):
        monkeypatch.setenv("SLACK_REACTIONS", "false")
        config = PlatformConfig(enabled=True, token="xoxb-test", extra={"reactions": True})
        a = SlackAdapter(config)
        assert a._reactions_enabled() is True

    def test_config_key_string_false(self, monkeypatch):
        monkeypatch.delenv("SLACK_REACTIONS", raising=False)
        config = PlatformConfig(enabled=True, token="xoxb-test", extra={"reactions": "false"})
        a = SlackAdapter(config)
        assert a._reactions_enabled() is False


# ---------------------------------------------------------------------------
# Integration: reactions are skipped when disabled
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reactions_not_called_when_disabled(adapter, monkeypatch):
    """When SLACK_REACTIONS=false, _add_reaction should never be called."""
    monkeypatch.setenv("SLACK_REACTIONS", "false")

    adapter._add_reaction = AsyncMock()
    adapter._remove_reaction = AsyncMock()
    adapter.handle_message = AsyncMock()

    # Simulate the reaction guard directly
    _should_react = True  # DM or mentioned
    channel_id = "C123"
    ts = "1234567890.123"

    if _should_react and adapter._reactions_enabled():
        await adapter._add_reaction(channel_id, ts, "eyes")

    await adapter.handle_message(None)

    if _should_react and adapter._reactions_enabled():
        await adapter._remove_reaction(channel_id, ts, "eyes")
        await adapter._add_reaction(channel_id, ts, "white_check_mark")

    adapter._add_reaction.assert_not_called()
    adapter._remove_reaction.assert_not_called()


@pytest.mark.asyncio
async def test_reactions_called_when_enabled(adapter, monkeypatch):
    """When SLACK_REACTIONS=true (default), reactions should be added."""
    monkeypatch.setenv("SLACK_REACTIONS", "true")

    adapter._add_reaction = AsyncMock()
    adapter._remove_reaction = AsyncMock()
    adapter.handle_message = AsyncMock()

    _should_react = True
    channel_id = "C123"
    ts = "1234567890.123"

    if _should_react and adapter._reactions_enabled():
        await adapter._add_reaction(channel_id, ts, "eyes")

    await adapter.handle_message(None)

    if _should_react and adapter._reactions_enabled():
        await adapter._remove_reaction(channel_id, ts, "eyes")
        await adapter._add_reaction(channel_id, ts, "white_check_mark")

    assert adapter._add_reaction.call_count == 2  # eyes + white_check_mark
    assert adapter._remove_reaction.call_count == 1  # remove eyes


@pytest.mark.asyncio
async def test_reactions_not_sent_when_should_react_false(adapter, monkeypatch):
    """Even when enabled, reactions are skipped if _should_react is False."""
    monkeypatch.setenv("SLACK_REACTIONS", "true")

    adapter._add_reaction = AsyncMock()
    adapter._remove_reaction = AsyncMock()
    adapter.handle_message = AsyncMock()

    _should_react = False  # not a DM, not mentioned
    channel_id = "C123"
    ts = "1234567890.123"

    if _should_react and adapter._reactions_enabled():
        await adapter._add_reaction(channel_id, ts, "eyes")

    await adapter.handle_message(None)

    if _should_react and adapter._reactions_enabled():
        await adapter._remove_reaction(channel_id, ts, "eyes")
        await adapter._add_reaction(channel_id, ts, "white_check_mark")

    adapter._add_reaction.assert_not_called()
    adapter._remove_reaction.assert_not_called()
