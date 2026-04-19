"""ACP auth helpers — detect the currently configured Hermes provider."""

from __future__ import annotations
from typing import Optional


def detect_provider() -> Optional[str]:
    """Resolve the active Hermes runtime provider, or None if unavailable."""
    try:
        from hermes_cli.runtime_provider import resolve_runtime_provider
    except ImportError:
        return None

    try:
        runtime = resolve_runtime_provider()
        if not isinstance(runtime, dict):
            return None

        api_key = runtime.get("api_key")
        provider = runtime.get("provider")

        if all(isinstance(x, str) and x.strip() for x in (api_key, provider)):
            return provider.strip().lower()

    except Exception:
        # Optional: log error here instead of silently ignoring
        return None

    return None


def has_provider() -> bool:
    """Return True if Hermes can resolve any runtime provider credentials."""
    return detect_provider() is not None
