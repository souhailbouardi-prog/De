# Vector store memory provider

Pluggable semantic memory: **python** (pure in-process, default), **faiss**, **chroma**, **qdrant**, or **pinecone**.

## Enable

```yaml
memory:
  provider: vector_store
  vector_store:
    type: python
    prefetch_top_k: 5
    upsert_min_chars: 40
```

Optional embeddings (otherwise a deterministic hash embedding is used for development):

```yaml
    embedding_model: sentence-transformers/all-MiniLM-L6-v2
```

Install extras when needed:

- `pip install "hermes-agent[vector-faiss]"`
- `pip install "hermes-agent[vector-chroma]"`
- `pip install "hermes-agent[vector-qdrant]"`
- `pip install "hermes-agent[vector-pinecone]"`

## Behavior

- **prefetch**: embeds the user query and injects top similar chunks.
- **sync_turn**: indexes combined user+assistant text (primary agent only).
- **on_session_end**: chunks the transcript and upserts each chunk.
- **on_delegation**: indexes delegation task + result on the parent agent.
- **Tool**: `vector_memory_search`.

Only one external `memory.provider` may be active at a time (same as other plugins).
