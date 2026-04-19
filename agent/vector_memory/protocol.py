"""Protocol for synchronous vector backends used by MemoryProvider.prefetch."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence, Tuple


class VectorStoreBackend(ABC):
    """Minimal sync vector index: upsert by id and similarity search."""

    @abstractmethod
    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        """Replace-or-insert rows (same length for all args)."""

    @abstractmethod
    def search(
        self, query_vector: Sequence[float], top_k: int
    ) -> List[Tuple[str, str, float]]:
        """Return list of (id, text, score) highest similarity first."""

    @abstractmethod
    def close(self) -> None:
        """Release native handles if any."""
