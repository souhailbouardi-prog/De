"""OpenAI-compatible embedding HTTP client with RPS guard and FTS fallback flag."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Sync embeddings; safe for MemoryProvider.prefetch (no asyncio required)."""

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self._model = (cfg.get("embedding_model") or "text-embedding-3-small").strip()
        base_env = cfg.get("embedding_api_base_env") or "OPENAI_API_BASE"
        key_env = cfg.get("embedding_api_key_env") or "OPENAI_API_KEY"
        self._base = os.environ.get(base_env, "").strip() or "https://api.openai.com/v1"
        self._key = os.environ.get(key_env, "").strip()
        self._rps = max(0.25, float(cfg.get("rate_limit_rps") or 4.0))
        self._fallback_seconds = float(cfg.get("fallback_fts_seconds") or 90.0)
        self._lock = threading.Lock()
        self._next_slot = 0.0
        self._fallback_until = 0.0

    def fts_fallback_active(self) -> bool:
        return time.monotonic() < self._fallback_until

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return empty list on failure (caller uses keyword / FTS-only path)."""
        if not texts:
            return []
        if not self._key:
            self._trigger_fallback("missing embedding API key")
            return []
        self._throttle()
        url = self._base.rstrip("/") + "/embeddings"
        body = json.dumps({"model": self._model, "input": texts}).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                self._trigger_fallback(f"embedding HTTP {e.code}")
            logger.warning("Embedding HTTP error: %s", e)
            return []
        except Exception as e:
            self._trigger_fallback(str(e))
            logger.warning("Embedding failed: %s", e)
            return []

        data = payload.get("data") or []
        out: List[List[float]] = []
        for item in sorted(data, key=lambda x: x.get("index", 0)):
            vec = item.get("embedding")
            if isinstance(vec, list):
                out.append([float(v) for v in vec])
        if len(out) != len(texts):
            logger.warning("Embedding payload length mismatch")
            return []
        return out

    def _throttle(self) -> None:
        gap = 1.0 / self._rps
        with self._lock:
            now = time.monotonic()
            if now < self._next_slot:
                time.sleep(self._next_slot - now)
            self._next_slot = max(self._next_slot, now) + gap

    def _trigger_fallback(self, reason: str) -> None:
        logger.info("Embedding FTS fallback: %s", reason)
        self._fallback_until = time.monotonic() + self._fallback_seconds
