"""OpenAI-style tool schemas for vector_store."""

from __future__ import annotations

from typing import Any, Dict

VECTOR_SEARCH_SCHEMA: Dict[str, Any] = {
    "name": "vector_memory_search",
    "description": (
        "Search the local vector memory by semantic similarity. "
        "Returns short text excerpts with scores."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language query."},
            "top_k": {
                "type": "integer",
                "description": "Max hits (default from config, max 20).",
            },
        },
        "required": ["query"],
    },
}
