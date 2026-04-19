"""Tests for vector_hybrid memory provider and hybrid retrieval helpers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent.vector_hybrid.eviction import estimate_record_bytes, evict_by_policy
from agent.vector_hybrid.hybrid_retrieval import fuse_hybrid, keyword_score
from plugins.memory.vector_hybrid.provider import VectorHybridMemoryProvider


def test_keyword_score_basic():
    assert keyword_score("hello world", "hello there world") > 0.2


def test_fuse_hybrid_vec_and_kw():
    vec = [("a", 0.9, {"text": "alpha"}), ("b", 0.5, {"text": "beta"})]
    kw = [("a", "alpha soup", 0.4)]
    out = fuse_hybrid("alpha", vec, kw, alpha=0.6, max_chunks=5)
    assert len(out) >= 1
    assert out[0][0] == "a"


def test_evict_fifo_orders_oldest():
    now = 1_700_000_000.0
    recs = [
        ("x", {"created_ts": now - 100, "priority": 0.5}, "a"),
        ("y", {"created_ts": now - 10, "priority": 0.5}, "b"),
    ]
    total = sum(estimate_record_bytes(m, t) for _, m, t in recs)
    victim = evict_by_policy(
        [(rid, m, t) for rid, m, t in recs],
        policy="fifo",
        budget_bytes=total // 2,
        now_ts=now,
    )
    assert "x" in victim


def test_provider_available_noop_backend(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "")
    monkeypatch.setenv("PINECONE_API_KEY", "")
    with patch("hermes_cli.config.load_config") as lc:
        lc.return_value = {
            "memory": {
                "vector_hybrid": {"backend": ""},
            }
        }
        p = VectorHybridMemoryProvider()
        assert p.is_available() is True


def test_prefetch_keyword_fallback(monkeypatch):
    p = VectorHybridMemoryProvider()
    p._cron_skip = False
    p._cfg = {"prefetch_char_cap": 2000, "hybrid_alpha": 0.5, "fts_scope": "keyword_cache"}
    p._backend = MagicMock()
    p._embedder = MagicMock()
    p._embedder.fts_fallback_active.return_value = True
    p._embedder.embed_texts.return_value = []
    p._bridge = None
    p._kw = {"id1": ("python asyncio testing", {"created_ts": 1.0})}
    out = p.prefetch("async python")
    assert "vector_hybrid recall" in out or "async" in out.lower()


def test_tool_search_json():
    p = VectorHybridMemoryProvider()
    p._cron_skip = False
    p._cfg = {"prefetch_char_cap": 500, "hybrid_alpha": 0.5, "fts_scope": "keyword_cache"}
    p._backend = None
    p._embedder = MagicMock()
    p._embedder.fts_fallback_active.return_value = True
    p._embedder.embed_texts.return_value = []
    p._kw = {}
    raw = p.handle_tool_call("vector_hybrid_search", {"query": "hi"}, session_id="s")
    data = json.loads(raw)
    assert data.get("ok") is True
