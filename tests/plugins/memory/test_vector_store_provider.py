"""Tests for bundled vector_store memory provider."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from pathlib import Path

from agent.memory_manager import MemoryManager
from agent.vector_memory.embedder import HashTextEmbedder
from agent.vector_memory.factory import build_vector_backend
from plugins.memory.vector_store.provider import VectorStoreMemoryProvider


@pytest.fixture
def vs_config():
    return {
        "memory": {
            "provider": "vector_store",
            "vector_store": {
                "type": "python",
                "prefetch_top_k": 3,
                "upsert_min_chars": 10,
                "session_chunk_chars": 200,
            },
        }
    }


def test_vector_provider_available(vs_config):
    with patch("hermes_cli.config.load_config", return_value=vs_config):
        p = VectorStoreMemoryProvider()
        assert p.is_available()


def test_initialize_prefetch_and_search(vs_config):
    with patch("hermes_cli.config.load_config", return_value=vs_config):
        p = VectorStoreMemoryProvider()
        p.initialize(
            "sess-1",
            hermes_home="/tmp/hermes-test",
            agent_context="primary",
            platform="cli",
        )
        p.sync_turn("User talks about redis caching", "Assistant explains TTL keys.")
        ctx = p.prefetch("What about caching?")
        assert "vector_store" in ctx.lower() or "redis" in ctx.lower()
        raw = p.handle_tool_call(
            "vector_memory_search", {"query": "caching", "top_k": 2}
        )
        data = json.loads(raw)
        assert "results" in data
        assert len(data["results"]) >= 1
        p.shutdown()


def test_on_session_end_chunks(vs_config):
    with patch("hermes_cli.config.load_config", return_value=vs_config):
        p = VectorStoreMemoryProvider()
        p.initialize(
            "sess-2",
            hermes_home="/tmp/hermes-test",
            agent_context="primary",
            platform="cli",
        )
        msgs = [
            {"role": "user", "content": "alpha " * 80},
            {"role": "assistant", "content": "beta " * 80},
        ]
        p.on_session_end(msgs)
        ctx = p.prefetch("alpha topic")
        assert ctx
        p.shutdown()


def test_subagent_context_skips_sync_turn(vs_config):
    with patch("hermes_cli.config.load_config", return_value=vs_config):
        p = VectorStoreMemoryProvider()
        p.initialize(
            "sess-3",
            hermes_home="/tmp/hermes-test",
            agent_context="subagent",
            platform="cli",
        )
        marker = "subagent_only_marker_xyz"
        p.sync_turn(marker * 30, "y" * 200)
        ctx = p.prefetch(marker)
        p.shutdown()
        assert marker.lower() not in ctx.lower()


def test_on_delegation_upserts(vs_config):
    with patch("hermes_cli.config.load_config", return_value=vs_config):
        p = VectorStoreMemoryProvider()
        p.initialize(
            "sess-4",
            hermes_home="/tmp/hermes-test",
            agent_context="primary",
            platform="cli",
        )
        p.on_delegation("task " * 20, "result " * 20, child_session_id="c1")
        raw = p.handle_tool_call("vector_memory_search", {"query": "task"})
        data = json.loads(raw)
        assert data.get("results")
        p.shutdown()


def test_factory_unknown_type_returns_none():
    emb = HashTextEmbedder(dim=32)
    assert build_vector_backend({"type": "unknown_xyz"}, emb, Path("/tmp")) is None


def test_memory_manager_registers_tool_schema(vs_config):
    with patch("hermes_cli.config.load_config", return_value=vs_config):
        p = VectorStoreMemoryProvider()
        mgr = MemoryManager()
        mgr.add_provider(p)
        schemas = mgr.get_all_tool_schemas()
        names = {s.get("name") for s in schemas}
        assert "vector_memory_search" in names
