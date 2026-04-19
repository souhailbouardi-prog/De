"""Tests for ``_resolve_max_request_bytes`` (API_SERVER_MAX_REQUEST_MB)."""

import importlib

import pytest

from gateway.platforms import api_server as api_server_module
from gateway.platforms.api_server import _resolve_max_request_bytes


@pytest.fixture
def env(monkeypatch):
    monkeypatch.delenv("API_SERVER_MAX_REQUEST_MB", raising=False)
    return monkeypatch


class TestResolveMaxRequestBytes:
    def test_default_is_25_mb(self, env):
        assert _resolve_max_request_bytes() == 25 * 1024 * 1024

    def test_env_override_integer_mb(self, env):
        env.setenv("API_SERVER_MAX_REQUEST_MB", "50")
        assert _resolve_max_request_bytes() == 50 * 1024 * 1024

    def test_env_override_fractional_mb(self, env):
        env.setenv("API_SERVER_MAX_REQUEST_MB", "0.5")
        assert _resolve_max_request_bytes() == 524_288  # 0.5 MiB

    def test_empty_env_uses_default(self, env):
        env.setenv("API_SERVER_MAX_REQUEST_MB", "")
        assert _resolve_max_request_bytes() == 25 * 1024 * 1024

    def test_whitespace_env_uses_default(self, env):
        env.setenv("API_SERVER_MAX_REQUEST_MB", "   ")
        assert _resolve_max_request_bytes() == 25 * 1024 * 1024

    def test_invalid_env_falls_back_to_default(self, env, caplog):
        env.setenv("API_SERVER_MAX_REQUEST_MB", "not-a-number")
        with caplog.at_level("WARNING"):
            assert _resolve_max_request_bytes() == 25 * 1024 * 1024
        assert any("API_SERVER_MAX_REQUEST_MB" in r.getMessage() for r in caplog.records)

    def test_non_positive_env_falls_back_to_default(self, env):
        env.setenv("API_SERVER_MAX_REQUEST_MB", "0")
        assert _resolve_max_request_bytes() == 25 * 1024 * 1024
        env.setenv("API_SERVER_MAX_REQUEST_MB", "-5")
        assert _resolve_max_request_bytes() == 25 * 1024 * 1024

    def test_module_constant_reflects_default(self):
        # Sanity: the module-level constant captures the default at import time.
        assert api_server_module.MAX_REQUEST_BYTES >= 1_000_000
