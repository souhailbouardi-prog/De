"""Vector hybrid memory plugin registration."""

from __future__ import annotations

from plugins.memory.vector_hybrid.provider import VectorHybridMemoryProvider


def register(ctx: object) -> None:
    ctx.register_memory_provider(VectorHybridMemoryProvider())
