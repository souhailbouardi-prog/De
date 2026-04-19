"""Bundled vector memory provider (local semantic index)."""

from __future__ import annotations

from typing import Any

from plugins.memory.vector_store.provider import VectorStoreMemoryProvider


def register(ctx: Any) -> None:
    ctx.register_memory_provider(VectorStoreMemoryProvider())
