"""Byte-budget eviction for hybrid memory metadata records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List


def estimate_record_bytes(payload: dict[str, Any], text: str = "") -> int:
    """Rough payload size for eviction budgeting."""
    n = len(text.encode("utf-8"))
    pri = payload.get("priority")
    if pri is not None:
        n += 8
    la = payload.get("last_access_ts")
    if la is not None:
        n += 8
    return n + 64


def evict_by_policy(
    records: List[tuple[str, dict[str, Any], str]],
    *,
    policy: str,
    budget_bytes: int,
    now_ts: float | None = None,
) -> List[str]:
    """Return IDs to delete to stay within budget_bytes (lowest priority first).

    records: list of (id, payload, text_snippet)
    policy: fifo | ttl | honcho_priority
    """
    if budget_bytes <= 0 or not records:
        return []
    now = now_ts if now_ts is not None else datetime.now(timezone.utc).timestamp()
    sizes = [(rid, estimate_record_bytes(meta, txt), rid, meta) for rid, meta, txt in records]
    total = sum(s[1] for s in sizes)
    if total <= budget_bytes:
        return []

    to_remove: List[str] = []
    # Sort order: lower priority evicted first
    keyed: List[tuple[float, float, str]] = []
    for rid, sz, _, meta in sizes:
        pri = float(meta.get("priority", 0.5))
        if policy == "honcho_priority":
            sort_pri = pri  # higher priority keeps — evict low pri first
            keyed.append((sort_pri, -sz, rid))
        elif policy == "ttl":
            age = now - float(meta.get("created_ts", now))
            keyed.append((age, -sz, rid))  # oldest first
        else:  # fifo
            created = float(meta.get("created_ts", now))
            keyed.append((created, -sz, rid))  # smallest ts evicted first

    keyed.sort()
    over = total - budget_bytes
    acc = 0
    for _, _, rid in keyed:
        if acc >= over:
            break
        sz = next(s for s in sizes if s[2] == rid)[1]
        to_remove.append(rid)
        acc += sz
    return to_remove
