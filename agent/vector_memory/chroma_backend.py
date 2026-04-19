"""Chroma persistent client (optional chromadb)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Sequence, Tuple

from agent.vector_memory.protocol import VectorStoreBackend

logger = logging.getLogger(__name__)


class ChromaVectorBackend(VectorStoreBackend):
    def __init__(self, collection_name: str, persist_dir: Path) -> None:
        import chromadb  # type: ignore

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._col = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = embedder

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        self._col.upsert(
            ids=list(ids),
            documents=list(texts),
            embeddings=[list(v) for v in vectors],
        )

    def search(
        self, query_vector: Sequence[float], top_k: int
    ) -> List[Tuple[str, str, float]]:
        res = self._col.query(
            query_embeddings=[list(query_vector)],
            n_results=max(1, int(top_k)),
            include=["documents", "distances"],
        )
        out: List[Tuple[str, str, float]] = []
        ids = (res.get("ids") or [[]])[0] or []
        docs = (res.get("documents") or [[]])[0] or []
        dists = (res.get("distances") or [[]])[0] or []
        for eid, doc, dist in zip(ids, docs, dists):
            score = 1.0 - float(dist) if dist is not None else 0.0
            out.append((str(eid), str(doc or ""), score))
        return out

    def close(self) -> None:
        try:
            del self._col
            del self._client
        except Exception as e:
            logger.debug("chroma close: %s", e)
