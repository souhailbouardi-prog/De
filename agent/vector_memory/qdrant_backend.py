"""Qdrant local or remote (optional qdrant-client)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Sequence, Tuple

from agent.vector_memory.protocol import VectorStoreBackend

logger = logging.getLogger(__name__)


class QdrantVectorBackend(VectorStoreBackend):
    def __init__(self, collection: str, path: str, url: str, api_key: str, dim: int) -> None:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.http import models as qm  # type: ignore

        self._qm = qm
        if path and str(path).strip():
            self._client = QdrantClient(path=str(Path(path)))
        else:
            self._client = QdrantClient(
                url=url or "http://127.0.0.1:6333",
                api_key=api_key or None,
            )
        self._collection = collection
        self._dim = int(dim)
        try:
            self._client.get_collection(collection)
        except Exception:
            self._client.create_collection(
                collection_name=collection,
                vectors_config=qm.VectorParams(size=self._dim, distance=qm.Distance.COSINE),
            )

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        points = []
        for eid, text, vec in zip(ids, texts, vectors):
            pid = abs(hash(eid)) % (2**63 - 1) + 1
            points.append(
                self._qm.PointStruct(
                    id=pid,
                    vector=list(vec),
                    payload={"external_id": eid, "text": text},
                )
            )
        self._client.upsert(collection_name=self._collection, points=points)

    def search(
        self, query_vector: Sequence[float], top_k: int
    ) -> List[Tuple[str, str, float]]:
        hits = self._client.search(
            collection_name=self._collection,
            query_vector=list(query_vector),
            limit=max(1, int(top_k)),
            with_payload=True,
        )
        out: List[Tuple[str, str, float]] = []
        for h in hits:
            pl = h.payload or {}
            ext = str(pl.get("external_id", h.id))
            txt = str(pl.get("text", ""))
            out.append((ext, txt, float(h.score)))
        return out

    def close(self) -> None:
        try:
            self._client.close()
        except Exception as e:
            logger.debug("qdrant close: %s", e)
