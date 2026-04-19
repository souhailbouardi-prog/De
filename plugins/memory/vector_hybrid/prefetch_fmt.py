"""Format hybrid recall block for system prompt injection."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.vector_hybrid import fuse_hybrid, keyword_score

from plugins.memory.vector_hybrid.honcho_bridge import HonchoDialecticBridge


def format_hybrid_prefetch(
    *,
    query: str,
    cfg: Dict[str, Any],
    vec_hits: List[tuple[str, float, dict[str, Any]]],
    kw_map: Dict[str, tuple[str, dict[str, Any]]],
    bridge: Optional[HonchoDialecticBridge],
) -> str:
    cap = int(cfg.get("prefetch_char_cap") or 3500)
    alpha = float(cfg.get("hybrid_alpha") or 0.65)
    fts_scope = (cfg.get("fts_scope") or "keyword_cache").strip()
    kw_hits: List[tuple[str, str, float]] = []
    if fts_scope != "none":
        for cid, (txt, _) in kw_map.items():
            sc = keyword_score(query, txt)
            if sc > 0.02:
                kw_hits.append((cid, txt, sc))
    fused = fuse_hybrid(query, vec_hits, kw_hits, alpha=alpha, max_chunks=12)
    lines = []
    for hid, _sc, txt in fused[:8]:
        snippet = (txt or "").strip().replace("\n", " ")
        if snippet:
            lines.append(f"- ({hid[:8]}…) {snippet[:320]}")
    block = "[vector_hybrid recall]\n" + "\n".join(lines) if lines else ""
    if bridge:
        nudge = bridge.dialectic_nudge(query)
        if nudge:
            block += ("\n\n[dialectic nudge]\n" + nudge)[: max(1, cap // 4)]
    if len(block) > cap:
        block = block[:cap].rsplit("\n", 1)[0] + "\n…"
    return block
