"""Regression tests for the `/sethome` lock.

Home channel is set once (during provisioning or on first use) and then
locked. Without this guard, any user authorized to message the agent can
run ``/sethome`` to hijack owner identity, which matters under
``GATEWAY_ALLOW_ALL_USERS=true``.

Lock behavior:
  1. No home set → ``/sethome`` succeeds and persists.
  2. Home set via env var → ``/sethome`` rejects.
  3. Home set via loaded config → ``/sethome`` rejects.
  4. Lock is per-platform.
"""

import asyncio
import os

import gateway.run as gateway_run
from gateway.config import GatewayConfig, HomeChannel, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent, MessageType
from gateway.session import SessionSource


def _make_runner(config=None):
    runner = object.__new__(gateway_run.GatewayRunner)
    runner.config = config
    return runner


def _sethome_event(chat_id="123456", chat_name="Alice DM"):
    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id=chat_id,
        chat_name=chat_name,
        chat_type="dm",
        user_id="tg-user-1",
    )
    return MessageEvent(
        text="/sethome",
        message_type=MessageType.COMMAND,
        source=source,
        raw_message=None,
    )


def test_sethome_succeeds_when_no_home_is_set(monkeypatch, tmp_path):
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)
    cfg = GatewayConfig()
    cfg.platforms[Platform.TELEGRAM] = PlatformConfig(enabled=True)
    runner = _make_runner(cfg)

    result = asyncio.run(runner._handle_set_home_command(_sethome_event()))

    assert "✅" in result
    assert "Alice DM" in result
    assert os.environ.get("TELEGRAM_HOME_CHANNEL") == "123456"
    assert (tmp_path / "config.yaml").exists()
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)


def test_sethome_rejects_when_env_var_already_set(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_HOME_CHANNEL", "existing-home-chat")
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)
    runner = _make_runner(GatewayConfig())

    result = asyncio.run(runner._handle_set_home_command(_sethome_event()))

    assert "already set" in result.lower()
    assert os.environ["TELEGRAM_HOME_CHANNEL"] == "existing-home-chat"
    assert not (tmp_path / "config.yaml").exists()


def test_sethome_rejects_when_config_has_home_channel(monkeypatch, tmp_path):
    """Lock must trigger even if the env var is absent but the loaded
    GatewayConfig carries a home channel from provisioning."""
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)

    cfg = GatewayConfig()
    cfg.platforms[Platform.TELEGRAM] = PlatformConfig(
        enabled=True,
        home_channel=HomeChannel(
            platform=Platform.TELEGRAM,
            chat_id="provisioned-home",
            name="Owner",
        ),
    )
    runner = _make_runner(cfg)

    result = asyncio.run(runner._handle_set_home_command(_sethome_event()))

    assert "already set" in result.lower()
    assert os.environ.get("TELEGRAM_HOME_CHANNEL") is None
    assert not (tmp_path / "config.yaml").exists()


def test_sethome_lock_is_per_platform(monkeypatch, tmp_path):
    """A home channel set for Telegram must not lock /sethome on Discord."""
    monkeypatch.setenv("TELEGRAM_HOME_CHANNEL", "tg-home")
    monkeypatch.delenv("DISCORD_HOME_CHANNEL", raising=False)
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)

    cfg = GatewayConfig()
    cfg.platforms[Platform.TELEGRAM] = PlatformConfig(
        enabled=True,
        home_channel=HomeChannel(
            platform=Platform.TELEGRAM, chat_id="tg-home", name="TG Home",
        ),
    )
    cfg.platforms[Platform.DISCORD] = PlatformConfig(enabled=True)
    runner = _make_runner(cfg)

    discord_source = SessionSource(
        platform=Platform.DISCORD,
        chat_id="ds-channel-1",
        chat_name="General",
        chat_type="channel",
        user_id="ds-user-1",
    )
    event = MessageEvent(
        text="/sethome",
        message_type=MessageType.COMMAND,
        source=discord_source,
        raw_message=None,
    )

    result = asyncio.run(runner._handle_set_home_command(event))

    assert "✅" in result
    assert os.environ.get("DISCORD_HOME_CHANNEL") == "ds-channel-1"
    assert os.environ.get("TELEGRAM_HOME_CHANNEL") == "tg-home"
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)
    monkeypatch.delenv("DISCORD_HOME_CHANNEL", raising=False)
