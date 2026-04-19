"""Lazy text embedders: deterministic hash fallback or sentence-transformers."""

from __future__ import annotations

import hashlib
import logging
import math
from abc import ABC, abstractmethod
from typing import List, Sequence

logger = logging.getLogger(__name__)


class TextEmbedder(ABC):
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector length produced by encode()."""

    @abstractmethod
    def encode(self, texts: Sequence[str]) -> List[List[float]]:
        """Return one L2-normalized vector per input text."""


class HashTextEmbedder(TextEmbedder):
    """Deterministic pseudo-embeddings (no extra deps). For tests and CI."""

    def __init__(self, dim: int = 64) -> None:
        self._dim = max(8, int(dim))

    @property
    def dimensions(self) -> int:
        return self._dim

    def encode(self, texts: Sequence[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8", errors="replace")).digest()
            raw = []
            i = 0
            while len(raw) < self._dim:
                raw.append(((h[i % len(h)] - 128) / 128.0))
                i += 1
            n = math.sqrt(sum(x * x for x in raw)) or 1.0
            out.append([x / n for x in raw])
        return out


class SentenceTransformerEmbedder(TextEmbedder):
    """sentence-transformers backend (optional dependency)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(model_name)
        self._dim = int(self._model.get_sentence_embedding_dimension())

    @property
    def dimensions(self) -> int:
        return self._dim

    def encode(self, texts: Sequence[str]) -> List[List[float]]:
        import numpy as np  # type: ignore

        arr = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [row.astype(float).tolist() for row in np.atleast_2d(arr)]


def build_embedder(vs_cfg: dict) -> TextEmbedder:
    model = (vs_cfg.get("embedding_model") or "").strip()
    dim = int(vs_cfg.get("embed_dim", 64))
    if not model:
        return HashTextEmbedder(dim=dim)
    try:
        return SentenceTransformerEmbedder(model)
    except Exception as e:
        logger.warning(
            "sentence-transformers embedder unavailable (%s); using hash fallback",
            e,
        )
        return HashTextEmbedder(dim=dim)
