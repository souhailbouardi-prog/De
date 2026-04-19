"""Tests for terminal tool unified execution with auto-background.

Commands completing within 5 seconds return results immediately.
Commands exceeding 5 seconds are automatically moved to background execution.
"""
import json
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Shared test config dict — mirrors _get_env_config() return shape.
# ---------------------------------------------------------------------------
def _make_env_config(**overrides):
    """Return a minimal _get_env_config()-shaped dict with optional overrides."""
    config = {
        "env_type": "local",
        "timeout": 180,
        "cwd": "/tmp",
        "host_cwd": None,
        "modal_mode": "auto",
        "docker_image": "",
        "singularity_image": "",
        "modal_image": "",
        "daytona_image": "",
    }
    config.update(overrides)
    return config


class TestAutoBackground:
    """Unified execution: quick completion vs auto-background."""

    def test_quick_command_returns_immediately(self):
        """Commands completing within 5s return results immediately."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            mock_env.execute.return_value = {"output": "hello\n", "returncode": 0}

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}):
                result = json.loads(terminal_tool(command="echo hello"))

        assert result["exit_code"] == 0
        assert "hello" in result["output"]
        assert "session_id" not in result
        assert result["error"] is None
        # Should be called with 5-second timeout for quick attempt
        assert mock_env.execute.call_args[1]["timeout"] == 5

    def test_slow_command_auto_backgrounds(self):
        """Commands taking >5s auto-background with session_id."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            mock_env.env = {}
            # Simulate timeout (exit_code 124)
            mock_env.execute.return_value = {"output": "", "returncode": 124}

            mock_proc_session = MagicMock()
            mock_proc_session.id = "proc_test_123"
            mock_proc_session.pid = 12345
            mock_proc_session.notify_on_complete = False

            mock_registry = MagicMock()
            mock_registry.spawn_local.return_value = mock_proc_session

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}), \
                 patch("tools.process_registry.process_registry", mock_registry), \
                 patch("tools.approval.get_current_session_key", return_value=""), \
                 patch("gateway.session_context.get_session_env", return_value=""):
                result = json.loads(terminal_tool(command="sleep 10"))

        assert result["status"] == "auto_backgrounded"
        assert result["session_id"] == "proc_test_123"
        assert result["pid"] == 12345
        assert result["notify_on_complete"] is True
        assert "background" in result["output"].lower()
        assert "process(action='poll'" in result["output"] or "process" in result["output"]

    def test_auto_background_enables_notify_on_complete(self):
        """Auto-backgrounded commands always have notify_on_complete enabled."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            mock_env.env = {}
            mock_env.execute.return_value = {"output": "", "returncode": 124}

            mock_proc_session = MagicMock()
            mock_proc_session.id = "proc_abc"
            mock_proc_session.pid = 999
            mock_proc_session.notify_on_complete = False

            mock_registry = MagicMock()
            mock_registry.spawn_local.return_value = mock_proc_session

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}), \
                 patch("tools.process_registry.process_registry", mock_registry), \
                 patch("tools.approval.get_current_session_key", return_value=""), \
                 patch("gateway.session_context.get_session_env", return_value=""):
                result = json.loads(terminal_tool(command="long_running_task"))

        # Verify notify_on_complete was set on the session
        assert mock_proc_session.notify_on_complete is True

    def test_quick_command_with_error_returncode(self):
        """Quick commands with non-zero exit codes still return immediately."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            mock_env.execute.return_value = {"output": "error\n", "returncode": 1}

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}):
                result = json.loads(terminal_tool(command="false"))

        assert result["exit_code"] == 1
        assert "error" in result["output"]
        assert "session_id" not in result

    def test_slow_command_retries_on_transient_error(self):
        """Slow commands that fail with non-timeout errors are retried."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            # First call fails, second succeeds
            mock_env.execute.side_effect = [
                Exception("Connection error"),
                {"output": "success", "returncode": 0}
            ]

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}), \
                 patch("time.sleep"):  # Skip actual sleep
                result = json.loads(terminal_tool(command="some_command"))

        assert result["exit_code"] == 0
        assert "success" in result["output"]
        # Should have been called twice (retry)
        assert mock_env.execute.call_count == 2

    def test_workdir_passed_to_execute(self):
        """Workdir parameter is passed to env.execute."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            mock_env.execute.return_value = {"output": "", "returncode": 0}

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}):
                result = json.loads(terminal_tool(command="pwd", workdir="/home"))

        call_kwargs = mock_env.execute.call_args[1]
        assert call_kwargs["cwd"] == "/home"

    def test_pty_disabled_for_pipe_stdin_commands(self):
        """PTY is auto-disabled for commands requiring piped stdin."""
        from tools.terminal_tool import terminal_tool

        with patch("tools.terminal_tool._get_env_config", return_value=_make_env_config()), \
             patch("tools.terminal_tool._start_cleanup_thread"):

            mock_env = MagicMock()
            mock_env.env = {}
            mock_env.execute.return_value = {"output": "", "returncode": 124}

            mock_proc_session = MagicMock()
            mock_proc_session.id = "proc_pty_test"
            mock_proc_session.pid = 111
            mock_proc_session.notify_on_complete = False

            mock_registry = MagicMock()
            mock_registry.spawn_local.return_value = mock_proc_session

            with patch("tools.terminal_tool._active_environments", {"default": mock_env}), \
                 patch("tools.terminal_tool._last_activity", {"default": 0}), \
                 patch("tools.terminal_tool._check_all_guards", return_value={"approved": True}), \
                 patch("tools.process_registry.process_registry", mock_registry), \
                 patch("tools.approval.get_current_session_key", return_value=""), \
                 patch("gateway.session_context.get_session_env", return_value=""):
                # gh auth login with --with-token requires pipe stdin
                result = json.loads(terminal_tool(
                    command="gh auth login --with-token",
                    pty=True
                ))

        # PTY should be disabled for this command
        assert result["status"] == "auto_backgrounded"
        assert "pty_note" in result


class TestSchema:
    """Verify the tool schema."""

    def test_background_parameter_removed(self):
        """background parameter should not exist in schema."""
        from tools.terminal_tool import TERMINAL_SCHEMA
        properties = TERMINAL_SCHEMA["parameters"]["properties"]
        assert "background" not in properties

    def test_notify_on_complete_parameter_removed(self):
        """notify_on_complete parameter should not exist in schema."""
        from tools.terminal_tool import TERMINAL_SCHEMA
        properties = TERMINAL_SCHEMA["parameters"]["properties"]
        assert "notify_on_complete" not in properties

    def test_remaining_parameters(self):
        """Only expected parameters should remain."""
        from tools.terminal_tool import TERMINAL_SCHEMA
        properties = TERMINAL_SCHEMA["parameters"]["properties"]
        expected = {"command", "timeout", "workdir", "pty", "watch_patterns"}
        assert set(properties.keys()) == expected
