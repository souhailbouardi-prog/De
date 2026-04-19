"""Pluggable vector memory backends (local + optional third-party stores)."""

from __future__ import annotations

from agent.vector_memory.embedder import TextEmbedder, build_embedder
from agent.vector_memory.factory import build_vector_backend
from agent.vector_memory.protocol import VectorStoreBackend

__all__ = [
    "TextEmbedder",
    "build_embedder",
    "build_vector_backend",
    "VectorStoreBackend",
]
