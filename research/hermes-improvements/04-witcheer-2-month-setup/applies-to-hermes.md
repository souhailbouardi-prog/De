# What Aryan Could Adopt — Gap Analysis & Action List

Aryan's existing Hermes state (from repo inspection):
- `skills/health/daily-health` — health cron with DB + SQLite contention fix (from recent commits)
- `skills/advisor/life-advisor` — advisor skill
- KV (knowledge-vault) MCP integration — long-term indexed memory
- Recent work: phase 3 smart insights, phase transition detection (health)

witcheer's setup spans far more surface area. This is the **prioritized gap list**, ordered by leverage-per-hour.

---

## TIER 1 — High-leverage, low-cost (do this week)

### 1. Set session idle timeout to 60 minutes
**Why:** witcheer's single biggest performance win. Default is 1440 min (24h). Long sessions = bloated context = 10-minute responses.
**Action:** Find the session idle timeout config in Hermes (probably gateway or agent config), set to 60.
**Risk:** none. Research still persists to files between sessions.

### 2. Point compression at a local Ollama model
**Why:** Prevents the "silent compression death spiral" witcheer describes. Free, no rate limits.
**Action:**
```bash
brew install ollama
ollama pull qwen3.5:4b
```
Then in `.env`: `OPENAI_BASE_URL=http://localhost:11434/v1`; in `config.yaml`: `summary_model: qwen3.5:4b`, `compression_threshold: 0.50`, `ollama_keep_alive: 5m`.
**Risk:** low. Ollama is stable; M4 handles 4b models easily. Verify Hermes actually routes compression to this endpoint (may need config spelunking).

### 3. Per-job model config in jobs.json
**Why:** Survives framework updates. Witcheer's explicit #2 lesson.
**Action:** For Aryan's daily-health job, set `"model": "<cheap-model>"` explicitly in the job definition.
**Risk:** none.

### 4. Add the "mandatory writes + self-check" pattern to existing health cron
**Why:** Witcheer's single most effective prompt pattern — step N: "did I write? if no, loop." Every research cron needs this.
**Action:** At the end of the `daily-health` prompt, add:
```
Final self-check: did I write findings to <health log>? If NO, return to step X and write them now. A session with no writes is a failure.
```
**Risk:** none.

### 5. Start `voice-corrections.md` from day 1
**Why:** Witcheer's explicit lesson #3. Compounds slowly — start early.
**Action:** Create `memory/voice/voice-corrections.md`. Whenever Aryan edits an AI-produced draft (advisor, health insight, content), manually append a "when you did X, I changed it to Y, because Z" line. Even without a `voice-learn` skill yet, the file itself is useful.
**Risk:** none.

---

## TIER 2 — Structural wins (do this month)

### 6. Adopt the ALIVE walnut convention
**Why:** This is the "compound context" engine. See `alive-context-system.md`.
**Action:**
1. Create `memory/walnuts/` (or `~/hermes-world/`) with one walnut per domain: `health`, `career`, `finance`, `creative`, `hermes-meta`.
2. Each walnut has `_core/{key,now,tasks,insights,log}.md`.
3. Write a small `scripts/update-walnut.sh` that prepends a timestamped entry to `<walnut>/log.md`.
4. Modify the daily-health cron: read `walnuts/health/tasks.md` before running; call `update-walnut.sh health "<summary>"` at tail.
5. Build a `skills/walnuts/` skill that synthesizes a cross-domain view on demand.

**KV overlap decision:** Walnuts = hot working memory + prepend log. KV = long-term indexed knowledge. Periodic job can ingest walnut logs into KV.

**Risk:** duplication with KV if not scoped carefully. Spend 30 min up-front deciding the boundary.

### 7. Build a `daily-nudge` cron
**Why:** Witcheer's 11:00 job. Reads ALL project context files, suggests where to focus, surfaces cross-project tensions. Highest-value single cron after the morning briefing. Aryan has multiple projects (0DevProjects/*) — this is a natural fit.
**Action:** Cron job that reads all walnut `now.md` + current tasks, produces a 1-paragraph priority recommendation. Delivers to Telegram or preferred channel.
**Risk:** none. One cron. Can iterate.

### 8. Source diversity rule for any research-type cron
**Why:** Witcheer's explicit lesson #5. Without explicit ordering, LLMs default to Reddit for everything.
**Action:** Any prompt that does web search must specify order: "Fetch X first, then Y, then Z, THEN use web search to fill gaps."
**Risk:** none.

### 9. Add a meta `health-check` cron
**Why:** Witcheer's 21:00 job. Monitors cron execution, gateway status, disk space. Catches silent failures (compression death spiral being the canonical one).
**Action:** 1 cron, 10 lines. Checks: did each cron run? Is gateway up? Disk OK? Alerts to Telegram if not.
**Risk:** none.

---

## TIER 3 — High-ceiling (do this quarter)

### 10. Build a `nightly-builder` cron (autonomous code fill)
**Why:** "The wildest one. It looks at gaps identified during research... and autonomously writes code to fill them. It has built monitoring scripts, fixed broken parsers, and created new data pipelines. While I sleep."
**Action:**
1. A "gaps" file (e.g. `memory/gaps.md`) where research crons append identified missing tools/broken pipelines.
2. An overnight cron reads gaps, picks one, writes code, runs tests, commits to a branch.
3. Human review in the morning.
**Risk:** non-trivial. Requires sandboxing (witcheer uses Docker — `docker-cleanup.sh` removes zombie sandbox containers >4h old). Start with read-only code suggestions, then promote to autonomous.

### 11. Build a `weekly-planner` cron
**Why:** Witcheer's Sun 08:00 job. Reads performance + research + project states → produces weekly content + priority plan.
**Action:** One cron, reads all walnuts' log.md + content performance, produces a weekly plan posted to Telegram.
**Risk:** low.

### 12. Build a `voice-learn` skill
**Why:** Automates step 3-5 of the voice feedback loop.
**Action:** Skill triggered by "I tweaked your draft" in Telegram. Reads original + posted version, extracts diff, appends lesson to `voice-corrections.md`.
**Risk:** low. Diff extraction is an LLM task itself.

### 13. Add `compact_memory.sh` equivalent
**Why:** Prevents unbounded growth. Witcheer archives session logs >3 days old, trims ops log to 7 days.
**Action:** Shell script + weekly cron.
**Risk:** none with backup.

---

## TIER 4 — Infra hygiene (low priority, do once)

- **`github-push-nightly.sh` with secret scanning** — 13 regex patterns checking API keys, tokens, passwords before push. witcheer says three layers of checks.
- **`docker-cleanup.sh`** — removes zombie containers >4h old.
- **`auto-update.sh`** — daily framework update trigger.
- **Symlink scripts to `~/scripts/`** with `chmod 700` — witcheer's ergonomic convention, easier for agent to call.

---

## What to SKIP from witcheer's setup

- **Telegram channel drafting (`grimoire`, `grimoire-drafter`)** unless Aryan wants to run a public content channel. Not obviously needed.
- **DeFi-specific scripts (coingecko, defillama, rwa-tracker, governance-tracker, dune-monitor, stablecoin-supply-monitor)** — not Aryan's domain.
- **`yari-intel` / `arcana-intel`** — domain-specific skills, not transferable.
- **`alpha-scanner`** — same.
- **`research-defi` / `research-arcana`** crons — same.

---

## Suggested 2-week plan for Aryan

**Week 1:**
- Tier 1 items 1-5 (4 hours total): idle timeout, local Ollama compression, per-job model pin, mandatory-write self-check in health cron, start voice-corrections.md.

**Week 2:**
- Tier 2 item 6: adopt walnut convention with 3 walnuts (`health`, `hermes-meta`, one project). Wire daily-health to read+write its walnut.
- Tier 2 item 9: add a simple `health-check` meta cron.

Then assess: does the compound-context flywheel visibly kick in? If yes, expand to item 7 (daily-nudge) and item 10 (nightly-builder).

---

## Integration with KV

Aryan's KV is an advantage witcheer doesn't have. Potential integration patterns:

1. **Walnut log → KV ingestion cron.** A periodic job that reads walnut logs older than N days and imports them into KV as structured sources. This gives long-term semantic search over the compound context.
2. **KV search before walnut write.** A research cron could `mcp__knowledge-vault__search_knowledge` first, check for related sources, then do web research for gaps only.
3. **Voice corrections in KV as a collection.** `mcp__knowledge-vault__save_collection` for voice rules — queryable by future skills.

**Aryan's system could end up strictly better than witcheer's** by combining ALIVE (hot working memory + prepend log) with KV (indexed long-term knowledge) — witcheer has only the first half.
