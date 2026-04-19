"""Thin Pinecone adapter (optional dependency)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Sequence

from agent.vector_hybrid.types import VectorHit

logger = logging.getLogger(__name__)


class PineconeMemoryBackend:
    def __init__(
        self,
        api_key: str,
        index_name: str,
        *,
        namespace: str = "",
    ) -> None:
        from pinecone import Pinecone  # type: ignore[import-untyped]

        self._ns = namespace or ""
        pc = Pinecone(api_key=api_key)
        self._index = pc.Index(index_name)

    async def upsert(
        self,
        ids: Sequence[str],
        vectors: Sequence[Sequence[float]],
        payloads: Sequence[Dict[str, Any]],
    ) -> None:
        rows = [
            {"id": i, "values": list(v), "metadata": {k: str(val) for k, val in p.items()}}
            for i, v, p in zip(ids, vectors, payloads)
        ]

        def _sync():
            self._index.upsert(vectors=rows, namespace=self._ns)

        await asyncio.to_thread(_sync)

    async def query_vector(
        self, vector: Sequence[float], top_k: int
    ) -> List[VectorHit]:
        def _sync():
            return self._index.query(
                vector=list(vector),
                top_k=top_k,
                namespace=self._ns,
                include_metadata=True,
            )

        res = await asyncio.to_thread(_sync)
        out: List[VectorHit] = []
        raw = getattr(res, "matches", None) or (res.get("matches") if isinstance(res, dict) else None) or []
        for m in raw:
            if isinstance(m, dict):
                rid = str(m.get("id", ""))
                sc = float(m.get("score", 0.0))
                meta = dict(m.get("metadata") or {})
            else:
                rid = str(getattr(m, "id", ""))
                sc = float(getattr(m, "score", 0.0) or 0.0)
                meta = dict(getattr(m, "metadata", None) or {})
            out.append((rid, sc, meta))
        return out

    async def delete(self, ids: Sequence[str]) -> None:
        def _sync():
            self._index.delete(ids=list(ids), namespace=self._ns)

        await asyncio.to_thread(_sync)
