# ALIVE — The Context System That Makes Everything Compound

> "This is the part most people haven't seen before, and it's the part that makes the biggest difference." — witcheer

## What it is

ALIVE is a **structured on-disk context system**, created by @stackwalnuts. The basic unit is a **"walnut"** — a context container for one project or domain. Think of it as a personal knowledge graph expressed as a filesystem convention.

It is **not**:
- A memory indexing/search engine
- A vector store / RAG system
- A database
- A Hermes skill

It **is**:
- A directory convention
- A file-naming convention (5 canonical files per walnut)
- A write/read protocol wired into cron jobs via a single shell script (`update-walnut.sh`)
- A skill (`walnuts`) that lets the interactive agent synthesize a cross-venture view

The entire primitive is ~77 lines of bash + a directory convention + a SKILL.md.

## Directory structure

```
~/world/
  .alive/                         — config
  02_Life/witcheer/               — personal brand, content, growth
  04_Ventures/yari-finance/       — CDP protocol, his Growth Lead role
  04_Ventures/arcana/             — redacted
  04_Ventures/micro-entreprise/   — redacted
  05_Experiments/oz-agent/        — the agent itself
```

Categorization is PARA-like (`02_Life`, `04_Ventures`, `05_Experiments`). 5 walnuts across "his world".

## The 5 canonical files per walnut

Each walnut has a `_core/` folder containing:

| File | Content | Write cadence |
|---|---|---|
| `key.md` | Identity, thesis, connections to other walnuts | Rarely (when mission shifts) |
| `now.md` | Current phase, next action, blockers | Weekly / on shift |
| `tasks.md` | Urgent / active / backlog | Daily |
| `insights.md` | Standing knowledge, lessons learned | As discovered |
| `log.md` | Session history, **prepend-only, newest first** | Every cron run |

"That's it." — witcheer. Deliberately minimal.

## The three integration layers

### Layer 1: Cron jobs WRITE to walnuts

At the end of every research cron, `update-walnut.sh` (77 lines of bash) prepends a timestamped log entry to the relevant walnut's `log.md`:
- `research-ai` → writes to `oz-agent` walnut
- `research-defi` → writes to `yari-finance` walnut
- `research-arcana` → writes to `arcana` walnut

Every walnut therefore accumulates its own research history automatically.

### Layer 2: Cron jobs READ from walnuts

Before researching, each cron reads the relevant walnut's `tasks.md` and `insights.md`. This aligns research to actual current priorities:

- `research-ai` reads `oz-agent/tasks.md` ("improve draft quality") → searches for prompt engineering techniques specifically.
- `research-defi` reads `yari-finance/tasks.md` ("map RWA partnership opportunities") → searches for RWA protocol news specifically.
- `morning-briefing` reads **ALL** walnuts' `now.md` → surfaces what matters today across every project.

### Layer 3: Interactive Telegram gets walnut context

Typing `walnuts` in Telegram invokes the `walnuts` skill → the agent reads all 5 walnut files and delivers a synthesized cross-venture view. Example output from the article:

> 5 walnuts across your world.
> yari finance - pre-launch, 2-3 weeks out.
> arcana - live but no outreach started.
> oz agent - hitting quality ceiling on drafts.
> tension: yari launch + arcana outreach + oz quality fix all competing for attention in the same window.

Context stays in session until idle timeout.

## The compounding feedback loop

The full cycle witcheer describes:

1. Aryan/user updates walnut tasks (manually or via Telegram).
2. Cron jobs read tasks → research aligns to priorities.
3. Research produces findings → findings prepend-log to the walnut.
4. User adjusts tasks based on findings.
5. Next cron picks up adjusted priorities.
6. Research becomes more focused.
7. Findings become more relevant.
8. Repeat.

> "Each cron knows what I'm trying to accomplish. It reads my priorities before searching. It writes what it found after searching. And the next session starts smarter."

**Critical property:** both Claude Code and Hermes read/write the same files natively. Same context layer — no sync, no export, no translation.

## Why it works (design reasoning)

1. **Filesystem > DB.** Plain markdown is editable by human, by Claude Code, by Hermes, by any cron. No schema migrations. No server to run.
2. **Prepend-only log** = immutable history without write contention or needing a DB.
3. **Canonical 5-file schema** = small enough for any cron to read all of them into context cheaply, structured enough that the agent knows where to look for tasks vs insights vs history.
4. **Write-after-research is mandatory.** Step 8 of every research cron's prompt is explicit: "a session with no writes is a failure." Without this, research evaporates.
5. **Tasks file is the steering wheel.** Because crons read `tasks.md` before searching, the human keeps agency — update the tasks, and the whole fleet of crons pivots on next run.

## Mapping to Hermes primitives

| ALIVE concept | Hermes equivalent | Gap |
|---|---|---|
| `~/world/<area>/<walnut>/_core/*.md` | `memory/` (freeform) | No standard layout |
| `update-walnut.sh` | No equivalent | Need to add |
| `walnuts` skill | `skills/<name>/SKILL.md` | Straightforward port |
| Log.md prepend-only | No equivalent | Ergonomic helper needed |
| Crons read tasks before running | Convention in cron job prompt | Needs shared helper |

Aryan's Hermes already has `skills/advisor/life-advisor` and `skills/health/daily-health` — natural candidates for walnut-style context anchoring (a "health" walnut, a "finance" walnut, a "KV/hermes" walnut, etc.).

## Concrete things to port

1. **Directory convention.** Define `~/hermes-world/<area>/<walnut>/_core/{key,now,tasks,insights,log}.md`.
2. **`update-walnut.sh` analog** in `scripts/` that prepends a timestamped heading + provided content to a target walnut's `log.md`. Crons invoke at tail.
3. **SKILL.md for `walnuts`** that reads all 5 files across all walnuts and emits a cross-project synthesis. One-word trigger.
4. **Research cron prompt convention:** step 1 = load walnut tasks+insights; step N = write findings to walnut log; step N+1 = self-check "did I write?"
5. **Morning briefing reads all `now.md` files** to surface cross-cutting tensions.

## Risks / gotchas

- Aryan already uses the Knowledge Vault (KV) for persistent memory. There is overlap. A decision is needed: does ALIVE replace KV for project context, complement it, or does KV become the "insights" store while walnuts own the "log"? Recommendation: walnuts = local working memory + prepend log, KV = long-term indexed knowledge. The walnut log can be periodically ingested into KV.
- Prepend-only log grows unbounded. witcheer has `compact_memory.sh` archiving session logs >3 days old — so walnuts may still need rotation.
- No concurrency control on markdown files; if two crons write to the same log at once, corruption is possible. `update-walnut.sh` likely uses flock or similar — needs verification if replicated.
