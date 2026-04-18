import os
from unittest.mock import Mock, patch


class TestLiveCdpPersistentConnect:
    def test_first_live_cdp_command_connects_once_then_reuses_session(self, tmp_path):
        import tools.browser_tool as browser_tool

        session_info = {
            "session_name": "live-session",
            "cdp_url": "ws://host:9222/devtools/browser/abc",
            "features": {"cdp_override": True},
        }
        captured = []
        responses = [
            {"success": True, "data": {"launched": True}, "error": None},
            {"success": True, "data": {"title": "Example Domain"}, "error": None},
            {"success": True, "data": {"title": "Example Domain"}, "error": None},
        ]

        def fake_execute(cmd_parts, command, timeout, task_id, task_socket_dir, browser_env):
            captured.append((cmd_parts, command, task_socket_dir, browser_env))
            return responses[len(captured) - 1]

        with (
            patch("tools.browser_tool._find_agent_browser", return_value="npx agent-browser"),
            patch("tools.browser_tool._get_session_info", return_value=session_info),
            patch("tools.browser_tool._get_cdp_override", return_value="ws://host:9222/devtools/browser/abc"),
            patch("tools.browser_tool._socket_safe_tmpdir", return_value=str(tmp_path)),
            patch("tools.browser_tool._execute_browser_cli", side_effect=fake_execute),
            patch("tools.interrupt.is_interrupted", return_value=False),
        ):
            first = browser_tool._run_browser_command("task-live", "open", ["https://example.com"], timeout=30)
            second = browser_tool._run_browser_command("task-live", "get", ["title"], timeout=30)

        assert first["success"] is True
        assert second["success"] is True
        assert session_info["_persistent_cdp_connected"] is True

        connect_cmd, connect_name, connect_socket_dir, connect_env = captured[0]
        assert connect_name == "connect"
        assert connect_cmd == [
            "npx",
            "agent-browser",
            "connect",
            "--session",
            "live-session",
            "ws://host:9222/devtools/browser/abc",
            "--json",
        ]
        assert connect_socket_dir == os.path.join(str(tmp_path), "agent-browser-live-session")
        assert connect_env["AGENT_BROWSER_SOCKET_DIR"] == connect_socket_dir

        open_cmd, open_name, *_ = captured[1]
        get_cmd, get_name, *_ = captured[2]
        assert open_name == "open"
        assert get_name == "get"
        assert open_cmd[:6] == ["npx", "agent-browser", "--session", "live-session", "--json", "open"]
        assert get_cmd[:6] == ["npx", "agent-browser", "--session", "live-session", "--json", "get"]
        assert sum(1 for cmd, *_ in captured if cmd[2] == "connect") == 1

    def test_live_cdp_stale_timeout_resets_socket_dir_reconnects_and_retries_once(self, tmp_path):
        import tools.browser_tool as browser_tool

        session_info = {
            "session_name": "live-session",
            "cdp_url": "ws://host:9222/devtools/browser/abc",
            "features": {"cdp_override": True},
        }
        captured = []
        responses = [
            {"success": True, "data": {"launched": True}, "error": None},
            {"success": False, "error": "Command timed out after 30 seconds"},
            {"success": True, "data": {"launched": True}, "error": None},
            {"success": True, "data": {"snapshot": "ok", "refs": {}}, "error": None},
        ]
        reset_mock = Mock()

        def fake_execute(cmd_parts, command, timeout, task_id, task_socket_dir, browser_env):
            captured.append((cmd_parts, command))
            return responses[len(captured) - 1]

        with (
            patch("tools.browser_tool._find_agent_browser", return_value="npx agent-browser"),
            patch("tools.browser_tool._get_session_info", return_value=session_info),
            patch(
                "tools.browser_tool._get_cdp_override",
                side_effect=[
                    "ws://host:9222/devtools/browser/abc",
                    "ws://host:9222/devtools/browser/def",
                ],
            ),
            patch("tools.browser_tool._socket_safe_tmpdir", return_value=str(tmp_path)),
            patch("tools.browser_tool._execute_browser_cli", side_effect=fake_execute),
            patch("tools.browser_tool._reset_agent_browser_socket_dir", reset_mock),
            patch("tools.interrupt.is_interrupted", return_value=False),
        ):
            result = browser_tool._run_browser_command("task-live", "snapshot", ["-c"], timeout=30)

        assert result["success"] is True
        assert session_info["_persistent_cdp_connected"] is True
        reset_mock.assert_called_once_with("live-session")
        assert [name for _, name in captured] == ["connect", "snapshot", "connect", "snapshot"]
        assert captured[0][0][5] == "ws://host:9222/devtools/browser/abc"
        assert captured[2][0][5] == "ws://host:9222/devtools/browser/def"

    def test_live_cdp_close_timeout_does_not_retry_reconnect(self, tmp_path):
        import tools.browser_tool as browser_tool

        session_info = {
            "session_name": "live-session",
            "cdp_url": "ws://host:9222/devtools/browser/abc",
            "features": {"cdp_override": True},
        }
        captured = []
        responses = [
            {"success": True, "data": {"launched": True}, "error": None},
            {"success": False, "error": "Command timed out after 10 seconds"},
        ]
        reset_mock = Mock()

        def fake_execute(cmd_parts, command, timeout, task_id, task_socket_dir, browser_env):
            captured.append((cmd_parts, command))
            return responses[len(captured) - 1]

        with (
            patch("tools.browser_tool._find_agent_browser", return_value="npx agent-browser"),
            patch("tools.browser_tool._get_session_info", return_value=session_info),
            patch("tools.browser_tool._socket_safe_tmpdir", return_value=str(tmp_path)),
            patch("tools.browser_tool._execute_browser_cli", side_effect=fake_execute),
            patch("tools.browser_tool._reset_agent_browser_socket_dir", reset_mock),
            patch("tools.interrupt.is_interrupted", return_value=False),
        ):
            result = browser_tool._run_browser_command("task-live", "close", [], timeout=10)

        assert result["success"] is False
        assert "timed out" in result["error"]
        reset_mock.assert_not_called()
        assert [name for _, name in captured] == ["connect", "close"]

    def test_non_live_cloud_cdp_still_uses_per_command_cdp(self, tmp_path):
        import tools.browser_tool as browser_tool

        session_info = {
            "session_name": "cloud-session",
            "cdp_url": "ws://cloud.example/devtools/browser/xyz",
            "features": {"browserbase": True},
        }
        captured = []

        def fake_execute(cmd_parts, command, timeout, task_id, task_socket_dir, browser_env):
            captured.append((cmd_parts, command))
            return {"success": True, "data": {"snapshot": "ok", "refs": {}}, "error": None}

        with (
            patch("tools.browser_tool._find_agent_browser", return_value="npx agent-browser"),
            patch("tools.browser_tool._get_session_info", return_value=session_info),
            patch("tools.browser_tool._socket_safe_tmpdir", return_value=str(tmp_path)),
            patch("tools.browser_tool._execute_browser_cli", side_effect=fake_execute),
            patch("tools.interrupt.is_interrupted", return_value=False),
        ):
            result = browser_tool._run_browser_command("task-cloud", "snapshot", ["-c"], timeout=30)

        assert result["success"] is True
        cmd, name = captured[0]
        assert name == "snapshot"
        assert cmd[:6] == [
            "npx",
            "agent-browser",
            "--cdp",
            "ws://cloud.example/devtools/browser/xyz",
            "--json",
            "snapshot",
        ]
