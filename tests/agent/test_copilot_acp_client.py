from __future__ import annotations

from unittest.mock import patch

import pytest

from agent.copilot_acp_client import CopilotACPClient


def _make_client(tmp_path):
    return CopilotACPClient(
        api_key="copilot-acp",
        base_url="acp://copilot",
        acp_command="copilot",
        acp_args=["--acp", "--stdio"],
        acp_cwd=str(tmp_path),
    )


def _fake_popen_capture(captured):
    def _fake(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        raise FileNotFoundError("copilot not found")

    return _fake


def test_run_prompt_prefers_profile_home_when_available(monkeypatch, tmp_path):
    hermes_home = tmp_path / "hermes"
    profile_home = hermes_home / "home"
    profile_home.mkdir(parents=True)

    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    captured = {}
    client = _make_client(tmp_path)

    with patch("agent.copilot_acp_client.subprocess.Popen", side_effect=_fake_popen_capture(captured)):
        with pytest.raises(RuntimeError, match="Could not start Copilot ACP command"):
            client._run_prompt("hello", timeout_seconds=1)

    assert captured["kwargs"]["env"]["HOME"] == str(profile_home)


def test_run_prompt_passes_home_when_parent_env_is_clean(monkeypatch, tmp_path):
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("HERMES_HOME", raising=False)

    captured = {}
    client = _make_client(tmp_path)

    with patch("agent.copilot_acp_client.subprocess.Popen", side_effect=_fake_popen_capture(captured)):
        with pytest.raises(RuntimeError, match="Could not start Copilot ACP command"):
            client._run_prompt("hello", timeout_seconds=1)

    assert "env" in captured["kwargs"]
    assert captured["kwargs"]["env"]["HOME"]
