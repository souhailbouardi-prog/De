# Cross-Cutting Synthesis — 5 Articles + 6 Ecosystem Sources

**Goal**: surface where the 11 sources converge, disagree, and what the combined picture tells us about improving Aryan's Hermes setup.

---

## Convergences (where ≥3 sources agree)

### 1. Persistent context is the product — not the model

- **witcheer**: "persistence × time = compound context" — the AI is mediocre; infrastructure around it (walnuts, crons, voice corrections) is what works
- **GBrain**: "brain pages are append-only logs that compile into current truth" — the brain is the asset
- **Spisak**: "Claude Code stores facts. Hermes stores executable procedures" — skills compound
- **awesome-hermes-agent**: "Memory has become foundational, not optional" — Honcho, Hindsight, and multiple memory systems compete

**Implication for Aryan**: the KV MCP + life-advisor skill captures *sources*, but nothing currently synthesizes them into compiled-truth pages. This is the single biggest gap.

### 2. Skills are executable procedures, not notes

- **Spisak**: "Hermes stores executable procedures … the entire research-filter-format workflow"
- **GBrain**: `docs/ethos/THIN_HARNESS_FAT_SKILLS.md` — thin CLI core, fat markdown
- **obra/superpowers**: auto-triggering skills with strict "Use when…" clauses
- **awesome-hermes-agent**: agentskills.io cross-platform standard gaining traction

**Implication**: Aryan's `daily-health` and `life-advisor` skills are correctly shaped (procedures, not facts). The missing discipline is auto-triggering — right now they fire on explicit user command (`/health`, `/advisor`); obra's pattern would fire them automatically when the conversation matches a trigger.

### 3. One unified agent > multi-agent swarm (but sub-agents are fine)

- **Spisak**: fintech founder's 5-agent split failed in 48h — collapsed to one Hermes succeeded
- **AutoAgent**: meta-agent and task-agent split works *because* they share weights (model empathy)
- **GBrain**: sub-agents for entity detection / research execution routed to cheaper models
- **Anthropic Managed Agents**: brain/hands decoupling via virtualized interfaces

The pattern: **one agent with unified memory** + **specialized sub-agents for narrow delegated work**. Not 5 agents with independent memories.

**Implication**: Aryan is on the right path (one gateway, one memory, one KV). Don't split. But the `delegate_tool.py` + cheap-model routing pattern is worth adopting for entity detection + research.

### 4. Traces are load-bearing, not scores alone

- **AutoAgent**: "traces are everything. Score-only feedback tanks improvement rate"
- **GBrain**: timeline entries are the evidence trail — compiled_truth without provenance is hallucination
- **Seeing Like an Agent**: tool design is empirical — you learn from what the model actually does, not what you think it'll do
- **Hermes internals**: `_SKILL_REVIEW_PROMPT` reads trajectories every 15 turns (already half-right)

**Implication**: Any eval harness Aryan adds must capture trajectories, not just pass/fail. Hermes has this infrastructure (`trajectory_compressor.py`); it just isn't wired to scoring yet.

### 5. Model selection is load-bearing, non-deterministic ≠ free

- **Spisak**: model selection is the #1 Hermes setup failure; frontier model required for production
- **AutoAgent**: model empathy — same-model meta+task outperforms mixed; OpenRouter `:free` routing is worst case
- **witcheer**: three-tier stack (GLM-5 interactive / GLM-4.7 crons / local qwen3.5:4b compression) — each tier picked deliberately
- **awesome-hermes-agent**: no inference cost tracker in the ecosystem (gap)

**Implication (Aryan lived this today)**: GLM-4.5-air:free edited files unexpectedly; gpt-oss-120b:free behaved. Pinning to one specific free model beats rotating the `:free` roulette. Budget for frontier model on Aryan's highest-leverage cron (behavioral-morning-digest, which drives the day) if free tier quality is insufficient.

### 6. Deterministic collectors + LLM judgment

- **GBrain**: "code for data, LLMs for judgment … LLMs forget links — bake them in code"
- **last30days-skill**: multi-source research pipeline — deterministic fanout, LLM synthesis at the end
- **witcheer**: 35 shell scripts for data sources; LLM only classifies / writes / compresses

**Implication**: the upcoming Renpho→Apple Health weight auto-sync (in Aryan's Todoist backlog) and any KV enrichment cron should be deterministic Python/bash, not LLM-driven. Let the LLM judge the digest, not fetch it.

---

## Tensions (where sources disagree or hide complexity)

### Tension 1: "One agent" (Spisak) vs. "Meta/task split" (AutoAgent)

Spisak says splitting failed. AutoAgent says splitting is the only way self-optimization works. Resolution: **Spisak's anti-pattern is splitting by *domain* (marketing vs. sales vs. engineering).** AutoAgent's pattern is splitting by *role* (one learns, one does). The agents share the same user, the same memory, the same goal — only the learning-from-traces role is separate.

**For Aryan**: don't split health vs. advisor vs. finance. Do separate "optimizer of the daily-health skill" as a meta-agent if/when adding eval harnesses.

### Tension 2: "Frontier model required" (Spisak) vs. "Free local is viable" (witcheer)

Spisak: frontier API or Hermes feels broken. witcheer: GLM-4.7 for crons + local qwen3.5:4b works at $21/month. Resolution: **it depends on skill complexity.** Simple reminder crons (noon-nudge, evening melatonin) work on any model. Skills that require tool-use reasoning, code-edit judgment, or multi-step orchestration degrade below frontier.

**For Aryan**: message-only crons (health reminders) on free tier; any cron that invokes scripts + does synthesis (weekly-review, behavioral-digest) is the right place to spend model budget.

### Tension 3: "Compiled-truth rewrite" (GBrain) vs. "Append-only" (everything else)

GBrain uniquely requires *rewriting* compiled-truth on every update — an LLM-call-per-write cost. Other sources (Spisak, witcheer, obra) are pure append. Resolution: **compiled-truth is a synthesis layer, not an event log.** Events still go in a timeline; synthesis gets rewritten. This is a design choice with a real token cost that GBrain is explicit about.

**For Aryan**: a dream-cycle cron (re-synthesize compiled_truth nightly on stale pages) is the cheaper variant of GBrain's per-write rewrite. Batch the cost into one overnight job rather than paying on every update.

---

## Ranked action list — derived from all 11 sources

### Now (this week)

1. **Pin cron model** to one specific free model (not `:free` roulette) — *AutoAgent model empathy + Spisak #1 failure mode*. Already partially done today; document as policy.
2. **Add `[Source: ...]` to every fact written by skills** — *GBrain Iron Law*. One-line change to each SKILL.md.
3. **Install Hindsight or equivalent long-term memory layer** — *awesome-hermes-agent* — gives Hermes its own persistent memory across cron runs.

### Next (2-3 weeks)

4. **Add a wiki layer on top of KV** — *Spisak workflow #7 + GBrain compiled-truth*. New cron `kv-wiki-maintain` (weekly) reads new KV sources and updates synthesized wiki pages with cross-refs. Without this, every KV query is a fresh search; synthesis never compounds.
5. **Implement "brain-first lookup" in advisor skill** — *GBrain discipline*. Before web search / Firecrawl, grep vault + query KV MCP. One-line addition to `skills/advisor/life-advisor/SKILL.md`.
6. **Replace subjective skill-review with deterministic eval** — *AutoAgent + Hermes's existing loop*. For at least one skill (e.g. `daily-health`), define: "did a row get written to `health.db` with today's date? → pass/fail." Feed the score to `_SKILL_REVIEW_PROMPT` alongside the trace.
7. **Voice-corrections log** — *witcheer flywheel #2*. One markdown file capturing "you wrote X, I changed to Y, because Z" for every user edit. Becomes the voice training loop.

### Later (month+)

8. **Dream cycle nightly cron** — *GBrain dream cycle*. Entity sweep, citation audit, stale compiled_truth re-synthesis, sync+embed. The biggest compounding mechanism but also the most complex.
9. **Entity detection on every user turn** — *GBrain 6b*. Async sub-agent via `delegate_tool.py` routed to cheap model. Captures people/concepts to the vault automatically.
10. **Web monitoring via Camoufox + Firecrawl** — *Spisak workflow #2*. Replace manual thread-reading with a daily cron that summarizes handles Aryan follows.
11. **Meta-skill for skill optimization** — *AutoAgent + Hermes's `skill_manager_tool.py`*. Start with one target skill + one deterministic eval; add hill-climb + revert. This is the long-term roadmap for "Hermes that gets better at itself."

### Reject / not yet

- **Multi-agent split by domain** — *Spisak's explicit anti-pattern*. Don't do it.
- **Paid-tier frontier model by default** — unless a specific cron demonstrates free-tier inadequacy.
- **Custom GUI / workspace** — *awesome-hermes-agent gap*. Three competing solutions exist; pick when needed.
- **Full GBrain Postgres substrate** — *GBrain's own Tier 3 advice*. Wait until vault > 1000 files and grep is slow.
- **Splitting into multiple specialized Hermes instances** — *Spisak workflow #6 anti-pattern*.

---

## The unifying thesis

The 11 sources agree on this picture:

> **An agent with compound memory, grounded outputs, measured skills, and a same-model learning loop is worth more than a smarter agent with none of those.**

Everything Aryan has done so far — health cron, KV integration, advisor skill — is building this asset. The improvements that matter aren't new features; they're disciplines (source attribution, brain-first lookup, model pinning, eval-driven skill updates) that make the existing asset compound faster.
