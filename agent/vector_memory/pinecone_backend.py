"""Pinecone serverless index (optional pinecone-client)."""

from __future__ import annotations

import logging
import os
from typing import List, Sequence, Tuple

from agent.vector_memory.protocol import VectorStoreBackend

logger = logging.getLogger(__name__)


class PineconeVectorBackend(VectorStoreBackend):
    def __init__(self, index_name: str, api_key: str, dim: int) -> None:
        from pinecone import Pinecone  # type: ignore

        key = api_key or os.environ.get("PINECONE_API_KEY", "")
        self._pc = Pinecone(api_key=key)
        self._index = self._pc.Index(index_name)
        self._dim = int(dim)

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        recs = [
            {"id": eid, "values": list(vec), "metadata": {"text": text[:40000]}}
            for eid, text, vec in zip(ids, texts, vectors)
        ]
        self._index.upsert(vectors=recs)

    def search(
        self, query_vector: Sequence[float], top_k: int
    ) -> List[Tuple[str, str, float]]:
        res = self._index.query(
            vector=list(query_vector),
            top_k=max(1, int(top_k)),
            include_metadata=True,
        )
        out: List[Tuple[str, str, float]] = []
        for m in res.get("matches", []) or []:
            mid = str(m.get("id", ""))
            meta = m.get("metadata") or {}
            txt = str(meta.get("text", ""))
            sc = float(m.get("score", 0.0))
            out.append((mid, txt, sc))
        return out

    def close(self) -> None:
        logger.debug("pinecone client closed (no-op)")
