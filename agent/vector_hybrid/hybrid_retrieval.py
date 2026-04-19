"""Fuse dense vector hits with keyword-cache (pseudo-FTS) scores."""

from __future__ import annotations

import re
from typing import Dict, List, Sequence

from agent.vector_hybrid.types import KeywordHit, VectorHit


def _norm_scores(raw: Sequence[float]) -> List[float]:
    if not raw:
        return []
    lo, hi = min(raw), max(raw)
    if hi <= lo:
        return [1.0 for _ in raw]
    return [(x - lo) / (hi - lo) for x in raw]


def _tokenize(q: str) -> set[str]:
    return {t for t in re.split(r"\W+", q.lower()) if len(t) > 1}


def keyword_score(query: str, text: str) -> float:
    """Cheap overlap score in [0, 1]."""
    qtok = _tokenize(query)
    if not qtok:
        return 0.0
    ttok = _tokenize(text)
    if not ttok:
        return 0.0
    inter = len(qtok & ttok)
    return inter / max(len(qtok), 1)


def fuse_hybrid(
    query: str,
    vec_hits: List[VectorHit],
    kw_hits: List[KeywordHit],
    *,
    alpha: float,
    max_chunks: int,
) -> List[tuple[str, float, str]]:
    """Blend vector and keyword lists; return (id, fused_score, text).

    alpha weights dense similarity vs keyword score after normalization.
    """
    scores: Dict[str, tuple[float, str]] = {}
    vec_ids = [h[0] for h in vec_hits]
    vec_vals = [h[1] for h in vec_hits]
    vec_norm = _norm_scores(vec_vals)
    for i, hid in enumerate(vec_ids):
        payload = vec_hits[i][2]
        text = str(payload.get("text", ""))
        scores[hid] = (alpha * vec_norm[i], text)

    kw_vals = [h[2] for h in kw_hits]
    kw_norm = _norm_scores(kw_vals)
    for i, kh in enumerate(kw_hits):
        hid, txt, _ = kh
        dense = scores.get(hid, (0.0, txt))[0]
        merged = dense + (1.0 - alpha) * kw_norm[i]
        scores[hid] = (merged, txt or scores.get(hid, ("", txt))[1])

    ranked = sorted(scores.items(), key=lambda x: -x[1][0])
    out: List[tuple[str, float, str]] = []
    for hid, (sc, txt) in ranked[:max_chunks]:
        out.append((hid, sc, txt))
    return out
