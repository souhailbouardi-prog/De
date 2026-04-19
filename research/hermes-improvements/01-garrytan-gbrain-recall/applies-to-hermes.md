# GBrain → applies to Hermes

## Tier 1 — high value, low effort

**1. Compiled-truth + timeline page format**
Replace or augment `skills/note-taking/obsidian/SKILL.md` (currently grep/find only). New skill `skills/note-taking/brain-pages/SKILL.md` teaches the two-zone format (compiled-truth above `---` rewritten; timeline below `---` append-only). Works on existing Obsidian vault — no infra change. Immediately yields better "what do we know about X" answers.

**2. Source attribution as Iron Law**
Mandate `[Source: ...]` on every fact written by health/advisor/note-taking skills. Typed formats per channel. Single biggest discipline for making Hermes outputs auditable six months later. Matches Aryan's life-advisor vision where every behavioral suggestion needs grounding.

**3. Brain-first lookup protocol**
Before any `web_search` or Firecrawl, agent must first grep Obsidian vault + query knowledge-vault MCP. User's stated vision explicitly wants Hermes pulling from KV (50 Cent power dynamics etc.) — brain-first is literally that discipline. Add to `skills/advisor/life-advisor/SKILL.md` and to the system prompt block.

**4. Entity detection on every message (scaled)**
New `skills/note-taking/entity-capture/SKILL.md` + hook on user-turn. Hermes already has `tools/delegate_tool.py` for subagent delegation. Spawn async entity-detector on each user turn routed to a cheaper model (Haiku/Sonnet), non-blocking. Appends to Obsidian vault automatically.

**5. Dream cycle nightly cron**
`cron/jobs.py` already exists. Add `dream_cycle` at 02:00 local that (a) scans today's sessions from `SessionDB`, (b) extracts entities into vault, (c) consolidates `compiled_truth` on stale pages, (d) fixes broken back-links. Single biggest compounding mechanism GBrain identifies.

## Tier 2 — adopt with adaptation

**6. Two-repo boundary (agent config vs. knowledge)**
Hermes has `~/.hermes/` (agent config) + separate Obsidian vault (knowledge). Boundary exists; formalize via `KNOWLEDGE_BOUNDARY.md`. Test: "transfers if I switch AI agents?" → vault. "Transfers if I switch to a different person?" → agent.

**7. Three search modes + token-budget rule**
Extend `skills/note-taking/obsidian/SKILL.md` beyond grep: direct `cat` (known filename), `grep` (keyword), hybrid via knowledge-vault MCP's `search_knowledge` / `search_by_intent`. Rule: "search returns chunks → confirm relevance → THEN load full page" — critical token-saving discipline.

**8. Deterministic collectors + LLM judgment**
"Code for data, LLMs for judgment." Every new data source builds a thin Python collector producing pre-formatted markdown digests (IDs + links baked in); LLM reads digest. Applies immediately to health daily-log flow that's in active development.

**9. Sub-agent model routing table**
Codify in `tools/delegate_tool.py`: entity detection → Sonnet; research execution → DeepSeek; quick lookups → Groq; main session → Opus-class. Hermes already supports multi-provider; this is discipline on top.

**10. Fat skills as markdown**
GBrain's `docs/ethos/THIN_HARNESS_FAT_SKILLS.md` is direct validation of Hermes's existing model. Keep investing in richer SKILL.md files with judgment + failure modes, not more tool code.

## Tier 3 — only if scaling past grep

**11. Postgres + pgvector substrate** — when vault grows past ~1000 files and grep slows. Fork/vendor GBrain as Hermes optional-skill. PGLite default = zero infra.

**12. RRF hybrid search + multi-query expansion** — if building custom retrieval.

**13. Idempotent content-hash import** — SHA-256 on row, skip on re-import. Useful for bulk-import flows (chat history, health logs).

## Mapping table

| GBrain concept | Hermes landing point |
|---|---|
| SKILLPACK | Expand `AGENTS.md` with "Knowledge protocols" section |
| Compiled-truth + timeline | New `skills/note-taking/brain-pages/SKILL.md` |
| Entity detection on every message | New `skills/note-taking/entity-capture/SKILL.md` + `delegate_tool.py` + user-turn hook |
| Dream cycle | New `cron/jobs.py` job `dream_cycle` at 02:00, uses `SessionDB` |
| Brain-first lookup | Prepend to `skills/advisor/life-advisor/SKILL.md` + `prompt_builder.py` |
| Source attribution Iron Law | Shared rule `skills/note-taking/_rules.md`, referenced by every write-skill |
| Three search modes | Update `skills/note-taking/obsidian/SKILL.md` |
| Sub-agent routing | New doc `docs/sub-agent-routing.md`; enforced via `delegate_tool` model param |
| Two-repo boundary | New top-level `KNOWLEDGE_BOUNDARY.md` |
| Notability gate | Rule in entity-capture skill — no stub pages |

## What Hermes already has that GBrain validates

- **`MemoryProvider` abstraction** — `BuiltinMemoryProvider` = operational (MEMORY.md); external providers (Honcho, Hindsight, Mem0, or GBrain as new MemoryProvider) = knowledge layer.
- **`cron/jobs.py` + `scheduler.py`** — ready to host dream cycle, live-sync, daily heartbeat.
- **`hermes_state.py` SessionDB with FTS5** — full-text search over past sessions. Missing: entity extraction on top + compiled-truth synthesis per entity.
- **`skills/note-taking/obsidian/SKILL.md`** — exists but grep-only. Direct candidate for SKILLPACK-style upgrade.
- **`tools/delegate_tool.py`** — supports model-aware subagent dispatch. Ready for sub-agent routing.
- **Skills-as-markdown** — architecture Hermes already uses. GBrain's ethos essays are direct validation.
- **Knowledge-vault MCP** — provides semantic search primitives. Covers the search-mode distinctions (not pgvector, but `search_knowledge`/`search_by_intent`/`find_similar`).

## Gaps GBrain exposes in Hermes

- No entity-detection sub-agent — every conversation is lossy
- No compiled-truth synthesis — notes are append-only, "what do we know about X" is expensive
- No source attribution discipline — facts from LLM synthesis aren't traceable
- No brain-first-lookup rule — agent reaches for web before `memory_search` or vault grep
- `note-taking/obsidian` is pure grep — misses semantic matches, won't scale
- No dream cycle — maintenance is manual

## Risks for Hermes specifically

- **Frontier-model dependency**: GBrain states Opus 4.6 / GPT-5.4 Thinking minimum. Hermes supports smaller OSS. Document quality ranges per model tier; degrade gracefully on smaller models.
- **Subagent cost**: entity detection on every message adds per-message sub-agent cost. Cheap-model routing + budget rate limits required.
- **Obsidian plain-text vs. DB**: staying on Obsidian means hybrid RRF isn't portable without an embedding layer. Knowledge-vault MCP fills that role today.
- **Two-repo discipline retroactively**: existing vault may mix agent config and world knowledge. One-time migration cost.
