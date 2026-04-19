# GBrain — Research Findings

- **Source tweet**: https://x.com/garrytan/status/2042497872114090069 (Apr 10 2026, 5.4K likes, 596 retweets)
- **Repo**: https://github.com/garrytan/gbrain — MIT, TypeScript/Bun, v0.9.1, 6.1k stars, 672 forks, created 2026-04-05
- **Tweet text**: "If you want your OpenClaw or Hermes Agent to be able to have perfect total recall of all 10,000+ markdown files, GBrain is here to help. It's exactly my OpenClaw/Hermes Agent setup. MIT-licensed open source."
- **Sibling**: gstack (https://github.com/garrytan/gstack) — Garry's Claude Code setup

## 1. One-sentence framing

GBrain is a Postgres-native **hybrid RAG backbone** (the "retrieval layer") wrapped in an opinionated **agent playbook** (`docs/GBRAIN_SKILLPACK.md` + 23 guides) that tells the agent WHEN to read, WHEN to write, and HOW to keep the brain compounding. The SQL is table-stakes; **the playbook is the load-bearing contribution.**

## 2. Architecture — three layers, two repos

```
Brain Repo (git, markdown)  ──>  GBrain (retrieval)  <──>  AI Agent (read/write)
 source of truth                 Postgres + pgvector        skills define HOW
 human can always edit           hybrid search (RRF)        entity detect / enrich / ingest
```

- **Brain repo**: ~10,000 markdown files in `people/`, `companies/`, `meetings/`, `originals/`, `concepts/`, `media/`, `daily/`. Human-readable, git-versioned, survives any tool swap.
- **GBrain**: CLI + MCP server (stdio or HTTP) over a 10-table Postgres schema with pgvector HNSW + tsvector. Pluggable engine — default **PGLite** (embedded Postgres 17.5 via WASM, zero server), optional Supabase for >1000 pages (~$25/mo).
- **Agent** (OpenClaw, Hermes, Claude Code): doesn't store knowledge itself; reads/writes through GBrain via 30 MCP tools.

## 3. Indexing pipeline

1. **File resolution**: local → `.redirect.yaml` → `.supabase` → error.
2. **Markdown parse** (gray-matter): frontmatter + body. Body split at first standalone `---` into **compiled_truth** (above) and **timeline** (below).
3. **Content hash**: SHA-256 on `pages.content_hash`. Re-running import skips unchanged files — fully idempotent.
4. **Chunking** (3 strategies):
   - **Recursive** (default): 300-word chunks, 50-word sentence-aware overlap, 5-level delimiter hierarchy.
   - **Semantic**: embed sentences, cosine similarity between adjacent, Savitzky-Golay smoothing to find topic boundaries.
   - **LLM-guided**: 128-word candidates, Claude Haiku identifies topic shifts in sliding windows.
5. **Embedding**: OpenAI `text-embedding-3-large` (1536-dim), batch 100, exponential backoff.
6. **Transaction**: atomic page + chunks + tags + version snapshot.

Throughput: ~30s text import for 7,000 files; ~10–15 min embedding (~$4–5 OpenAI). Storage ~750MB for a 7.5k-page brain.

## 4. Retrieval — hybrid RAG with RRF fusion

```
Query
  ↓ (optional) multi-query expansion via Claude Haiku → 2 alt phrasings
  ├── Vector search (pgvector HNSW, cosine)    → 2x limit per variant
  └── Keyword search (Postgres tsvector, ts_rank, weighted A/B/C) → 2x limit
  ↓
RRF merge: score = Σ(1 / (60 + rank))     # Reciprocal Rank Fusion
  ↓
4-layer dedup: best 3 chunks/page, Jaccard > 0.85, no type > 60%, max 2 chunks/page
  ↓
Stale alerts: compiled_truth older than latest timeline → flag
  ↓
Top N (default 20) as chunks with slug refs
```

**Three search modes** the agent picks between:

| Mode | Command | Needs embeddings | Best for |
|---|---|---|---|
| Direct | `gbrain get <slug>` | No | Known slug |
| Keyword | `gbrain search <term>` | No | Exact names, day-one |
| Hybrid | `gbrain query <question>` | Yes | Semantic/fuzzy questions |

**tsvector weighting**: title (A), compiled_truth (B), timeline (C) — current synthesis surfaces first.

## 5. The knowledge model — "compiled truth + timeline"

Most distinctive idea. Every page has two zones separated by `---`:

```markdown
---
type: person
title: Sarah Chen
---
## State
VP Engineering at Acme Corp. Managing 45 people.
## Assessment
Sharp technical leader. [Source: User, meeting, 2026-04-07]
---
## Timeline
- 2026-04-07 | Discussed API migration. [Source: Meeting notes, 2026-04-07]
- 2026-03-15 | First intro from Pedro. [Source: User, direct, 2026-03-15]
```

| Zone | Action | Why |
|---|---|---|
| Compiled truth (above `---`) | **REWRITE** every update | Current synthesis; old assessments replaced, not accumulated |
| Timeline (below `---`) | **APPEND-ONLY**, never edited | Evidence trail; corrections are new entries |

Rationale: "Brain pages are append-only logs. To understand a person you read 200 timeline entries. The answer is buried in entry #147." Forcing rewrite on compiled_truth keeps top-of-page always-current, at the cost of an LLM call on writes.

## 6. The agent playbook — 10 disciplines

### 6a. Brain-agent loop (mandatory)
```
Signal → DETECT entities → READ brain FIRST → RESPOND with context
       → WRITE updates (compiled truth + timeline) → SYNC → next signal
```

### 6b. Entity detection on EVERY message
Async sonnet-class sub-agent spawned on every inbound message (non-blocking). Extract people/companies/concepts/originals. Capture user's **original thinking with exact phrasing** — never paraphrase.

### 6c. Brain-first lookup
Before any external API:
1. `gbrain search` (keyword)
2. `gbrain query` (hybrid)
3. `gbrain get people/<slug>` (direct guess)
4. Only then external API

### 6d. Source attribution (Iron Law)
Every fact carries `[Source: ...]`. Typed formats per channel. Hierarchy: user direct > primary (meeting/email) > enrichment API > web > social. **Conflicting sources noted with both citations — never silently resolved.**

### 6e. Iron Law of back-linking
"An unlinked mention is a broken brain." Every entity mentioned on page A must have a reciprocal timeline entry on entity A's own page. Enforced by nightly dream cycle.

### 6f. Dream cycle (nightly 2am cron — "most important job")
Four phases:
1. Entity sweep: today's conversations → thin pages / enrichment / timeline.
2. Citation audit: fix missing `[Source: ...]`, broken tweet URLs.
3. Memory consolidation: re-synthesize compiled_truth from accumulated timeline on stale pages (>7 days).
4. Sync + embed: `gbrain sync --no-pull --no-embed && gbrain embed --stale`.

"Skip the dream cycle and the brain slowly rots."

### 6g. Two-repo architecture (hard boundary)
- **Agent repo**: operational config only — AGENTS.md, SOUL.md, skills, cron, tasks, MEMORY.md.
- **Brain repo**: world knowledge only — people, companies, meetings, originals, concepts.

Test: "would this file transfer if I switched AI agents?" → brain. "Would this transfer if I switched to a different person?" → agent.

### 6h. Sub-agent model routing

| Task | Model | Cost ratio |
|---|---|---|
| Main session | Opus-class | 1x |
| Entity detection (every message) | Sonnet-class | 5–10x cheaper |
| Research execution | DeepSeek V3 | 25–40x cheaper |
| Quick lookups | Groq fast inference | cheapest |

### 6i. Deterministic collectors + LLM judgment
"Code for data, LLMs for judgment." Deterministic scripts produce pre-formatted markdown digests (with IDs + links baked in), LLM reads digest and does classification/replies. "LLMs forget links — bake them in code."

### 6j. Live sync not optional
Always chain: `gbrain sync --repo ~/brain && gbrain embed --stale`. Without the embed, new chunks are invisible to vector search.

### 6k. Notability gate
Not everything deserves a page. "A stub page with just a name is worse than no page (gives false confidence)."

## 7. Brain vs Memory vs Session (explicit distinction)

| Layer | Stores | Example | Query |
|---|---|---|---|
| **GBrain** | World knowledge (permanent) | "Pedro is CEO of Brex" | `gbrain search/query/get` |
| **Agent memory** | Operational state (replaceable) | "User prefers concise formatting" | `memory_search` |
| **Session context** | Current conversation | "We were just discussing the PR" | automatic |

## 8. Database schema (10 tables)

- **pages**: slug (unique), type, title, compiled_truth, timeline, frontmatter (JSONB), content_hash, search_vector (tsvector), timestamps
- **content_chunks**: page_id FK, chunk_text, chunk_source ('compiled_truth'|'timeline'), embedding vector(1536), HNSW index
- **links**: from_page_id, to_page_id, link_type, context
- **tags**: many-to-many
- **timeline_entries**: structured (date, source, summary, detail)
- **page_versions**: snapshot history
- **raw_data**: sidecar JSONB from external APIs
- **files**: binary attachments (S3/Supabase/local)
- **ingest_log**: audit trail
- **config**: brain-level settings

Indexes: B-tree on slug/type, GIN on frontmatter/search_vector, HNSW on embeddings, pg_trgm on title.

## 9. Integration pattern for Hermes

GBrain ships as:
- **OpenClaw plugin** (`openclaw.plugin.json`, `family: "bundle-plugin"`)
- **Standalone MCP server** (stdio or HTTP+bearer auth)
- **TypeScript library** (`createEngine('pglite' | 'postgres')`)
- **Standalone CLI**

README mentions Hermes deployment via Railway template (https://github.com/praveen-ks-2001/hermes-agent-template). User adds one MCP config (`command: gbrain, args: [serve]`), pastes SKILLPACK into system prompt, registers two cron jobs (live-sync every 15 min, dream cycle nightly).
