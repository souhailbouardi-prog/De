"""FAISS-backed in-process index (optional faiss-cpu + numpy)."""

from __future__ import annotations

import threading
from typing import List, Sequence, Tuple

import numpy as np

from agent.vector_memory.protocol import VectorStoreBackend


class FAISSVectorBackend(VectorStoreBackend):
    """IndexIDMap2(IndexFlatIP) with L2-normalized vectors (cosine via IP)."""

    def __init__(self, dim: int) -> None:
        import faiss  # type: ignore

        self._faiss = faiss
        self._dim = int(dim)
        self._lock = threading.Lock()
        base = faiss.IndexFlatIP(self._dim)
        self._index = faiss.IndexIDMap2(base)
        self._text_by_id: dict[int, str] = {}
        self._ext_by_id: dict[int, str] = {}

    def _stable_id(self, ext_id: str) -> int:
        h = abs(hash(ext_id))
        return (h % (2**63 - 1)) + 1

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        with self._lock:
            for ext_id, text, vec in zip(ids, texts, vectors):
                iid = self._stable_id(ext_id)
                try:
                    self._index.remove_ids(np.array([iid], dtype="int64"))
                except Exception:
                    pass
                row = np.array([list(vec)], dtype="float32")
                self._faiss.normalize_L2(row)
                self._index.add_with_ids(row, np.array([iid], dtype="int64"))
                self._text_by_id[iid] = text
                self._ext_by_id[iid] = ext_id

    def search(
        self, query_vector: Sequence[float], top_k: int
    ) -> List[Tuple[str, str, float]]:
        k = max(1, int(top_k))
        with self._lock:
            ntotal = int(self._index.ntotal)
            if ntotal == 0:
                return []
            q = np.array([list(query_vector)], dtype="float32")
            self._faiss.normalize_L2(q)
            scores, idxs = self._index.search(q, min(k, ntotal))
        out: List[Tuple[str, str, float]] = []
        for score, iid in zip(scores[0].tolist(), idxs[0].tolist()):
            if int(iid) < 0:
                continue
            iid_i = int(iid)
            ext = self._ext_by_id.get(iid_i, str(iid_i))
            text = self._text_by_id.get(iid_i, "")
            out.append((ext, text, float(score)))
        return out

    def close(self) -> None:
        with self._lock:
            self._index.reset()
            self._text_by_id.clear()
            self._ext_by_id.clear()
