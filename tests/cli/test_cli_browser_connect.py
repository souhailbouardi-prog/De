"""Tests for CLI browser CDP auto-launch helpers."""

import io
import os
import contextlib
from unittest.mock import patch

from cli import HermesCLI


def _assert_chrome_debug_cmd(cmd, expected_chrome, expected_port):
    """Verify the auto-launch command has all required flags."""
    assert cmd[0] == expected_chrome
    assert f"--remote-debugging-port={expected_port}" in cmd
    assert "--no-first-run" in cmd
    assert "--no-default-browser-check" in cmd
    user_data_args = [a for a in cmd if a.startswith("--user-data-dir=")]
    assert len(user_data_args) == 1, "Expected exactly one --user-data-dir flag"
    assert "chrome-debug" in user_data_args[0]


class TestChromeDebugLaunch:
    def test_windows_launch_uses_browser_found_on_path(self):
        captured = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            return object()

        with patch("cli.shutil.which", side_effect=lambda name: r"C:\Chrome\chrome.exe" if name == "chrome.exe" else None), \
             patch("cli.os.path.isfile", side_effect=lambda path: path == r"C:\Chrome\chrome.exe"), \
             patch("subprocess.Popen", side_effect=fake_popen):
            assert HermesCLI._try_launch_chrome_debug(9333, "Windows") is True

        _assert_chrome_debug_cmd(captured["cmd"], r"C:\Chrome\chrome.exe", 9333)
        assert captured["kwargs"]["start_new_session"] is True

    def test_windows_launch_falls_back_to_common_install_dirs(self, monkeypatch):
        captured = {}
        program_files = r"C:\Program Files"
        # Use os.path.join so path separators match cross-platform
        installed = os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe")

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            return object()

        monkeypatch.setenv("ProgramFiles", program_files)
        monkeypatch.delenv("ProgramFiles(x86)", raising=False)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)

        with patch("cli.shutil.which", return_value=None), \
             patch("cli.os.path.isfile", side_effect=lambda path: path == installed), \
             patch("subprocess.Popen", side_effect=fake_popen):
            assert HermesCLI._try_launch_chrome_debug(9222, "Windows") is True

        _assert_chrome_debug_cmd(captured["cmd"], installed, 9222)


class TestBrowserConnectBehavior:
    def test_status_uses_config_backed_cdp_url(self, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        config.write_text("browser:\n  cdp_url: http://127.0.0.1:9222\n")
        monkeypatch.setattr("cli._hermes_home", tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)

        cli = HermesCLI.__new__(HermesCLI)
        buf = io.StringIO()
        with patch.object(HermesCLI, "_cdp_endpoint_reachable", return_value=True), \
             contextlib.redirect_stdout(buf):
            cli._handle_browser_command("/browser status")

        out = buf.getvalue()
        assert "connected to live Chrome via CDP" in out
        assert "http://127.0.0.1:9222" in out
        assert "Source: config.yaml" in out

    def test_disconnect_reports_persistent_config_instead_of_erasing_it(self, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        config.write_text("browser:\n  cdp_url: http://127.0.0.1:9222\n")
        monkeypatch.setattr("cli._hermes_home", tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)

        cli = HermesCLI.__new__(HermesCLI)
        buf = io.StringIO()
        with patch("tools.browser_tool.cleanup_all_browsers"), \
             contextlib.redirect_stdout(buf):
            cli._handle_browser_command("/browser disconnect")

        out = buf.getvalue()
        assert "configured via config.yaml" in out
        assert "fully revert to default mode" in out
        assert "http://127.0.0.1:9222" in config.read_text()

    def test_disconnect_keeps_persistent_config_when_env_override_is_active(self, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        config.write_text("browser:\n  cdp_url: http://127.0.0.1:9222\n")
        monkeypatch.setattr("cli._hermes_home", tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        monkeypatch.setenv("BROWSER_CDP_URL", "http://127.0.0.1:9333")

        cli = HermesCLI.__new__(HermesCLI)
        buf = io.StringIO()
        with patch("tools.browser_tool.cleanup_all_browsers"), \
             contextlib.redirect_stdout(buf):
            cli._handle_browser_command("/browser disconnect")

        out = buf.getvalue()
        assert "session override disconnected" in out.lower()
        assert "browser.cdp_url remains active" in out
        assert "http://127.0.0.1:9222" in config.read_text()
        assert os.environ.get("BROWSER_CDP_URL", "") == ""

    def test_status_probes_actual_host_not_localhost(self, monkeypatch):
        monkeypatch.setenv("BROWSER_CDP_URL", "http://unreachable.invalid:9333")
        cli = HermesCLI.__new__(HermesCLI)
        buf = io.StringIO()
        with patch.object(HermesCLI, "_cdp_endpoint_reachable", return_value=False), \
             contextlib.redirect_stdout(buf):
            cli._handle_browser_command("/browser status")

        out = buf.getvalue()
        assert "http://unreachable.invalid:9333" in out
        assert "not reachable" in out

    def test_connect_does_not_set_env_when_endpoint_unreachable(self, monkeypatch):
        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
        cli = HermesCLI.__new__(HermesCLI)
        buf = io.StringIO()
        with patch.object(HermesCLI, "_cdp_endpoint_reachable", return_value=False), \
             patch.object(HermesCLI, "_try_launch_chrome_debug", return_value=False), \
             patch("tools.browser_tool.cleanup_all_browsers"), \
             contextlib.redirect_stdout(buf):
            cli._handle_browser_command("/browser connect http://unreachable.invalid:9333")

        out = buf.getvalue()
        assert "connection was not changed" in out.lower()
        assert os.environ.get("BROWSER_CDP_URL", "") == ""

    def test_connect_sets_env_when_endpoint_reachable(self, monkeypatch):
        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
        cli = HermesCLI.__new__(HermesCLI)
        with patch.object(HermesCLI, "_cdp_endpoint_reachable", return_value=True), \
             patch("tools.browser_tool.cleanup_all_browsers"):
            cli._handle_browser_command("/browser connect http://127.0.0.1:9222")

        assert os.environ["BROWSER_CDP_URL"] == "http://127.0.0.1:9222"
