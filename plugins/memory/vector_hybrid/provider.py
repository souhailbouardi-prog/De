"""VectorHybrid MemoryProvider — dense index + keyword cache + optional Honcho nudge."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List

from agent.memory_provider import MemoryProvider
from agent.vector_hybrid import EmbeddingService, build_memory_backend
from plugins.memory.vector_hybrid.async_util import run_async
from plugins.memory.vector_hybrid.honcho_bridge import HonchoDialecticBridge
from plugins.memory.vector_hybrid.prefetch_fmt import format_hybrid_prefetch
from tools.registry import tool_error

logger = logging.getLogger(__name__)

SEARCH_SCHEMA = {
    "name": "vector_hybrid_search",
    "description": (
        "Search hybrid vector + keyword memory indexed for this Hermes session."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language query."},
        },
        "required": ["query"],
    },
}


class VectorHybridMemoryProvider(MemoryProvider):
    def __init__(self) -> None:
        self._cfg: Dict[str, Any] = {}
        self._backend = None
        self._embedder: EmbeddingService | None = None
        self._bridge: HonchoDialecticBridge | None = None
        self._cron_skip = False
        self._kw: Dict[str, tuple[str, dict[str, Any]]] = {}
        self._session_id = ""

    @property
    def name(self) -> str:
        return "vector_hybrid"

    def is_available(self) -> bool:
        """True when noop / keyword path is usable or backend env vars are set."""
        try:
            import os

            from hermes_cli.config import load_config

            vh = (load_config().get("memory") or {}).get("vector_hybrid") or {}
            b = (vh.get("backend") or "").strip().lower()
            if b in ("", "none"):
                return True
            if b == "qdrant":
                envk = vh.get("qdrant_url_env") or "QDRANT_URL"
                return bool(os.environ.get(envk, "").strip())
            if b == "pinecone":
                pk = vh.get("pinecone_api_key_env") or "PINECONE_API_KEY"
                pi = vh.get("pinecone_index_env") or "PINECONE_INDEX"
                return bool(os.environ.get(pk, "").strip() and os.environ.get(pi, "").strip())
            return False
        except Exception:
            return False

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        self._session_id = session_id
        ctx = kwargs.get("agent_context", "")
        plat = kwargs.get("platform", "")
        if ctx in ("cron", "flush") or plat == "cron":
            self._cron_skip = True
            logger.debug("vector_hybrid skipped (cron/flush)")
            return

        from hermes_cli.config import load_config

        merged = load_config().get("memory") or {}
        self._cfg = dict(merged.get("vector_hybrid") or {})

        self._backend = build_memory_backend(self._cfg)
        self._embedder = EmbeddingService(self._cfg)
        self._bridge = HonchoDialecticBridge(bool(self._cfg.get("honcho_bridge")))
        if self._bridge:
            self._bridge.setup(session_id, **kwargs)

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._cron_skip or not query.strip():
            return ""
        vec_hits: List[tuple[str, float, dict[str, Any]]] = []
        emb: List[List[float]] = []
        if self._embedder and not self._embedder.fts_fallback_active():
            emb = self._embedder.embed_texts([query.strip()])
        if emb and self._backend:
            try:
                vec_hits = run_async(
                    self._backend.query_vector(emb[0], top_k=10),
                    timeout=60,
                )
            except Exception as e:
                logger.debug("Vector query failed (fallback to keywords): %s", e)

        return format_hybrid_prefetch(
            query=query,
            cfg=self._cfg,
            vec_hits=vec_hits,
            kw_map=self._kw,
            bridge=self._bridge,
        )

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        if self._cron_skip or not self._backend or not self._embedder:
            return
        blob = (user_content + "\n---\n" + assistant_content).strip()
        if not blob:
            return
        tid = hashlib.sha256(blob.encode()).hexdigest()[:20]
        now = time.time()
        meta = {"created_ts": now, "priority": 0.35, "text": blob[:1200]}
        self._kw[tid] = (blob[:8000], meta)

        vecs = self._embedder.embed_texts([blob[:4000]])
        if not vecs:
            return
        try:
            run_async(
                self._backend.upsert([tid], vecs, [meta]),
                timeout=120,
            )
        except Exception as e:
            logger.debug("vector_hybrid upsert skipped: %s", e)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [SEARCH_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs: Any) -> str:
        if tool_name != "vector_hybrid_search":
            raise NotImplementedError(tool_name)
        q = (args.get("query") or "").strip()
        if not q:
            return tool_error("query required")
        body = self.prefetch(q, session_id=str(kwargs.get("session_id", "")))
        return json.dumps({"ok": True, "context": body})

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if self._cron_skip or not self._backend or not self._embedder:
            return
        parts: List[str] = []
        for m in messages[-40:]:
            role = m.get("role", "")
            content = str(m.get("content", ""))[:4000]
            if content.strip():
                parts.append(f"{role}: {content}")
        blob = "\n".join(parts)[:16000]
        if len(blob) < 40:
            return
        sid = hashlib.sha256(blob.encode()).hexdigest()[:24]
        now = time.time()
        meta = {"created_ts": now, "priority": 0.9, "text": blob[:2000], "kind": "session_summary"}
        vecs = self._embedder.embed_texts([blob[:6000]])
        if not vecs:
            return
        try:
            run_async(self._backend.upsert([sid], vecs, [meta]), timeout=180)
        except Exception as e:
            logger.debug("session summary upsert skipped: %s", e)

    def shutdown(self) -> None:
        self._kw.clear()
