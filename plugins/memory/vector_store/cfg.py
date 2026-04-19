"""Load ``memory.vector_store`` from the active Hermes config."""

from __future__ import annotations

from typing import List


def mem_vector_cfg() -> dict:
    try:
        from hermes_cli.config import load_config

        m = load_config().get("memory") or {}
        vs = m.get("vector_store")
        return dict(vs) if isinstance(vs, dict) else {}
    except Exception:
        return {}


def chunk_text(text: str, size: int) -> List[str]:
    t = text.strip()
    if not t:
        return []
    out: List[str] = []
    i = 0
    while i < len(t):
        out.append(t[i : i + size])
        i += size
    return out
