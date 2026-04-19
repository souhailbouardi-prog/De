"""Factory for optional vector backends."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Protocol, runtime_checkable

from agent.vector_hybrid.backends.noop import NoOpMemoryBackend

logger = logging.getLogger(__name__)


@runtime_checkable
class MemoryBackend(Protocol):
    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None: ...

    async def query_vector(
        self, vector: list[float], top_k: int
    ) -> list[tuple[str, float, dict[str, Any]]]: ...

    async def delete(self, ids: list[str]) -> None: ...


def build_memory_backend(cfg: Dict[str, Any]) -> MemoryBackend:
    """Return a backend from merged vector_hybrid config (no network)."""
    raw = (cfg.get("backend") or "").strip().lower()
    if raw in ("", "none"):
        return NoOpMemoryBackend()  # type: ignore[return-value]

    if raw == "qdrant":
        url_env = cfg.get("qdrant_url_env") or "QDRANT_URL"
        key_env = cfg.get("qdrant_api_key_env") or "QDRANT_API_KEY"
        url = os.environ.get(url_env, "").strip()
        if not url:
            logger.warning("Qdrant selected but %s unset — using noop backend", url_env)
            return NoOpMemoryBackend()  # type: ignore[return-value]
        api_key = os.environ.get(key_env, "").strip() or None
        coll = cfg.get("collection") or "hermes_memory"
        dim = int(cfg.get("embedding_dimensions") or 1536)
        try:
            from agent.vector_hybrid.backends.qdrant import QdrantMemoryBackend

            return QdrantMemoryBackend(url, api_key, coll, vector_size=dim)  # type: ignore[return-value]
        except Exception as e:
            logger.warning("Qdrant backend unavailable: %s", e)
            return NoOpMemoryBackend()  # type: ignore[return-value]

    if raw == "pinecone":
        key_env = cfg.get("pinecone_api_key_env") or "PINECONE_API_KEY"
        idx_env = cfg.get("pinecone_index_env") or "PINECONE_INDEX"
        key = os.environ.get(key_env, "").strip()
        idx = os.environ.get(idx_env, "").strip()
        if not key or not idx:
            logger.warning("Pinecone selected but env incomplete — noop backend")
            return NoOpMemoryBackend()  # type: ignore[return-value]
        ns = (cfg.get("pinecone_namespace") or "").strip()
        try:
            from agent.vector_hybrid.backends.pinecone import PineconeMemoryBackend

            return PineconeMemoryBackend(key, idx, namespace=ns)  # type: ignore[return-value]
        except Exception as e:
            logger.warning("Pinecone backend unavailable: %s", e)
            return NoOpMemoryBackend()  # type: ignore[return-value]

    logger.warning("Unknown vector_hybrid.backend %r — noop", raw)
    return NoOpMemoryBackend()  # type: ignore[return-value]
