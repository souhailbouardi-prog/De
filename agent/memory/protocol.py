"""MemoryProvider protocol — the contract for long-term memory integrations.

Lifecycle (enforced by ``MemoryProviderRegistry``):

    is_available()
        │
    initialize(session_key, config)
        │
        ├─ capabilities()             ← once after init (tool surface, gating)
        │
        ├─ [per turn]
        │   ├─ enrich_turn(msg, msgs) ← pre-API-call (parallel, ≤5s)
        │   ├─ on_memory_write(...)   ← memory tool routing (daemon)
        │   └─ on_turn_complete(...)  ← post-turn sync (daemon)
        │
        ├─ on_compress(msgs, n)       ← before context compression
        │                                (non-daemon, joined)
        │
        └─ shutdown()                 ← atexit or explicit teardown
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class MemoryProvider(Protocol):
    """Contract for long-term memory integrations.

    Every method MUST degrade gracefully when the backing service is
    unavailable — return ``None``, empty string, or silently no-op
    rather than raise.  The registry wraps each call in a try/except
    as a safety net, but providers should handle their own errors first.
    """

    # ── Identity ───────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Short, unique identifier (e.g. ``"honcho"``, ``"byterover"``).

        Used as:

        * Key into the ``config.yaml`` provider section
          (``config.get(provider.name, {})``)
        * Label in logs and sanitized context fences
        * Deduplication key (two providers with the same name are
          rejected)
        """
        ...

    # ── Gate ───────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Return ``True`` if this provider is installed and minimally
        configured.

        Called once before ``initialize()``.  If ``False``, the provider
        is skipped entirely — no other methods will be called.

        **Contract:**

        * Must be cheap: no network I/O, no subprocess.  Target <100ms.
        * May check: env var exists, binary on PATH, config file present.
        """
        ...

    # ── Lifecycle ──────────────────────────────────────────────────────

    def initialize(self, session_key: str, config: Dict[str, Any]) -> None:
        """One-time setup for this agent session.

        Args:
            session_key: Opaque session identifier (e.g.
                ``"cli_20260330_abc"``, ``"telegram:123456"``).
                Providers may use this directly or resolve their own
                session identifier internally.
            config: The provider's subtree from ``config.yaml``
                (e.g. ``config.get("honcho", {})``).  May be empty if
                not configured — providers may load their own config
                from separate sources.

        Called after ``is_available()`` returns ``True``.  May create
        connections, prefetch data, register tool handler context, start
        background threads, etc.

        **Threading:** Called on the main thread, sequentially per
        provider.

        Raises on fatal failure — the registry catches the exception,
        logs a warning, and drops this provider.
        """
        ...

    def shutdown(self) -> None:
        """Clean up on session end or process exit.

        Flush pending writes, close connections, join background threads.

        **Contract:**

        * Must complete within 15 seconds.
        * Must be idempotent (may be called more than once).
        * Must never raise (log and swallow).
        * Must not shut down shared or borrowed resources (e.g. a
          gateway-shared session manager passed via constructor).
        """
        ...

    # ── Configuration ──────────────────────────────────────────────────

    def capabilities(self) -> Dict[str, Any]:
        """Return provider capabilities.  Called once after
        ``initialize()``.  Return value is frozen for the session.

        Optional keys (all have defaults applied by the registry):

        * ``tool_names``: ``set[str]`` — tool names this provider
          contributes to the agent's active tool surface.  Tools must
          be pre-registered in the global ``ToolRegistry``.
          Default: ``set()``.
        * ``suppresses_local_writes``: ``bool | dict[str, bool]`` —
          when ``True``, local ``MEMORY.md`` / ``USER.md`` writes are
          skipped entirely.  When a ``dict``, per-target suppression
          is applied (e.g. ``{"memory": True, "user": False}``).
          Default: ``False``.
        """
        ...

    # ── Per-turn enrichment ────────────────────────────────────────────

    def enrich_turn(self, user_message: str,
                    messages: List[Dict[str, Any]]) -> Optional[str]:
        """Retrieve context for the current turn.

        Called before each LLM API call.  The returned text is injected
        into the **user message** at API-call time only — it is NOT
        persisted to session history, keeping the canonical message
        clean for replay.

        Args:
            user_message: The original user message (clean, no memory
                context prefixes or fences).
            messages: Full conversation history (**read-only** — shared
                across providers, not copied).  Content may be ``str``
                or ``list[dict]`` (multipart).  Providers must not
                modify this list.

        Returns:
            Context string to inject, or ``None`` to skip this turn.

        **Threading:** Called in parallel across providers via
        ``ThreadPoolExecutor`` with a shared deadline of 5 seconds.
        Providers that exceed the deadline have their result dropped.

        **Provider decides internally:**

        * Whether to inject on this turn (every turn? every Nth?
          first turn only?)
        * What to query (use ``user_message`` and ``messages`` to
          determine relevance)
        * How much to return (provider manages its own token budget)
        """
        ...

    # ── Memory tool routing ────────────────────────────────────────────

    def on_memory_write(self, action: str, target: str,
                        content: Optional[str],
                        old_text: Optional[str] = None) -> None:
        """Hook for ``memory`` tool add / replace / remove operations.

        Called when the LLM invokes the memory tool, **regardless** of
        whether the local ``MemoryStore`` write was performed or
        suppressed.  Providers must not assume the local write happened.

        Args:
            action:   ``"add"``, ``"replace"``, or ``"remove"``
            target:   ``"user"`` or ``"memory"``
            content:  The content being written (``None`` for remove).
            old_text: The text being replaced or removed (``None`` for
                add).  Available for providers that need to track what
                changed.

        **Threading:** Called on a dedicated daemon thread per provider.
        Fire-and-forget — the agent does NOT wait for completion.
        """
        ...

    # ── Post-turn sync ─────────────────────────────────────────────────

    def on_turn_complete(self, user_message: str,
                         assistant_response: str) -> None:
        """Post-turn write-back.

        Called after the agent produces a final response (not after each
        tool-calling iteration — only once per user turn).

        Args:
            user_message:       The **original** user message (not the
                                enriched version with memory context).
            assistant_response: The agent's final text response
                                (think blocks stripped).

        **Threading:** Called on a dedicated daemon thread per provider.
        Fire-and-forget — the agent does NOT wait for completion.

        Only called on **successful** turn completion.  NOT called when
        the turn is interrupted or fails.
        """
        ...

    # ── Pre-compression flush ──────────────────────────────────────────

    def on_compress(self, messages: List[Dict[str, Any]],
                    compression_count: int) -> None:
        """Pre-compression flush — last chance to extract insights.

        Called by the context compressor **before** middle turns are
        summarized and discarded.  This is the provider's opportunity
        to persist anything valuable from the conversation that will
        be permanently lost.

        Args:
            messages: Full session snapshot, normalized to
                ``{"role": str, "content": str}`` (plain text, no
                multipart).  The provider decides which segments are
                relevant.
            compression_count: How many times compression has run this
                session (0-indexed).

        **Threading:** Called on a dedicated **non-daemon** thread per
        provider, with ``join(timeout=120s)``.  The compressor waits
        for providers to finish before discarding messages.  This is
        the **only** hook with this guarantee — all other write hooks
        use daemon threads.
        """
        ...
