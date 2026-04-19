# Daily Health Module — Design Spec (v2)

**Date:** 2026-04-10
**Approach:** Pure Skill (Approach A) — skill + scripts + cron jobs
**Scope:** MVP (Phase 1 from brief)
**Revision:** v2 — addresses Codex adversarial review (8 findings)

---

## Context

Aryan needs a daily health coach via Telegram that pulls WHOOP data, sends scheduled check-ins, logs habits conversationally, and catches disengagement early ("never miss twice"). The module is a Hermes skill — no custom tool registration, no standalone daemon.

**Key behavioral insight:** Aryan builds systems during moments of clarity, follows intensely, then collapses on single disruption. The agent must be low-friction, zero-judgment on slips, and operationalize "never miss twice" rather than just noting it.

---

## File Structure

```
skills/health/daily-health/
├── SKILL.md                    # Skill definition, trigger keywords, agent instructions
├── scripts/
│   └── health_log.py          # SQLite-backed health event logging + queries
└── references/
    └── aryan-health-profile.md # Condensed health profile for system prompt context

~/.hermes/scripts/
├── health_morning_query.py    # Zero-arg wrapper: prints last user interaction timestamp
├── health_noon_query.py       # Zero-arg wrapper: prints whether morning was responded to
└── health_log_cli.py          # Zero-arg wrapper: reads HEALTH_LOG_CMD env var, dispatches

~/.hermes/health/
└── health.db                  # SQLite database for health events
```

**Note on script placement:** Hermes cron scripts must reside in `~/.hermes/scripts/` and are
executed as `python <path>` with no CLI arguments (see `cron/scheduler.py:344`). The wrapper
scripts in `~/.hermes/scripts/` import from the skill's `health_log.py` module and call
specific functions directly. The skill's `scripts/health_log.py` is the library; the
wrappers are the cron entry points.

---

## SKILL.md

**Frontmatter:**
```yaml
name: daily-health
description: Daily health coach — WHOOP check-ins, habit logging, melatonin reminders, never-miss-twice detection
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Health, WHOOP, Habits, Telegram]
    related_skills: []
triggers:
  - /health
  - health check
  - log health
```

**Body sections:**
1. **Context** — Aryan's health conditions (hypothyroidism, lichen planus, asthma, recently quit smoking, deconditioned cardio), current phase (Recovery → Phase 1: fix sleep, walk daily, supplements, don't smoke), behavioral patterns (video game mindset, identity-based framing)
2. **Morning Check-In Instructions** — How to call WHOOP MCP tools (`mcp_whoop_get_recoveries`, `mcp_whoop_get_sleeps`), format the summary (recovery, HRV, RHR, SpO2, sleep duration/stages), suggest 3 daily tasks from current phase. **Informational only — no questions.** The check-in delivers data; the user logs responses via `/health` when ready.
3. **Evening Reminder Instructions** — Melatonin message format, brief prompt ("How was today?"). Also informational — user responds via `/health` if they want to log.
4. **Habit Parsing Guide** — Natural language patterns: walks ("walked 25 min"), meals ("had chicken rice"), supplements ("took supplements"), smoking ("smoked a cigarette"), nebulizing, weight, symptoms. How to call `health_log.py` for each. The agent invokes the terminal tool to run `python ~/.hermes/scripts/health_log_cli.py` with the appropriate env var.
5. **Tone Rules** — Direct not preachy. Zero judgment on slips (respond: "Noted. One slip doesn't undo your progress. Don't buy a pack. Tomorrow is a new day."). Brief Telegram-scannable messages. Identity-based framing. Data-driven (reference actual WHOOP numbers).
6. **Never Miss Twice** — When cron script reports >48h since last **user** interaction, append nudge: "Hey — haven't heard from you in 2 days. Everything okay? Remember: missing once is fine. Missing twice starts a new habit. Even just saying 'alive' counts as checking in."

### Interaction Model (Codex finding #2 fix)

Cron jobs run in isolated sessions. User replies to cron-delivered Telegram messages land in the
normal gateway chat session, which does NOT have the health skill loaded. Therefore:

- **Cron messages are informational only** — they deliver data, don't ask questions
- **User logs via explicit `/health` trigger** — e.g., `/health walked 20 min`, `/health smoked`, `/health clean today`, `/health mood 4`
- **The skill parses natural language after `/health`** — so `/health had eggs and rice for lunch` works

This avoids the reply-binding problem entirely. The user controls when to engage.

---

## Data Storage: SQLite

**File:** `~/.hermes/health/health.db`

**Schema:**
```sql
CREATE TABLE health_events (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,          -- ISO 8601 timestamp, always UTC (e.g., 2026-04-10T14:30:00Z)
    source TEXT NOT NULL DEFAULT 'user',  -- 'system' for cron-generated, 'user' for user-logged
    type TEXT NOT NULL,        -- checkin, response, habit, evening, symptom, nudge
    subtype TEXT,              -- walk, meal, supplement, smoke, nebulize, weight
    value REAL,                -- 25 (minutes), 4 (mood), 71.2 (kg)
    unit TEXT,                 -- min, kg, scale
    data TEXT,                 -- JSON blob for structured data (WHOOP metrics, meal details)
    note TEXT                  -- free text (symptom notes, meal descriptions)
);
CREATE INDEX idx_ts ON health_events(ts);
CREATE INDEX idx_type ON health_events(type);
CREATE INDEX idx_type_ts ON health_events(type, ts);
CREATE INDEX idx_source_ts ON health_events(source, ts);

-- Idempotency: prevent duplicate system events (e.g., two morning check-ins same day)
CREATE UNIQUE INDEX idx_system_daily ON health_events(date(ts), type, source)
    WHERE source = 'system' AND type IN ('checkin', 'evening', 'nudge');
```

**Database pragmas (match hermes_state.py pattern):**
```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")
conn.execute("PRAGMA synchronous=NORMAL")
```

**Why these pragmas:**
- **WAL mode** — allows concurrent reads during writes (cron + chat won't block each other)
- **busy_timeout=5000** — retry for 5s instead of immediate `database is locked` failure
- **synchronous=NORMAL** — safe with WAL, better performance than FULL

**Timestamp convention:** All timestamps stored as UTC. Conversion to local time (ET) happens
only at display time, using `hermes_time.py` helpers. This prevents DST/offset bugs in
queries — lexical ordering of UTC ISO 8601 strings is always chronological.

**Event types:**
| type | source | subtype | value | data | note |
|------|--------|---------|-------|------|------|
| checkin | system | — | — | `{"recovery":95,"hrv":94.8,...}` | — |
| response | user | — | — | `{"smoked":false,"supplements":true}` | — |
| habit | user | walk | 25 | — | "evening walk, cold but manageable" |
| habit | user | meal | — | `{"protein_est":45}` | "chicken rice eggs" |
| habit | user | supplement | — | — | — |
| habit | user | smoke | — | — | — |
| habit | user | nebulize | — | — | — |
| habit | user | weight | 71.2 | — | — |
| habit | user | sighing | 5 | min | "cyclic sighing" |
| evening | system | — | — | — | "reminder sent" |
| evening | user | — | 4 | — | "feeling better than yesterday" |
| symptom | user | — | — | — | "wheeze less on forced exhale" |
| nudge | system | noon | — | — | "supplement nudge sent" |
| nudge | system | miss2 | — | — | "never-miss-twice nudge sent" |

---

## health_log.py Library

**Location:** `skills/health/daily-health/scripts/health_log.py`

This is a Python module (importable), not a CLI script. The cron wrapper scripts import from it.

**Public functions:**

```python
# Logging
log_event(type, subtype=None, source="user", value=None, unit=None, data=None, note=None)

# Queries
last_user_interaction() -> str | None     # UTC ISO timestamp of most recent source='user' event
today_events() -> list[dict]              # All events for today (UTC day boundary)
check_morning_response() -> bool          # Did today's system checkin get a user response?
events_range(days: int) -> list[dict]     # All events from last N days
```

**Implementation details:**
- Uses Python `sqlite3` (stdlib, zero deps)
- DB path: `~/.hermes/health/health.db` (auto-creates directory + tables on first run)
- All timestamps stored as UTC ISO 8601
- WAL mode + busy_timeout (matches hermes_state.py concurrency pattern)
- JSON output for queries (agent parses it)
- Idempotency: system events deduplicated by (date, type, source)

---

## Cron Wrapper Scripts

**Location:** `~/.hermes/scripts/` (required by Hermes cron runner)

These are zero-argument Python scripts that import from the health_log module.

### health_morning_query.py
```python
"""Cron pre-run script: prints last user interaction timestamp."""
import sys
sys.path.insert(0, "<path-to-skill>/scripts")
from health_log import last_user_interaction
ts = last_user_interaction()
print(ts or "NEVER")
```

### health_noon_query.py
```python
"""Cron pre-run script: prints whether morning checkin was responded to."""
import sys
sys.path.insert(0, "<path-to-skill>/scripts")
from health_log import check_morning_response
print("RESPONDED" if check_morning_response() else "NO_RESPONSE")
```

### health_log_cli.py
```python
"""CLI wrapper for agent to call health_log functions via terminal tool.
Reads HEALTH_LOG_CMD env var for the command, HEALTH_LOG_ARGS for JSON args."""
import sys, os, json
sys.path.insert(0, "<path-to-skill>/scripts")
from health_log import log_event, last_user_interaction, today_events, events_range

cmd = os.environ.get("HEALTH_LOG_CMD", "")
args = json.loads(os.environ.get("HEALTH_LOG_ARGS", "{}"))

if cmd == "log":
    log_event(**args)
    print("OK")
elif cmd == "last_interaction":
    print(last_user_interaction() or "NEVER")
elif cmd == "today":
    print(json.dumps(today_events(), indent=2))
elif cmd == "range":
    print(json.dumps(events_range(args.get("days", 7)), indent=2))
else:
    print(f"Unknown command: {cmd}", file=sys.stderr)
    sys.exit(1)
```

---

## Cron Jobs

Three jobs in `~/.hermes/cron/jobs.json`:

### Job 1: Morning Check-In
```json
{
  "name": "health-morning-checkin",
  "schedule": "30 10 * * *",
  "skills": ["daily-health"],
  "prompt": "Run the morning health check-in. Pull last night's WHOOP data via mcp_whoop_get_recoveries and mcp_whoop_get_sleeps. Format as a brief Telegram summary with recovery, HRV, RHR, SpO2, sleep duration and stages. Add 3 daily tasks from current phase priorities. Log the WHOOP data as a system checkin event via the terminal tool. Check the script output for last user interaction time — if it says NEVER or the timestamp is >48h ago, append the never-miss-twice nudge. Do NOT ask questions — this is informational only.",
  "deliver": "telegram",
  "script": "health_morning_query.py"
}
```

### Job 2: Evening Reminder
```json
{
  "name": "health-evening-reminder",
  "schedule": "30 19 * * *",
  "skills": ["daily-health"],
  "prompt": "Send the evening melatonin reminder: 'Melatonin time. Take half a tab now. Blue light glasses on in an hour.' Log this as a system evening event via the terminal tool. Do NOT ask questions.",
  "deliver": "telegram"
}
```

### Job 3: Noon Supplement Nudge (Always Send)
```json
{
  "name": "health-noon-nudge",
  "schedule": "0 12 * * *",
  "skills": ["daily-health"],
  "prompt": "Send a brief supplement nudge: 'Hey — did you take your supplements? Just checking.' Log this as a system nudge event (subtype: noon) via the terminal tool.",
  "deliver": "telegram"
}
```

**Design note (Codex finding #8):** The noon nudge always sends instead of conditionally
suppressing via `[SILENT]`. The `[SILENT]` marker is fragile — the scheduler suppresses
delivery if `[SILENT]` appears anywhere in the response (case-insensitive substring match
at `scheduler.py:867`). For a health system, false suppression is worse than a redundant
nudge. If the user already took supplements, they'll just ignore it.

**Timezone note:** Cron expressions are in system local time (ET for Aryan). Times are
stable as long as the system timezone doesn't change. Hermes uses `hermes_time.py` for
timezone-aware operations internally.

---

## WHOOP MCP Configuration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  whoop:
    command: mcp-hub
    args: ["serve", "-s", "whoop", "--transport", "stdio"]
    timeout: 120
    connect_timeout: 60
```

**Path note (Codex finding #7):** Uses bare `mcp-hub` (resolved via PATH) instead of a
hardcoded absolute path. Ensure `mcp-hub` is on the PATH — e.g., via a symlink:
```bash
ln -sf ~/Documents/0DevProjects/mcp-hub/.venv/bin/mcp-hub /usr/local/bin/mcp-hub
```

**Gateway restart required:** MCP tools are discovered at gateway startup. After adding
the WHOOP server to config.yaml, restart the Hermes gateway for cron jobs to have access
to `mcp_whoop_*` tools. A running gateway will NOT auto-discover new MCP servers.

**Tools available to agent:**
- `mcp_whoop_get_recoveries` — recovery score, HRV, RHR, SpO2, skin temp
- `mcp_whoop_get_sleeps` — sleep stages, duration, efficiency, respiratory rate
- `mcp_whoop_get_cycles` — daily strain, calories
- `mcp_whoop_get_workouts` — workout details (future use)
- `mcp_whoop_get_profile` — user profile

**Auth:** mcp-hub reads tokens from `~/.config/mcp-hub/whoop_tokens.json`, auto-refreshes OAuth. No agent-side auth needed.

**Reconnection:** Hermes retries flaky stdio MCP servers up to 5 times before giving up
permanently (`mcp_tool.py:1950`). If mcp-hub crashes repeatedly, WHOOP tools become
unavailable until gateway restart. Monitor cron job output for MCP errors.

---

## references/aryan-health-profile.md

Condensed from the full health research. Contains:
- Age, height, weight, location
- Active conditions (hypothyroidism, lichen planus, asthma, post-smoking recovery)
- Current phase (Recovery → Phase 1) and daily priorities
- Supplement stack (condensed list, not full research)
- Medications (Oracort 0.1%, Budecort nebulizer)
- Behavioral notes (video game mindset, identity framing, never miss twice)

**Not included:** Full research files, session logs, predictive models — those stay in the aryan-health project. The skill only carries what the agent needs for daily interactions.

---

## Known Limitations (MVP)

1. **Delivery failure is silent.** If Telegram send fails after the agent generates output,
   the scheduler still marks the job as successful (`scheduler.py:208-251`). There is no
   outbox or retry queue. The morning check-in could be generated and logged but never
   received. This is a Hermes platform limitation — fixing it is out of scope for a skill.

2. **No reply-binding across sessions.** Cron sessions are isolated from the gateway chat
   session. User replies to cron messages are handled as generic chat unless the user
   explicitly invokes `/health`. This is why cron messages are informational-only.

3. **MCP reconnection limit.** After 5 failed reconnects, WHOOP MCP tools are permanently
   unavailable until gateway restart.

---

## Verification Plan

1. **health_log.py unit test** — Create temp SQLite DB, test all functions (log_event, last_user_interaction, check_morning_response, events_range). Verify WAL mode is set. Test concurrent writes via threading + multiprocessing (simulate cron + chat overlap). Verify idempotency constraint prevents duplicate system events.
2. **Wrapper script test** — Run each `~/.hermes/scripts/health_*.py` directly, verify stdout output format matches what cron prompts expect (e.g., "NEVER", "RESPONDED", "NO_RESPONSE").
3. **Source column test** — Log system and user events, verify `last_user_interaction()` only returns user events (not system checkins).
4. **UTC timestamp test** — Log events, verify all stored timestamps are UTC. Query `today_events()` across a UTC day boundary, verify correctness.
5. **Skill load test** — Run `hermes` with skill loaded via `/health`, send test messages ("walked 20 min", "smoked", "weight 71.2"), verify events persist in DB with `source='user'`.
6. **WHOOP MCP test** — Verify `mcp-hub` spawns from Hermes config (bare command, not absolute path), agent can call `mcp_whoop_get_recoveries` and get real data. Test after gateway restart.
7. **Cron dry run** — Create morning check-in job, trigger manually (`hermes cron run <job-id>`), verify Telegram message arrives with WHOOP data. Verify wrapper script output is injected into prompt.
8. **Evening reminder** — Manual trigger, verify melatonin message arrives.
9. **Noon nudge** — Manual trigger, verify supplement nudge always sends (no conditional suppression).
10. **Never miss twice** — Insert stale last-interaction timestamp (>48h), trigger morning cron, verify nudge appended. Also test with `source='system'` events only — should still trigger nudge (system events don't count as user interaction).
11. **Idempotency** — Trigger morning cron twice in same day, verify only one system checkin row exists.
12. **End-to-end** — Let it run for a full day cycle: morning check-in arrives → user types `/health took supplements, walked 20 min` → noon nudge arrives → evening reminder arrives → verify DB has correct events with correct sources.

---

## Codex Review Changelog

| # | Finding | Severity | Fix Applied |
|---|---------|----------|-------------|
| 1 | Cron script contract wrong (no CLI args allowed) | **Breaking** | Zero-arg wrapper scripts in `~/.hermes/scripts/`, import from skill module |
| 2 | Reply loop broken (cron session != chat session) | **Breaking** | Cron messages informational-only, user logs via explicit `/health` trigger |
| 3 | Delivery failure silent | Medium | Documented as known limitation (Hermes platform issue) |
| 4 | No actor/source column in events | **Breaking** | Added `source` column (`system`/`user`), filtered queries |
| 5 | Timezone/DST bugs | High | All timestamps stored as UTC, display-time conversion only |
| 6 | SQLite concurrency underspecified | High | WAL mode, busy_timeout, idempotency constraint (matches hermes_state.py) |
| 7 | MCP path hardcoded, no auto-reload | Medium | Bare `mcp-hub` command, documented gateway restart requirement |
| 8 | `[SILENT]` suppression fragile | Medium | Removed conditional suppression, noon nudge always sends |
