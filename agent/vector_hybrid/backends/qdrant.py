"""Thin Qdrant adapter (optional dependency)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any, Dict, List, Sequence

from agent.vector_hybrid.types import VectorHit

logger = logging.getLogger(__name__)


def _stable_point_id(hermes_id: str) -> int:
    h = hashlib.sha256(hermes_id.encode()).digest()[:8]
    return int.from_bytes(h, "big", signed=False) % (2**63 - 1)


class QdrantMemoryBackend:
    def __init__(
        self,
        url: str,
        api_key: str | None,
        collection: str,
        *,
        vector_size: int,
    ) -> None:
        from qdrant_client import QdrantClient  # type: ignore[import-untyped]
        from qdrant_client.models import (  # type: ignore[import-untyped]
            Distance,
            PointStruct,
            VectorParams,
        )

        self._collection = collection
        self._client = QdrantClient(url=url, api_key=api_key or None)
        self._PointStruct = PointStruct

        try:
            self._client.get_collection(collection_name=collection)
        except Exception:
            self._client.recreate_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def upsert(
        self,
        ids: Sequence[str],
        vectors: Sequence[Sequence[float]],
        payloads: Sequence[Dict[str, Any]],
    ) -> None:
        pts = []
        for hid, vec, pay in zip(ids, vectors, payloads):
            p = dict(pay)
            p["hermes_id"] = hid
            pts.append(
                self._PointStruct(id=_stable_point_id(hid), vector=list(vec), payload=p)
            )

        def _sync() -> None:
            self._client.upsert(collection_name=self._collection, points=pts)

        await asyncio.to_thread(_sync)

    async def query_vector(
        self, vector: Sequence[float], top_k: int
    ) -> List[VectorHit]:
        def _sync():
            return self._client.search(
                collection_name=self._collection,
                query_vector=list(vector),
                limit=top_k,
                with_payload=True,
            )

        hits = await asyncio.to_thread(_sync)
        out: List[VectorHit] = []
        for h in hits:
            payload = dict(h.payload or {})
            rid = str(payload.get("hermes_id") or h.id)
            sc = float(h.score or 0.0)
            out.append((rid, sc, payload))
        return out

    async def delete(self, ids: Sequence[str]) -> None:
        from qdrant_client.models import PointIdsList  # type: ignore[import-untyped]

        int_ids = [_stable_point_id(i) for i in ids]

        def _sync():
            self._client.delete(
                collection_name=self._collection,
                points_selector=PointIdsList(points=int_ids),
            )

        await asyncio.to_thread(_sync)
