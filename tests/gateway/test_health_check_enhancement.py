"""Tests for enhanced gateway health check endpoints.

The health check system now provides:
  - GET /health  — liveness probe with uptime and gateway state (backward-compat)
  - GET /ready   — readiness probe returning 503 when gateway is not running
  - GET /v1/status — comprehensive diagnostics (platforms, agents, config)
"""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from gateway.platforms.api_server import APIServerAdapter
from gateway.status import _build_runtime_status_record


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_mock_request():
    """Return a minimal aiohttp-like request object."""
    return MagicMock()


def _make_adapter():
    """Create an APIServerAdapter with minimal config for testing."""
    adapter = APIServerAdapter.__new__(APIServerAdapter)
    adapter._start_time = time.monotonic()
    adapter._config = {"api_key": "test", "allowed_users": [], "port": 8080}
    return adapter


# ── /health tests ─────────────────────────────────────────────────────────


class TestHealthEndpoint:
    """Enhanced /health endpoint includes uptime and gateway state."""

    def test_health_returns_ok_status(self):
        adapter = _make_adapter()
        with patch.object(adapter, "_handle_health") as mock_handler:
            # Actually call the real implementation
            pass
        # Call the real handler
        adapter = _make_adapter()
        # We need to test against the actual implementation, not a mock
        # Import the handler method directly
        from gateway.platforms.api_server import APIServerAdapter as _AS
        # Create a real-ish instance
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        # The handler is async, so we need to run it
        import asyncio
        response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
            instance._handle_health(_make_mock_request())
        )
        # aiohttp web.json_response stores the body internally
        body = json.loads(response.text)
        assert body["status"] == "ok"
        assert "platform" in body

    def test_health_includes_uptime(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic() - 100  # Started 100s ago
        import asyncio
        response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
            instance._handle_health(_make_mock_request())
        )
        body = json.loads(response.text)
        assert "uptime_seconds" in body
        assert body["uptime_seconds"] >= 99  # Allow small timing variance

    def test_health_includes_gateway_state(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        # Mock read_runtime_status to return a known state
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {"gateway_state": "running"}
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_health(_make_mock_request())
            )
            body = json.loads(response.text)
            assert body.get("gateway_state") == "running"


# ── /ready tests ──────────────────────────────────────────────────────────


class TestReadyEndpoint:
    """GET /ready returns 503 when gateway is not in 'running' state."""

    def test_ready_returns_200_when_running(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {"gateway_state": "running"}
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_ready(_make_mock_request())
            )
            assert response.status == 200
            body = json.loads(response.text)
            assert body["ready"] is True

    def test_ready_returns_503_when_starting(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {"gateway_state": "starting"}
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_ready(_make_mock_request())
            )
            assert response.status == 503
            body = json.loads(response.text)
            assert body["ready"] is False

    def test_ready_returns_503_when_draining(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {"gateway_state": "draining"}
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_ready(_make_mock_request())
            )
            assert response.status == 503

    def test_ready_returns_503_when_no_status_file(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = None
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_ready(_make_mock_request())
            )
            assert response.status == 503


# ── /v1/status tests ──────────────────────────────────────────────────────


class TestStatusEndpoint:
    """GET /v1/status returns comprehensive gateway diagnostics."""

    def test_status_includes_platforms(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {
                "gateway_state": "running",
                "platforms": {
                    "telegram": {"state": "connected"},
                    "discord": {"state": "fatal", "error_code": "token_invalid"},
                },
                "active_agents": 3,
                "pid": 12345,
            }
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_status(_make_mock_request())
            )
            body = json.loads(response.text)
            assert "platforms" in body
            assert "telegram" in body["platforms"]
            assert "discord" in body["platforms"]

    def test_status_includes_active_agents_count(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic()
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {
                "gateway_state": "running",
                "platforms": {},
                "active_agents": 5,
                "pid": 12345,
            }
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_status(_make_mock_request())
            )
            body = json.loads(response.text)
            assert body["active_agents"] == 5

    def test_status_includes_uptime(self):
        from gateway.platforms.api_server import APIServerAdapter as _AS
        instance = _AS.__new__(_AS)
        instance._start_time = time.monotonic() - 200
        with patch("gateway.platforms.api_server.read_runtime_status") as mock_status:
            mock_status.return_value = {"gateway_state": "running", "platforms": {}, "pid": 12345}
            import asyncio
            response = asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                instance._handle_status(_make_mock_request())
            )
            body = json.loads(response.text)
            assert "uptime_seconds" in body
            assert body["uptime_seconds"] >= 199
