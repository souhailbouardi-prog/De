import json
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from gateway.config import PlatformConfig
from gateway.platforms.api_server import APIServerAdapter, cors_middleware, security_headers_middleware


class _ChatSessionDB:
    def resolve_session_id(self, session_id):
        if session_id == "short":
            return "ws_full_123"
        return session_id

    def get_messages_as_conversation(self, session_id):
        return [{"role": "assistant", "content": f"history for {session_id}"}]


def _make_adapter(api_key: str = "") -> APIServerAdapter:
    extra = {}
    if api_key:
        extra["key"] = api_key
    return APIServerAdapter(PlatformConfig(enabled=True, extra=extra))


def _create_app(adapter: APIServerAdapter) -> web.Application:
    mws = [mw for mw in (cors_middleware, security_headers_middleware) if mw is not None]
    app = web.Application(middlewares=mws)
    app["api_server_adapter"] = adapter
    app.router.add_get("/api/config", adapter._handle_get_config)
    app.router.add_patch("/api/config", adapter._handle_patch_config)
    app.router.add_post("/api/sessions/{session_id}/chat", adapter._handle_session_chat)
    app.router.add_post("/api/sessions/{session_id}/chat/stream", adapter._handle_session_chat_stream)
    return app


class TestWorkspaceConfigAPI:
    @pytest.mark.asyncio
    async def test_get_config_redacts_secrets(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", str(tmp_path))
        config_dir = tmp_path / ".hermes"
        config_dir.mkdir(parents=True)
        (config_dir / "config.yaml").write_text(
            """
model:
  provider: openai
mcp_servers:
  figma:
    env:
      API_KEY: secret-123
      SAFE_FLAG: visible
custom_providers:
  - name: internal
    api_key: super-secret
""".strip()
        )

        adapter = _make_adapter()
        app = _create_app(adapter)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.get("/api/config")
            assert resp.status == 200
            data = await resp.json()
            assert data["mcp_servers"]["figma"]["env"]["API_KEY"] == "***REDACTED***"
            assert data["mcp_servers"]["figma"]["env"]["SAFE_FLAG"] == "visible"
            assert data["custom_providers"][0]["api_key"] == "***REDACTED***"


    @pytest.mark.asyncio
    async def test_patch_config_rejects_non_object_payload(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", str(tmp_path))
        config_dir = tmp_path / ".hermes"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.yaml"
        config_path.write_text("model:\n  provider: openai\n")

        adapter = _make_adapter()
        app = _create_app(adapter)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.patch(
                "/api/config",
                data='["not", "an", "object"]',
                headers={"Content-Type": "application/json"},
            )
            assert resp.status == 400
            data = await resp.json()
            assert "JSON object" in data["error"]

        assert config_path.read_text() == "model:\n  provider: openai\n"

    @pytest.mark.asyncio
    async def test_patch_config_merges_allowed_keys_and_ignores_unsupported(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", str(tmp_path))
        config_dir = tmp_path / ".hermes"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.yaml"
        config_path.write_text(
            """
model:
  provider: openai
  model: gpt-4
display:
  theme: dark
platforms:
  telegram:
    enabled: true
""".strip()
        )

        adapter = _make_adapter()
        app = _create_app(adapter)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.patch(
                "/api/config",
                json={
                    "model": {"model": "gpt-5"},
                    "display": {"theme": "light"},
                    "platforms": {"telegram": {"enabled": False}},
                },
            )
            assert resp.status == 200
            data = await resp.json()
            assert sorted(data["updated_keys"]) == ["display", "model"]

        written = config_path.read_text()
        assert "model: gpt-5" in written
        assert "theme: light" in written
        assert "enabled: true" in written
        assert "enabled: false" not in written


class TestWorkspaceChatAPI:
    @pytest.mark.asyncio
    async def test_session_chat_uses_resolved_session_id_and_history(self):
        adapter = _make_adapter()
        adapter._session_db = _ChatSessionDB()

        captured = {}

        async def fake_run_agent(**kwargs):
            captured.update(kwargs)
            return {"final_response": "done"}, {"input_tokens": 1}

        adapter._run_agent = fake_run_agent
        app = _create_app(adapter)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/api/sessions/short/chat",
                json={"message": "hello", "system_message": "be sharp"},
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["session_id"] == "ws_full_123"
            assert data["response"] == "done"

        assert captured["session_id"] == "ws_full_123"
        assert captured["ephemeral_system_prompt"] == "be sharp"
        assert captured["conversation_history"] == [
            {"role": "assistant", "content": "history for ws_full_123"}
        ]

    @pytest.mark.asyncio
    async def test_session_chat_stream_emits_started_delta_completed_and_done(self):
        adapter = _make_adapter()
        adapter._session_db = _ChatSessionDB()

        async def fake_run_agent(**kwargs):
            kwargs["stream_delta_callback"]("hel")
            kwargs["stream_delta_callback"]("lo")
            return {"final_response": "hello"}, {"output_tokens": 2}

        adapter._run_agent = fake_run_agent
        app = _create_app(adapter)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/api/sessions/short/chat/stream",
                json={"message": "hello"},
            )
            assert resp.status == 200
            body = await resp.text()

        assert "event: run.started" in body
        assert "event: assistant.delta" in body
        assert "event: assistant.completed" in body
        assert "event: run.completed" in body
        assert "data: [DONE]" in body
        assert '"session_id": "ws_full_123"' in body
