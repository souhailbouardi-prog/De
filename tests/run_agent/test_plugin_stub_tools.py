"""Tests for graceful plugin degradation with stub tools."""
import pytest


class TestPluginStubTools:
    """When a plugin fails to init, stub tools should explain the failure."""

    def test_stub_tool_returns_error_message(self):
        """A stub tool should return a clear message explaining the plugin is unavailable."""
        from run_agent import _make_plugin_stub_handler

        handler = _make_plugin_stub_handler("memory_search", "Honcho connection refused")
        result = handler()
        assert "Honcho" in result
        assert "unavailable" in result.lower()
        assert "memory_search" in result

    def test_stub_tool_schema_matches_original(self):
        """Stub tool schema should have the same name as the original tool."""
        from run_agent import _make_plugin_stub_schema

        schema = _make_plugin_stub_schema("memory_search", "Search persistent memory")
        assert schema["function"]["name"] == "memory_search"
        assert "unavailable" in schema["function"]["description"].lower() or "disabled" in schema["function"]["description"].lower()
