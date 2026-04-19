"""Vector-store MemoryProvider (semantic recall + optional tool search)."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List

from agent.memory_provider import MemoryProvider
from agent.vector_memory import build_embedder, build_vector_backend
from agent.vector_memory.protocol import VectorStoreBackend
from plugins.memory.vector_store.cfg import chunk_text, mem_vector_cfg
from plugins.memory.vector_store.schemas import VECTOR_SEARCH_SCHEMA
from tools.registry import tool_error

logger = logging.getLogger(__name__)


class VectorStoreMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "vector_store"

    def is_available(self) -> bool:
        vs = mem_vector_cfg()
        try:
            from hermes_constants import get_hermes_home

            emb = build_embedder(vs)
            home = Path(str(get_hermes_home()))
            return build_vector_backend(vs or {"type": "python"}, emb, home) is not None
        except Exception as e:
            logger.debug("vector_store is_available: %s", e)
            return False

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        self._session_id = session_id
        self._ctx = dict(kwargs)
        self._lock = threading.Lock()
        vs = mem_vector_cfg()
        self._embedder = build_embedder(vs)
        from hermes_constants import get_hermes_home

        hh = kwargs.get("hermes_home") or str(get_hermes_home())
        home = Path(str(hh))
        self._backend = build_vector_backend(vs or {"type": "python"}, self._embedder, home)
        self._top_k = int(vs.get("prefetch_top_k", 5))
        self._min_chars = int(vs.get("upsert_min_chars", 40))
        self._chunk = int(vs.get("session_chunk_chars", 800))
        self._turn = 0
        if self._backend is None:
            logger.warning("vector_store: backend failed to initialize")

    def system_prompt_block(self) -> str:
        return (
            "Vector memory is active: recent turns and session-end chunks are "
            "indexed for semantic recall. Use vector_memory_search for explicit lookup."
        )

    def _primary(self) -> bool:
        return str(self._ctx.get("agent_context", "primary")) == "primary"

    def _upsert_texts(self, pairs: List[tuple[str, str]]) -> None:
        if not self._backend or not pairs:
            return
        ids, texts = zip(*pairs)
        vecs = self._embedder.encode(list(texts))
        with self._lock:
            self._backend.upsert(list(ids), list(texts), vecs)

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._backend or not query.strip():
            return ""
        try:
            qv = self._embedder.encode([query.strip()])[0]
            with self._lock:
                hits = self._backend.search(qv, self._top_k)
        except Exception as e:
            logger.debug("vector_store prefetch: %s", e)
            return ""
        if not hits:
            return ""
        lines = [f"[{s:.3f}] {txt[:500]}" for _eid, txt, s in hits if txt]
        return "vector_store recall:\n" + "\n".join(lines)

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        if not self._primary() or not self._backend:
            return
        blob = f"{user_content}\n{assistant_content}".strip()
        if len(blob) < self._min_chars:
            return
        self._turn += 1
        sid = session_id or self._session_id
        doc_id = hashlib.sha256(f"{sid}:{self._turn}".encode()).hexdigest()[:24]
        self._upsert_texts([(doc_id, blob)])

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if not self._primary() or not self._backend:
            return
        parts: List[str] = []
        for m in messages:
            role = str(m.get("role", ""))
            content = m.get("content", "")
            if isinstance(content, list):
                content = json.dumps(content)[: self._chunk * 2]
            parts.append(f"{role}: {str(content)[:4000]}")
        big = "\n\n".join(parts)
        sid = self._session_id
        chunk_pairs: List[tuple[str, str]] = []
        for i, chunk in enumerate(chunk_text(big, self._chunk)):
            if len(chunk) < self._min_chars:
                continue
            cid = hashlib.sha256(f"{sid}:sess:{i}".encode()).hexdigest()[:24]
            chunk_pairs.append((cid, chunk))
        self._upsert_texts(chunk_pairs)

    def on_delegation(
        self, task: str, result: str, *, child_session_id: str = "", **kwargs: Any
    ) -> None:
        if not self._backend:
            return
        blob = f"delegation task:\n{task}\n\nresult:\n{result}".strip()
        if len(blob) < self._min_chars:
            return
        cid = hashlib.sha256(
            f"{self._session_id}:sub:{child_session_id}".encode()
        ).hexdigest()[:24]
        self._upsert_texts([(cid, blob)])

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [VECTOR_SEARCH_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs: Any) -> str:
        if tool_name != "vector_memory_search":
            return tool_error(f"Unknown tool {tool_name}")
        if not self._backend:
            return tool_error("Vector backend not initialized")
        q = str(args.get("query", "")).strip()
        if not q:
            return tool_error("Missing query")
        tk = int(args.get("top_k") or self._top_k)
        tk = max(1, min(tk, 20))
        try:
            qv = self._embedder.encode([q])[0]
            with self._lock:
                hits = self._backend.search(qv, tk)
            return json.dumps({"results": [{"text": t, "score": s} for _i, t, s in hits]})
        except Exception as e:
            return tool_error(str(e))

    def shutdown(self) -> None:
        if self._backend:
            try:
                self._backend.close()
            except Exception as e:
                logger.debug("vector_store shutdown: %s", e)
            self._backend = None
