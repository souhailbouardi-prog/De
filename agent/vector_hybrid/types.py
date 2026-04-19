"""Shared types for vector hybrid memory (dimension-agnostic vectors)."""

from __future__ import annotations

from typing import Any, List, Tuple

# (id, score, payload dict)
VectorHit = Tuple[str, float, dict[str, Any]]
# (id, text, keyword_score)
KeywordHit = Tuple[str, str, float]
