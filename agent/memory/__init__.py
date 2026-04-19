"""Memory provider protocol and registry for long-term memory integrations.

Provides a lifecycle contract for memory integrations (Honcho, ByteRover,
future providers) and a registry that orchestrates them with parallel
execution, error isolation, deadline enforcement, and context sanitization.

Usage::

    from agent.memory import MemoryProvider, MemoryProviderRegistry
    from agent.memory import inject_memory_context
"""

from agent.memory.protocol import MemoryProvider
from agent.memory.registry import (
    MemoryProviderRegistry,
    ENRICH_TURN_DEADLINE,
    COMPRESS_DEADLINE,
    SHUTDOWN_DEADLINE,
)
from agent.memory.context import (
    sanitize_context,
    build_memory_context_block,
    inject_memory_context,
)

__all__ = [
    "MemoryProvider",
    "MemoryProviderRegistry",
    "ENRICH_TURN_DEADLINE",
    "COMPRESS_DEADLINE",
    "SHUTDOWN_DEADLINE",
    "sanitize_context",
    "build_memory_context_block",
    "inject_memory_context",
]
