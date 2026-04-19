"""MemoryProviderRegistry — orchestrates multiple memory providers.

Handles parallel execution, error isolation, deadline enforcement, and
lifecycle management so that ``AIAgent`` has a single, thin integration
surface instead of per-provider wiring.
"""

import atexit
import logging
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from agent.memory.protocol import MemoryProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deadline constants (seconds)
# ---------------------------------------------------------------------------

ENRICH_TURN_DEADLINE = 5.0
"""Max wall-clock time for all providers to return per-turn context
(parallel).  Tight because it blocks the LLM API call."""

COMPRESS_DEADLINE = 120.0
"""Per-provider deadline for pre-compression flush.  May involve an
auxiliary LLM call + external write, so needs room."""

SHUTDOWN_DEADLINE = 15.0
"""Per-provider deadline for shutdown.  Enforced by the registry —
providers that exceed this are logged and abandoned."""


class MemoryProviderRegistry:
    """Manages memory provider lifecycle and dispatches hooks.

    Owned by ``AIAgent`` — one instance per session.  NOT a singleton:
    gateway creates a fresh registry per incoming message, matching
    ``AIAgent``'s stateless-per-message pattern.

    Thread safety: all public methods are safe to call from any thread.
    Internal state is guarded by ``_lock``.  Provider methods are called
    outside the lock to avoid deadlocks.
    """

    def __init__(self) -> None:
        self._providers: List[MemoryProvider] = []
        self._lock = threading.Lock()
        self._initialized = False
        self._shutdown_called = False
        self._atexit_registered = False
        # Capabilities (frozen after init)
        self._provider_tool_names: frozenset = frozenset()
        self._suppress_memory: bool = False
        self._suppress_user: bool = False

    # ── Registration ───────────────────────────────────────────────────

    def register(self, provider: MemoryProvider) -> None:
        """Add a provider before initialization.

        Raises ``ValueError`` if a provider with the same name is
        already registered, or ``RuntimeError`` if the registry is
        already initialized.
        """
        with self._lock:
            if self._initialized:
                raise RuntimeError(
                    "Cannot register providers after initialize_all()"
                )
            names = {p.name for p in self._providers}
            if provider.name in names:
                raise ValueError(
                    f"Duplicate memory provider name: {provider.name!r}"
                )
            self._providers.append(provider)

    # ── Initialization ─────────────────────────────────────────────────

    def initialize_all(
        self, session_key: str, config: Dict[str, Any],
    ) -> None:
        """Initialize all registered providers, dropping unavailable
        or failed ones.

        Args:
            session_key: Passed to each provider's ``initialize()``.
            config: Full agent config dict.  Each provider receives
                ``config.get(provider.name, {})``.
        """
        with self._lock:
            if self._initialized:
                logger.debug("initialize_all() called more than once, skipping")
                return
            providers_snapshot = list(self._providers)

        active: List[MemoryProvider] = []
        tool_names: set = set()
        suppress_memory = False
        suppress_user = False

        for p in providers_snapshot:
            try:
                if not p.is_available():
                    logger.debug(
                        "Memory provider '%s' not available, skipping",
                        p.name,
                    )
                    continue

                provider_config = config.get(p.name, {})
                if not isinstance(provider_config, dict):
                    provider_config = {}
                p.initialize(session_key, provider_config)

                # Read capabilities
                caps = p.capabilities()
                tool_names.update(caps.get("tool_names", set()))

                suppress = caps.get("suppresses_local_writes", False)
                if isinstance(suppress, bool) and suppress:
                    suppress_memory = True
                    suppress_user = True
                elif isinstance(suppress, dict):
                    if suppress.get("memory", False):
                        suppress_memory = True
                    if suppress.get("user", False):
                        suppress_user = True

                active.append(p)
                logger.info("Memory provider '%s' initialized", p.name)
            except Exception:
                logger.warning(
                    "Memory provider '%s' init failed, skipping",
                    p.name,
                    exc_info=True,
                )

        with self._lock:
            self._providers = active
            self._provider_tool_names = frozenset(tool_names)
            self._suppress_memory = suppress_memory
            self._suppress_user = suppress_user
            self._initialized = True

        self._register_atexit()

    # ── Properties ─────────────────────────────────────────────────────

    @property
    def active_providers(self) -> List[MemoryProvider]:
        """Snapshot of currently active providers."""
        with self._lock:
            return list(self._providers)

    @property
    def provider_tool_names(self) -> frozenset:
        """Tool names contributed by active providers."""
        with self._lock:
            return self._provider_tool_names

    def suppresses_local_writes_for(self, target: str) -> bool:
        """Return ``True`` if local writes should be suppressed for
        the given target (``"memory"`` or ``"user"``).
        """
        with self._lock:
            if target == "memory":
                return self._suppress_memory
            if target == "user":
                return self._suppress_user
            return False

    # ── Per-turn enrichment ────────────────────────────────────────────

    def enrich_turn(
        self, user_message: str, messages: List[Dict[str, Any]],
    ) -> List[Tuple[str, str]]:
        """Query all providers for per-turn context (parallel).

        Returns a list of ``(label, context_text)`` tuples suitable
        for passing to ``inject_memory_context()`` or
        ``build_memory_context_block()``.

        Providers that timeout or fail are silently skipped.

        Note: the method may block slightly beyond the deadline while
        the thread pool shuts down.  Provider results are only
        *collected* within the deadline; slow providers' results are
        discarded but their threads may still be running briefly.
        """
        with self._lock:
            if not self._initialized:
                return []
            providers = list(self._providers)

        if not providers:
            return []

        results: List[Tuple[str, str]] = []

        with ThreadPoolExecutor(max_workers=max(1, len(providers))) as pool:
            futures = {
                pool.submit(p.enrich_turn, user_message, messages): p
                for p in providers
            }
            try:
                done = as_completed(
                    futures, timeout=ENRICH_TURN_DEADLINE,
                )
                for future in done:
                    provider = futures[future]
                    try:
                        ctx = future.result(timeout=0)
                        if ctx:
                            results.append(
                                (f"{provider.name} memory", ctx)
                            )
                    except Exception:
                        logger.debug(
                            "Provider '%s' enrich_turn failed",
                            provider.name,
                            exc_info=True,
                        )
            except TimeoutError:
                logger.debug(
                    "Turn enrichment timed out after %.1fs",
                    ENRICH_TURN_DEADLINE,
                )

        return results

    # ── Memory write routing ───────────────────────────────────────────

    def on_memory_write(
        self, action: str, target: str,
        content: Optional[str], old_text: Optional[str] = None,
    ) -> None:
        """Dispatch a memory write to all providers (fire-and-forget).

        Each provider is called on a separate daemon thread.  The agent
        does NOT wait for completion.
        """
        for p in self.active_providers:
            threading.Thread(
                target=self._safe_call,
                args=(p.on_memory_write, action, target, content, old_text),
                name=f"mem-write-{p.name}",
                daemon=True,
            ).start()

    # ── Post-turn sync ─────────────────────────────────────────────────

    def on_turn_complete(
        self, user_message: str, assistant_response: str,
    ) -> None:
        """Dispatch post-turn hooks to all providers (fire-and-forget).

        Each provider is called on a separate daemon thread.
        """
        for p in self.active_providers:
            threading.Thread(
                target=self._safe_call,
                args=(p.on_turn_complete, user_message, assistant_response),
                name=f"mem-turn-{p.name}",
                daemon=True,
            ).start()

    # ── Pre-compression flush ──────────────────────────────────────────

    def on_compress(
        self, messages: List[Dict[str, Any]], compression_count: int,
    ) -> None:
        """Flush all providers before compression.

        Uses **non-daemon** threads with ``join()`` so that providers
        can complete even if the process is exiting.  The compressor
        waits up to ``COMPRESS_DEADLINE`` per provider before proceeding.
        """
        threads: List[threading.Thread] = []
        for p in self.active_providers:
            t = threading.Thread(
                target=self._safe_call,
                args=(p.on_compress, messages, compression_count),
                name=f"mem-compress-{p.name}",
                daemon=False,
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=COMPRESS_DEADLINE)
            if t.is_alive():
                logger.warning(
                    "Memory provider compress thread '%s' exceeded "
                    "deadline (%.0fs), proceeding without it",
                    t.name,
                    COMPRESS_DEADLINE,
                )

    # ── Shutdown ───────────────────────────────────────────────────────

    def shutdown_all(self) -> None:
        """Shut down all providers with enforced deadline.

        Each provider gets ``SHUTDOWN_DEADLINE`` seconds to complete.
        Providers that exceed the deadline are logged and abandoned.

        Idempotent — safe to call multiple times (atexit + explicit).
        """
        with self._lock:
            if self._shutdown_called:
                return
            self._shutdown_called = True
            providers = list(self._providers)

        threads: List[threading.Thread] = []
        for p in providers:
            t = threading.Thread(
                target=self._safe_call,
                args=(p.shutdown,),
                name=f"mem-shutdown-{p.name}",
                daemon=True,
            )
            t.start()
            threads.append((t, p))

        for t, p in threads:
            t.join(timeout=SHUTDOWN_DEADLINE)
            if t.is_alive():
                logger.warning(
                    "Memory provider '%s' shutdown exceeded %ds deadline",
                    p.name,
                    SHUTDOWN_DEADLINE,
                )

    # ── Internals ──────────────────────────────────────────────────────

    def _register_atexit(self) -> None:
        """Register a process-exit hook to shut down providers.

        Uses a weak reference to avoid preventing garbage collection
        of the registry (and by extension, the AIAgent that owns it).
        """
        if self._atexit_registered:
            return
        self._atexit_registered = True

        ref = weakref.ref(self)

        def _on_exit():
            registry = ref()
            if registry is not None:
                registry.shutdown_all()

        atexit.register(_on_exit)

    @staticmethod
    def _safe_call(fn, *args) -> None:
        """Call *fn* with *args*, swallowing all exceptions."""
        try:
            fn(*args)
        except Exception:
            logger.debug(
                "Memory provider call %s failed",
                getattr(fn, "__qualname__", fn),
                exc_info=True,
            )
