# vector_hybrid memory provider

Select with `memory.provider: vector_hybrid` in `config.yaml`.

Configure backends and embeddings under `memory.vector_hybrid` (see defaults in `hermes_cli/config.py`).

- Only one external memory provider may be active; use this provider alone, or enable `honcho_bridge` for optional dialectic snippets (requires Honcho credentials).
- Optional extras: `hermes-agent[vector-qdrant]`, `hermes-agent[vector-pinecone]`.
