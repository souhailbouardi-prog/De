"""Tests for gateway/config.py reply_in_thread bridging.

Issue: #7532 - slack.reply_in_thread config not applied to platform extra dict
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from gateway.config import PlatformConfig, GatewayConfig, load_gateway_config, Platform


class TestReplyInThreadBridging:
    """Test that reply_in_thread config is bridged to platform extra dict."""

    def test_slack_reply_in_thread_false_bridged(self, tmp_path):
        """When slack.reply_in_thread: false, it should be in platform extra."""
        config_yaml = """
slack:
  reply_in_thread: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            # Load gateway config
            gw_config = load_gateway_config()

            # Check slack platform
            slack_config = gw_config.platforms.get(Platform.SLACK)
            if slack_config:
                extra = slack_config.extra
                assert "reply_in_thread" in extra
                assert extra["reply_in_thread"] is False

    def test_slack_reply_in_thread_true_bridged(self, tmp_path):
        """When slack.reply_in_thread: true, it should be in platform extra."""
        config_yaml = """
slack:
  reply_in_thread: true
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            slack_config = gw_config.platforms.get(Platform.SLACK)
            if slack_config:
                extra = slack_config.extra
                assert "reply_in_thread" in extra
                assert extra["reply_in_thread"] is True

    def test_slack_reply_in_thread_default_true(self, tmp_path):
        """When reply_in_thread not set, default should be True."""
        config_yaml = """
slack:
  require_mention: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            slack_config = gw_config.platforms.get(Platform.SLACK)
            if slack_config:
                # Default behavior: reply_in_thread not in extra, defaults to True
                # when accessed via .get("reply_in_thread", True)
                assert slack_config.extra.get("reply_in_thread", True) is True

    def test_discord_reply_in_thread_bridged(self, tmp_path):
        """Discord reply_in_thread should also be bridged."""
        config_yaml = """
discord:
  reply_in_thread: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            discord_config = gw_config.platforms.get(Platform.DISCORD)
            if discord_config:
                extra = discord_config.extra
                assert "reply_in_thread" in extra
                assert extra["reply_in_thread"] is False

    def test_telegram_reply_in_thread_bridged(self, tmp_path):
        """Telegram reply_in_thread should also be bridged."""
        config_yaml = """
telegram:
  reply_in_thread: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            telegram_config = gw_config.platforms.get(Platform.TELEGRAM)
            if telegram_config:
                extra = telegram_config.extra
                assert "reply_in_thread" in extra
                assert extra["reply_in_thread"] is False

    def test_multiple_platforms_reply_in_thread(self, tmp_path):
        """Multiple platforms can have different reply_in_thread settings."""
        config_yaml = """
slack:
  reply_in_thread: false
discord:
  reply_in_thread: true
telegram:
  reply_in_thread: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            slack_config = gw_config.platforms.get(Platform.SLACK)
            if slack_config:
                assert slack_config.extra.get("reply_in_thread") is False

            discord_config = gw_config.platforms.get(Platform.DISCORD)
            if discord_config:
                assert discord_config.extra.get("reply_in_thread") is True

            telegram_config = gw_config.platforms.get(Platform.TELEGRAM)
            if telegram_config:
                assert telegram_config.extra.get("reply_in_thread") is False


class TestReplyInThreadWithOtherConfigs:
    """Test reply_in_thread combined with other platform configs."""

    def test_reply_in_thread_with_require_mention(self, tmp_path):
        """reply_in_thread should work alongside require_mention."""
        config_yaml = """
slack:
  require_mention: false
  reply_in_thread: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            slack_config = gw_config.platforms.get(Platform.SLACK)
            if slack_config:
                extra = slack_config.extra
                assert "reply_in_thread" in extra
                assert extra["reply_in_thread"] is False

    def test_reply_in_thread_with_free_response_channels(self, tmp_path):
        """reply_in_thread should work alongside free_response_channels."""
        config_yaml = """
slack:
  free_response_channels: ["C123", "C456"]
  reply_in_thread: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
            gw_config = load_gateway_config()

            slack_config = gw_config.platforms.get(Platform.SLACK)
            if slack_config:
                extra = slack_config.extra
                assert "reply_in_thread" in extra
                assert extra["reply_in_thread"] is False
                # free_response_channels should also be bridged
                assert "free_response_channels" in extra


if __name__ == "__main__":
    pytest.main([__file__, "-v"])