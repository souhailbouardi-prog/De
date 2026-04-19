"""No-op vector backend — queries return empty (keyword path still works)."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from agent.vector_hybrid.types import VectorHit


class NoOpMemoryBackend:
    async def upsert(
        self,
        ids: Sequence[str],
        vectors: Sequence[Sequence[float]],
        payloads: Sequence[Dict[str, Any]],
    ) -> None:
        return

    async def query_vector(
        self, vector: Sequence[float], top_k: int
    ) -> List[VectorHit]:
        return []

    async def delete(self, ids: Sequence[str]) -> None:
        return
