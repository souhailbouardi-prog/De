from types import SimpleNamespace

import httpx

from agent.copilot_acp_client import CopilotACPClient


def test_create_chat_completion_accepts_httpx_timeout_object(monkeypatch):
    client = CopilotACPClient(command="copilot", args=["--acp", "--stdio"])

    captured = {}

    def fake_run_prompt(prompt_text, *, timeout_seconds):
        captured["timeout_seconds"] = timeout_seconds
        return "ok", ""

    monkeypatch.setattr(client, "_run_prompt", fake_run_prompt)

    response = client._create_chat_completion(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "ping"}],
        timeout=httpx.Timeout(timeout=30.0, connect=5.0),
    )

    assert response.choices[0].message.content == "ok"
    assert isinstance(captured["timeout_seconds"], float)
    assert captured["timeout_seconds"] == 30.0
