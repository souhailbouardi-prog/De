"""Optional Honcho dialectic snippet for VectorHybrid prefetch (composition)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HonchoDialecticBridge:
    """Best-effort dialectic line via HonchoSessionManager (same SDK as honcho plugin)."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled
        self._manager = None
        self._session_key = ""
        self._logged_skip = False

    def setup(self, session_id: str, **kwargs: Any) -> None:
        if not self._enabled:
            return
        try:
            from plugins.memory.honcho.client import HonchoClientConfig, get_honcho_client
            from plugins.memory.honcho.session import HonchoSessionManager

            cfg = HonchoClientConfig.from_global_config()
            if not cfg.enabled or not (cfg.api_key or cfg.base_url):
                return
            client = get_honcho_client(cfg)
            self._manager = HonchoSessionManager(
                honcho=client,
                config=cfg,
                context_tokens=cfg.context_tokens,
            )
            title = kwargs.get("session_title")
            gsk = kwargs.get("gateway_session_key")
            self._session_key = (
                cfg.resolve_session_name(
                    session_title=title,
                    session_id=session_id,
                    gateway_session_key=gsk,
                )
                or session_id
                or "hermes-default"
            )
            self._manager.get_or_create(self._session_key)
        except Exception as e:
            if not self._logged_skip:
                logger.debug("Honcho dialectic bridge unavailable: %s", e)
                self._logged_skip = True

    def dialectic_nudge(self, query: str, *, max_chars: int = 600) -> str:
        if not self._enabled or not self._manager or not self._session_key:
            return ""
        q = (query or "").strip()
        if not q:
            return ""
        try:
            out = self._manager.dialectic_query(self._session_key, q[:2000])
            if not out:
                return ""
            out = out.strip()
            if len(out) > max_chars:
                out = out[:max_chars].rsplit(" ", 1)[0] + " …"
            return out
        except Exception as e:
            logger.debug("Dialectic nudge failed (non-fatal): %s", e)
            return ""
