"""Helpers for optional cheap-vs-strong model routing."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from utils import is_truthy_value

_COMPLEX_KEYWORDS = {
    "debug",
    "debugging",
    "implement",
    "implementation",
    "refactor",
    "patch",
    "traceback",
    "stacktrace",
    "exception",
    "error",
    "analyze",
    "analysis",
    "investigate",
    "architecture",
    "design",
    "compare",
    "benchmark",
    "optimize",
    "optimise",
    "review",
    "terminal",
    "shell",
    "tool",
    "tools",
    "pytest",
    "test",
    "tests",
    "plan",
    "planning",
    "delegate",
    "subagent",
    "cron",
    "docker",
    "kubernetes",
}

_URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)


def _coerce_bool(value: Any, default: bool = False) -> bool:
    return is_truthy_value(value, default=default)


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def choose_cheap_model_route(user_message: str, routing_config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the configured cheap-model route when a message looks simple.

    Conservative by design: if the message has signs of code/tool/debugging/
    long-form work, keep the primary model.
    """
    cfg = routing_config or {}
    if not _coerce_bool(cfg.get("enabled"), False):
        return None

    cheap_model = cfg.get("cheap_model") or {}
    if not isinstance(cheap_model, dict):
        return None
    provider = str(cheap_model.get("provider") or "").strip().lower()
    model = str(cheap_model.get("model") or "").strip()
    if not provider or not model:
        return None

    text = (user_message or "").strip()
    if not text:
        return None

    max_chars = _coerce_int(cfg.get("max_simple_chars"), 160)
    max_words = _coerce_int(cfg.get("max_simple_words"), 28)

    if len(text) > max_chars:
        return None
    if len(text.split()) > max_words:
        return None
    if text.count("\n") > 1:
        return None
    if "```" in text or "`" in text:
        return None
    if _URL_RE.search(text):
        return None

    lowered = text.lower()
    words = {token.strip(".,:;!?()[]{}\"'`") for token in lowered.split()}
    if words & _COMPLEX_KEYWORDS:
        return None

    route = dict(cheap_model)
    route["provider"] = provider
    route["model"] = model
    route["routing_reason"] = "simple_turn"
    return route


def resolve_turn_route(user_message: str, routing_config: Optional[Dict[str, Any]], primary: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve the effective model/runtime for one turn.

    Returns a dict with model/runtime/signature/label fields.
    """
    route = choose_cheap_model_route(user_message, routing_config)
    if not route:
        return {
            "model": primary.get("model"),
            "runtime": {
                "api_key": primary.get("api_key"),
                "base_url": primary.get("base_url"),
                "provider": primary.get("provider"),
                "api_mode": primary.get("api_mode"),
                "command": primary.get("command"),
                "args": list(primary.get("args") or []),
                "credential_pool": primary.get("credential_pool"),
            },
            "label": None,
            "signature": (
                primary.get("model"),
                primary.get("provider"),
                primary.get("base_url"),
                primary.get("api_mode"),
                primary.get("command"),
                tuple(primary.get("args") or ()),
            ),
        }

    from hermes_cli.runtime_provider import resolve_runtime_provider

    explicit_api_key = None
    api_key_env = str(route.get("api_key_env") or "").strip()
    if api_key_env:
        explicit_api_key = os.getenv(api_key_env) or None

    try:
        runtime = resolve_runtime_provider(
            requested=route.get("provider"),
            explicit_api_key=explicit_api_key,
            explicit_base_url=route.get("base_url"),
        )
    except Exception:
        return {
            "model": primary.get("model"),
            "runtime": {
                "api_key": primary.get("api_key"),
                "base_url": primary.get("base_url"),
                "provider": primary.get("provider"),
                "api_mode": primary.get("api_mode"),
                "command": primary.get("command"),
                "args": list(primary.get("args") or []),
                "credential_pool": primary.get("credential_pool"),
            },
            "label": None,
            "signature": (
                primary.get("model"),
                primary.get("provider"),
                primary.get("base_url"),
                primary.get("api_mode"),
                primary.get("command"),
                tuple(primary.get("args") or ()),
            ),
        }

    return {
        "model": route.get("model"),
        "runtime": {
            "api_key": runtime.get("api_key"),
            "base_url": runtime.get("base_url"),
            "provider": runtime.get("provider"),
            "api_mode": runtime.get("api_mode"),
            "command": runtime.get("command"),
            "args": list(runtime.get("args") or []),
            "credential_pool": runtime.get("credential_pool"),
        },
        "label": f"smart route → {route.get('model')} ({runtime.get('provider')})",
        "signature": (
            route.get("model"),
            runtime.get("provider"),
            runtime.get("base_url"),
            runtime.get("api_mode"),
            runtime.get("command"),
            tuple(runtime.get("args") or ()),
        ),
    }


# =============================================================================
# Match-based model routing (``model.routes``)
# =============================================================================
#
# A generic layer that lets callers pick a model + provider bundle based on a
# context dict describing the turn (``platform``, ``source_kind``, etc.). The
# router iterates ``model.routes`` — a list of ``{match: {...}, model,
# provider, api_key, base_url, ...}`` entries — and applies the first route
# whose ``match`` predicates are all satisfied by the context.
#
# Two legacy shorthand forms are supported for backwards compatibility and
# config ergonomics (the ``routes`` list is canonical; shims synthesize
# entries from them at match time):
#
#   model.platforms.<name>:       routes by platform (existing shorthand)
#   model.by_source.<kind>:       routes by source identity (owner / hub_peer
#                                 / stranger / cron)
#
# This replaces two separate hooks (platform-only + source-only) with a
# single generic matcher, so ``_resolve_session_agent_runtime`` has one hook
# point instead of two.

SOURCE_KIND_OWNER = "owner"
SOURCE_KIND_HUB_PEER = "hub_peer"
SOURCE_KIND_STRANGER = "stranger"
SOURCE_KIND_CRON = "cron"
KNOWN_SOURCE_KINDS = frozenset({
    SOURCE_KIND_OWNER,
    SOURCE_KIND_HUB_PEER,
    SOURCE_KIND_STRANGER,
    SOURCE_KIND_CRON,
})

_OVERRIDE_RUNTIME_KEYS = ("api_key", "base_url", "provider", "api_mode", "command", "args")


def _normalize_routes(model_config: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect the effective ordered route list from ``model_config``.

    Precedence (first match wins during lookup):

    1. Explicit ``routes:`` list as declared in config.
    2. Legacy ``platforms.<name>`` entries (synthesized as
       ``{match: {platform: <name>}, ...}``).
    3. Legacy ``by_source.<kind>`` entries (synthesized as
       ``{match: {source_kind: <kind>}, ...}``).

    Legacy shorthand routes are appended AFTER explicit routes so that a new
    ``routes:`` block always takes priority over old shorthand configs on
    the same path. Explicit routes also dedupe old entries semantically —
    if both are set and an explicit route matches first, the legacy one is
    unreachable.
    """
    if not isinstance(model_config, dict):
        return []

    routes: List[Dict[str, Any]] = []

    explicit = model_config.get("routes")
    if isinstance(explicit, list):
        for item in explicit:
            if isinstance(item, dict) and isinstance(item.get("match"), dict):
                routes.append(item)

    platforms = model_config.get("platforms")
    if isinstance(platforms, dict):
        for name, override in platforms.items():
            if isinstance(override, str) and override:
                routes.append({"match": {"platform": str(name)}, "model": override})
            elif isinstance(override, dict) and override:
                routes.append({"match": {"platform": str(name)}, **override})

    by_source = model_config.get("by_source")
    if isinstance(by_source, dict):
        for kind, override in by_source.items():
            if isinstance(override, dict) and override:
                routes.append({"match": {"source_kind": str(kind)}, **override})

    return routes


def _route_matches(match_spec: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Return True when every key in ``match_spec`` equals the context value.

    Missing keys in ``context`` never match (empty context satisfies empty
    match only). String comparison is case-sensitive.
    """
    if not isinstance(match_spec, dict) or not match_spec:
        return False
    for key, expected in match_spec.items():
        actual = context.get(key)
        if actual is None:
            return False
        if str(actual) != str(expected):
            return False
    return True


def apply_route(
    model: str,
    runtime_kwargs: Dict[str, Any],
    model_config: Optional[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """Apply the first matching ``model.routes`` entry to ``(model, runtime_kwargs)``.

    ``context`` is a dict describing the turn. Current recognised keys:

    * ``platform``   — inbound platform string ("telegram", "hub", "cli", ...)
    * ``source_kind`` — ``"owner"`` / ``"hub_peer"`` / ``"stranger"`` /
                        ``"cron"`` as classified by the caller.

    Callers may add additional keys (e.g. ``user_id``); routes that don't
    reference them are unaffected.

    Each route entry has shape::

        {
          "match": { "platform": "hub", "source_kind": "stranger", ... },
          "model": "my-model",            # optional; preserves base when missing
          "provider": "custom",           # optional
          "api_key": "sk-...",
          "base_url": "https://...",
          "api_mode": "chat_completions",
          "command": [...],  "args": [...]
        }

    Partial overrides are supported — any field not set on the matched route
    keeps its base value. First match wins; no match leaves inputs unchanged.
    """
    if not context:
        return model, runtime_kwargs
    routes = _normalize_routes(model_config)
    if not routes:
        return model, runtime_kwargs

    for entry in routes:
        match_spec = entry.get("match")
        if not isinstance(match_spec, dict):
            continue
        if not _route_matches(match_spec, context):
            continue

        new_model = model
        new_runtime = dict(runtime_kwargs or {})
        applied = []

        if entry.get("model"):
            new_model = str(entry["model"])
            applied.append("model")
        for key in _OVERRIDE_RUNTIME_KEYS:
            val = entry.get(key)
            if val in (None, "", []):
                continue
            if key == "args":
                new_runtime[key] = list(val)
            else:
                new_runtime[key] = val
            applied.append(key)

        if applied:
            import logging
            logging.getLogger(__name__).info(
                "model.routes matched: context=%s fields=%s model=%s provider=%s",
                context, applied, new_model, new_runtime.get("provider"),
            )
        return new_model, new_runtime

    return model, runtime_kwargs
