"""Pure-Python cosine vector store (zero optional deps beyond stdlib)."""

from __future__ import annotations

import math
import threading
import time
from typing import Dict, List, Sequence, Tuple

from agent.vector_memory.protocol import VectorStoreBackend


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class PythonVectorBackend(VectorStoreBackend):
    """In-memory cosine similarity with FIFO cap and optional TTL."""

    def __init__(self, *, max_docs: int = 5000, ttl_seconds: int = 0) -> None:
        self._max = max(1, int(max_docs))
        self._ttl = max(0, int(ttl_seconds))
        self._lock = threading.Lock()
        self._order: List[str] = []
        self._rows: Dict[str, Tuple[str, List[float], float]] = {}

    def _evict_ttl_unlocked(self) -> None:
        if self._ttl <= 0:
            return
        cutoff = time.time() - self._ttl
        stale = [
            doc_id
            for doc_id in list(self._order)
            if self._rows.get(doc_id, ("", [], 0.0))[2] < cutoff
        ]
        for doc_id in stale:
            self._drop(doc_id)

    def _drop(self, doc_id: str) -> None:
        self._rows.pop(doc_id, None)
        try:
            self._order.remove(doc_id)
        except ValueError:
            pass

    def _fifo(self) -> None:
        while len(self._order) > self._max:
            oldest = self._order.pop(0)
            self._rows.pop(oldest, None)

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        now = time.time()
        with self._lock:
            self._evict_ttl_unlocked()
            for doc_id, text, vec in zip(ids, texts, vectors):
                if doc_id in self._rows:
                    try:
                        self._order.remove(doc_id)
                    except ValueError:
                        pass
                self._rows[doc_id] = (text, list(vec), now)
                self._order.append(doc_id)
            self._fifo()

    def search(
        self, query_vector: Sequence[float], top_k: int
    ) -> List[Tuple[str, str, float]]:
        q = list(query_vector)
        k = max(1, int(top_k))
        with self._lock:
            self._evict_ttl_unlocked()
            scored: List[Tuple[str, str, float]] = []
            for doc_id, (text, vec, _ts) in self._rows.items():
                scored.append((doc_id, text, _cosine(q, vec)))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:k]

    def close(self) -> None:
        with self._lock:
            self._rows.clear()
            self._order.clear()
