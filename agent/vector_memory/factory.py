"""Select a vector backend from ``memory.vector_store`` config."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from agent.vector_memory.embedder import TextEmbedder
from agent.vector_memory.protocol import VectorStoreBackend

logger = logging.getLogger(__name__)


def _resolve_path(hermes_home: Path, rel: str) -> Path:
    p = (rel or "").strip()
    if not p:
        return hermes_home / "vector"
    out = Path(p)
    if out.is_absolute():
        return out
    return (hermes_home / out).resolve()


def build_vector_backend(
    vs: dict[str, Any],
    embedder: TextEmbedder,
    hermes_home: Path,
) -> Optional[VectorStoreBackend]:
    """Return None if type unknown or required deps missing."""
    t = (vs.get("type") or "python").lower().strip()
    if t == "python":
        from agent.vector_memory.python_backend import PythonVectorBackend

        return PythonVectorBackend(
            max_docs=int(vs.get("max_docs", 5000)),
            ttl_seconds=int(vs.get("ttl_seconds", 0)),
        )
    if t == "faiss":
        try:
            from agent.vector_memory.faiss_backend import FAISSVectorBackend

            return FAISSVectorBackend(embedder.dimensions)
        except Exception as e:
            logger.warning("FAISS backend unavailable (%s); falling back to python", e)
            from agent.vector_memory.python_backend import PythonVectorBackend

            return PythonVectorBackend(
                max_docs=int(vs.get("max_docs", 5000)),
                ttl_seconds=int(vs.get("ttl_seconds", 0)),
            )
    if t == "chroma":
        try:
            from agent.vector_memory.chroma_backend import ChromaVectorBackend

            persist = _resolve_path(hermes_home, str(vs.get("path", "vector/chroma")))
            persist.mkdir(parents=True, exist_ok=True)
            name = str(vs.get("collection") or "hermes_vectors")
            return ChromaVectorBackend(name, persist)
        except Exception as e:
            logger.warning("Chroma backend unavailable: %s", e)
            return None
    if t == "qdrant":
        try:
            from agent.vector_memory.qdrant_backend import QdrantVectorBackend

            return QdrantVectorBackend(
                collection=str(vs.get("collection") or "hermes_vectors"),
                path=str(vs.get("path") or ""),
                url=str(vs.get("url") or ""),
                api_key=str(vs.get("api_key") or ""),
                dim=embedder.dimensions,
            )
        except Exception as e:
            logger.warning("Qdrant backend unavailable: %s", e)
            return None
    if t in ("pinecone", "pinecone-serverless"):
        try:
            from agent.vector_memory.pinecone_backend import PineconeVectorBackend

            return PineconeVectorBackend(
                index_name=str(vs.get("collection") or vs.get("index") or "hermes"),
                api_key=str(vs.get("api_key") or ""),
                dim=embedder.dimensions,
            )
        except Exception as e:
            logger.warning("Pinecone backend unavailable: %s", e)
            return None
    logger.warning("Unknown memory.vector_store.type %r", t)
    return None
