# Daily Health Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Hermes skill that acts as a daily health coach via Telegram — delivers WHOOP check-ins, logs habits, sends reminders, and detects disengagement.

**Architecture:** Pure Skill (SKILL.md + scripts + cron jobs). SQLite for event persistence with WAL mode. Cron jobs deliver informational messages to Telegram. User interacts via explicit `/health` trigger. WHOOP data via mcp-hub stdio MCP server.

**Tech Stack:** Python 3.11+, sqlite3 (stdlib), Hermes skill system, Hermes cron scheduler, mcp-hub (WHOOP OAuth)

**Spec:** `docs/superpowers/specs/2026-04-10-daily-health-module-design.md` (v2)

---

## File Structure

```
# New files to create:
skills/health/daily-health/SKILL.md                    # Skill definition + agent instructions
skills/health/daily-health/scripts/health_log.py       # SQLite health event library
skills/health/daily-health/references/aryan-health-profile.md  # Condensed health profile
tests/test_health_log.py                               # Unit tests for health_log module

# Files created at runtime (by setup script, not committed):
~/.hermes/scripts/health_morning_query.py              # Cron wrapper: last user interaction
~/.hermes/scripts/health_noon_query.py                 # Cron wrapper: morning response check
~/.hermes/scripts/health_log_cli.py                    # CLI wrapper for agent terminal calls
~/.hermes/health/health.db                             # SQLite database (auto-created)

# Files to modify:
~/.hermes/config.yaml                                  # Add mcp_servers.whoop entry
```

---

### Task 1: health_log.py — SQLite Event Library

**Files:**
- Create: `skills/health/daily-health/scripts/health_log.py`
- Create: `tests/test_health_log.py`

- [ ] **Step 1: Write failing tests for health_log module**

Create `tests/test_health_log.py`:

```python
#!/usr/bin/env python3
"""Tests for health_log SQLite event library."""
import json
import os
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Will be importable after Step 3
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "health" / "daily-health" / "scripts"))


class TestHealthLog(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_health.db")
        os.environ["HEALTH_DB_PATH"] = self.db_path

        # Re-import to pick up new env var
        import importlib
        import health_log
        importlib.reload(health_log)
        self.hl = health_log

    def tearDown(self):
        os.environ.pop("HEALTH_DB_PATH", None)

    def test_log_event_basic(self):
        self.hl.log_event(type="habit", subtype="walk", source="user", value=25, unit="min")
        events = self.hl.today_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "habit")
        self.assertEqual(events[0]["subtype"], "walk")
        self.assertEqual(events[0]["source"], "user")
        self.assertAlmostEqual(events[0]["value"], 25.0)

    def test_log_event_with_data_json(self):
        data = {"recovery": 95, "hrv": 94.8}
        self.hl.log_event(type="checkin", source="system", data=data)
        events = self.hl.today_events()
        self.assertEqual(len(events), 1)
        parsed = json.loads(events[0]["data"])
        self.assertEqual(parsed["recovery"], 95)

    def test_timestamps_are_utc(self):
        self.hl.log_event(type="habit", subtype="supplement", source="user")
        events = self.hl.today_events()
        ts = events[0]["ts"]
        self.assertTrue(ts.endswith("Z") or "+00:00" in ts, f"Timestamp not UTC: {ts}")

    def test_last_user_interaction_ignores_system(self):
        self.hl.log_event(type="checkin", source="system")
        result = self.hl.last_user_interaction()
        self.assertIsNone(result, "System events should not count as user interaction")

        self.hl.log_event(type="response", source="user")
        result = self.hl.last_user_interaction()
        self.assertIsNotNone(result)

    def test_check_morning_response_false(self):
        self.hl.log_event(type="checkin", source="system")
        self.assertFalse(self.hl.check_morning_response())

    def test_check_morning_response_true(self):
        self.hl.log_event(type="checkin", source="system")
        self.hl.log_event(type="response", source="user")
        self.assertTrue(self.hl.check_morning_response())

    def test_events_range(self):
        self.hl.log_event(type="habit", subtype="walk", source="user", value=20)
        events = self.hl.events_range(7)
        self.assertEqual(len(events), 1)

    def test_system_event_idempotency(self):
        self.hl.log_event(type="checkin", source="system", data={"recovery": 90})
        self.hl.log_event(type="checkin", source="system", data={"recovery": 95})
        events = self.hl.today_events()
        system_checkins = [e for e in events if e["type"] == "checkin" and e["source"] == "system"]
        self.assertEqual(len(system_checkins), 1, "Duplicate system checkin should be ignored")

    def test_wal_mode_enabled(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        self.assertEqual(mode, "wal")

    def test_concurrent_writes(self):
        errors = []

        def writer(source, n):
            try:
                for i in range(n):
                    self.hl.log_event(
                        type="habit", subtype="walk", source=source,
                        value=float(i), note=f"thread-{source}-{i}"
                    )
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=writer, args=("user", 20))
        t2 = threading.Thread(target=writer, args=("user", 20))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Concurrent write errors: {errors}")
        events = self.hl.today_events()
        self.assertEqual(len(events), 40)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/aryanbhatia/Documents/0DevProjects/hermes-agent && python -m pytest tests/test_health_log.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'health_log'`

- [ ] **Step 3: Implement health_log.py**

Create `skills/health/daily-health/scripts/health_log.py`:

```python
#!/usr/bin/env python3
"""SQLite-backed health event logging and queries.

This is a library module — import it from wrapper scripts or tests.
DB location: HEALTH_DB_PATH env var, or ~/.hermes/health/health.db
"""
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

_lock = threading.Lock()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS health_events (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',
    type TEXT NOT NULL,
    subtype TEXT,
    value REAL,
    unit TEXT,
    data TEXT,
    note TEXT
);
CREATE INDEX IF NOT EXISTS idx_ts ON health_events(ts);
CREATE INDEX IF NOT EXISTS idx_type ON health_events(type);
CREATE INDEX IF NOT EXISTS idx_type_ts ON health_events(type, ts);
CREATE INDEX IF NOT EXISTS idx_source_ts ON health_events(source, ts);
CREATE UNIQUE INDEX IF NOT EXISTS idx_system_daily ON health_events(date(ts), type, source)
    WHERE source = 'system' AND type IN ('checkin', 'evening', 'nudge');
"""


def _db_path() -> Path:
    override = os.environ.get("HEALTH_DB_PATH")
    if override:
        return Path(override)
    hermes_home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    return hermes_home / "health" / "health.db"


def _get_conn() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(path),
        check_same_thread=False,
        timeout=5.0,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA_SQL)
    return conn


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_utc_start() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")


def log_event(
    type: str,
    subtype: str = None,
    source: str = "user",
    value: float = None,
    unit: str = None,
    data: dict = None,
    note: str = None,
) -> None:
    """Insert a health event. System events are deduplicated per day."""
    ts = _utc_now()
    data_str = json.dumps(data) if data else None
    conn = _get_conn()
    with _lock:
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO health_events (ts, source, type, subtype, value, unit, data, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, source, type, subtype, value, unit, data_str, note),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            # Idempotency: duplicate system event for today — update instead
            conn.execute("ROLLBACK")
            if source == "system":
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    "UPDATE health_events SET ts=?, data=?, note=? "
                    "WHERE date(ts)=date(?) AND type=? AND source='system'",
                    (ts, data_str, note, ts, type),
                )
                conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()


def last_user_interaction() -> str | None:
    """Return UTC ISO timestamp of the most recent source='user' event, or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT ts FROM health_events WHERE source='user' ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        return row["ts"] if row else None
    finally:
        conn.close()


def today_events() -> list[dict]:
    """Return all events for today (UTC day boundary)."""
    start = _today_utc_start()
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM health_events WHERE ts >= ? ORDER BY ts", (start,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def check_morning_response() -> bool:
    """Return True if today's system checkin has a subsequent user response."""
    start = _today_utc_start()
    conn = _get_conn()
    try:
        checkin = conn.execute(
            "SELECT ts FROM health_events WHERE ts >= ? AND type='checkin' AND source='system' LIMIT 1",
            (start,),
        ).fetchone()
        if not checkin:
            return False
        response = conn.execute(
            "SELECT 1 FROM health_events WHERE ts > ? AND source='user' LIMIT 1",
            (checkin["ts"],),
        ).fetchone()
        return response is not None
    finally:
        conn.close()


def events_range(days: int) -> list[dict]:
    """Return all events from the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM health_events WHERE ts >= ? ORDER BY ts", (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/aryanbhatia/Documents/0DevProjects/hermes-agent && python -m pytest tests/test_health_log.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/health/daily-health/scripts/health_log.py tests/test_health_log.py
git commit -m "feat(health): add SQLite health event library with tests"
```

---

### Task 2: Cron Wrapper Scripts

**Files:**
- Create: `skills/health/daily-health/scripts/health_morning_query.py`
- Create: `skills/health/daily-health/scripts/health_noon_query.py`
- Create: `skills/health/daily-health/scripts/health_log_cli.py`
- Create: `skills/health/daily-health/scripts/install_wrappers.py`

These scripts live in the skill repo but get symlinked/copied to `~/.hermes/scripts/` at install time. The wrappers are zero-arg Python scripts that import from health_log.

- [ ] **Step 1: Create health_morning_query.py**

Create `skills/health/daily-health/scripts/health_morning_query.py`:

```python
#!/usr/bin/env python3
"""Cron pre-run script: prints last user interaction timestamp.

Must be installed to ~/.hermes/scripts/ (zero-arg, no CLI args).
"""
import sys
from pathlib import Path

# Add skill scripts dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from health_log import last_user_interaction

ts = last_user_interaction()
print(ts or "NEVER")
```

- [ ] **Step 2: Create health_noon_query.py**

Create `skills/health/daily-health/scripts/health_noon_query.py`:

```python
#!/usr/bin/env python3
"""Cron pre-run script: prints whether morning checkin was responded to.

Must be installed to ~/.hermes/scripts/ (zero-arg, no CLI args).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from health_log import check_morning_response

print("RESPONDED" if check_morning_response() else "NO_RESPONSE")
```

- [ ] **Step 3: Create health_log_cli.py**

Create `skills/health/daily-health/scripts/health_log_cli.py`:

```python
#!/usr/bin/env python3
"""CLI wrapper for agent to call health_log functions via terminal tool.

Usage (from agent terminal tool):
    HEALTH_LOG_CMD=log HEALTH_LOG_ARGS='{"type":"habit","subtype":"walk","value":25}' python health_log_cli.py
    HEALTH_LOG_CMD=last_interaction python health_log_cli.py
    HEALTH_LOG_CMD=today python health_log_cli.py
    HEALTH_LOG_CMD=range HEALTH_LOG_ARGS='{"days":7}' python health_log_cli.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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

- [ ] **Step 4: Create install_wrappers.py**

Create `skills/health/daily-health/scripts/install_wrappers.py`:

```python
#!/usr/bin/env python3
"""Install cron wrapper scripts to ~/.hermes/scripts/.

Creates symlinks from ~/.hermes/scripts/ pointing to the skill's script files.
Run once after cloning or updating the skill.

Usage: python install_wrappers.py
"""
import os
from pathlib import Path

HERMES_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
SCRIPTS_DIR = HERMES_HOME / "scripts"
SKILL_SCRIPTS = Path(__file__).resolve().parent

WRAPPERS = [
    "health_morning_query.py",
    "health_noon_query.py",
    "health_log_cli.py",
]


def install():
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    for name in WRAPPERS:
        src = SKILL_SCRIPTS / name
        dst = SCRIPTS_DIR / name
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        dst.symlink_to(src)
        print(f"  {dst} -> {src}")
    print(f"Installed {len(WRAPPERS)} wrapper scripts to {SCRIPTS_DIR}")


if __name__ == "__main__":
    install()
```

- [ ] **Step 5: Test the wrapper scripts manually**

```bash
cd /Users/aryanbhatia/Documents/0DevProjects/hermes-agent
python skills/health/daily-health/scripts/install_wrappers.py
python ~/.hermes/scripts/health_morning_query.py
# Expected output: NEVER
python ~/.hermes/scripts/health_noon_query.py
# Expected output: NO_RESPONSE
```

- [ ] **Step 6: Commit**

```bash
git add skills/health/daily-health/scripts/health_morning_query.py \
       skills/health/daily-health/scripts/health_noon_query.py \
       skills/health/daily-health/scripts/health_log_cli.py \
       skills/health/daily-health/scripts/install_wrappers.py
git commit -m "feat(health): add cron wrapper scripts and installer"
```

---

### Task 3: Health Profile Reference

**Files:**
- Create: `skills/health/daily-health/references/aryan-health-profile.md`

- [ ] **Step 1: Read the source health profile**

Read these files to extract the condensed profile:
- `/Users/aryanbhatia/Documents/0DevProjects/aryan-health/research/00-health-profile.md`
- `/Users/aryanbhatia/Documents/0DevProjects/aryan-health/research/START-HERE.md`
- `/Users/aryanbhatia/Documents/0DevProjects/aryan-health/research/07-supplements/old-vs-new-stack.md`

- [ ] **Step 2: Write the condensed profile**

Create `skills/health/daily-health/references/aryan-health-profile.md`:

The file should contain ONLY what the agent needs for daily interactions:
- Bio: 21M, 187cm, 71kg, Toronto, BMO GAM intern starting mid-May 2026
- Conditions: subclinical hypothyroidism (TSH 4.99), lichen planus, childhood asthma, recently quit smoking, recovering from bacterial bronchitis, severely deconditioned cardio (walking HR 137-191, VO2max ~25)
- Current phase: Recovery → Phase 1 (fix sleep, walk daily, supplements, don't smoke, nebulize)
- Daily priorities: sunlight 10min, supplements with breakfast, nebulize, cyclic sighing 5min, walk 20-30min, melatonin 0.5mg at 7:30 PM, bed by midnight
- Supplement stack: condensed list of current supplements
- Medications: Oracort 0.1% (oral LP), Budecort nebulizer 2x/day
- Behavioral notes: video game mindset, identity-based framing, "never miss twice", collapses on single disruption
- Tone: direct not preachy, zero judgment on slips, brief messages

Do NOT include full research, session logs, or predictive models.

- [ ] **Step 3: Commit**

```bash
git add skills/health/daily-health/references/aryan-health-profile.md
git commit -m "docs(health): add condensed health profile reference"
```

---

### Task 4: SKILL.md

**Files:**
- Create: `skills/health/daily-health/SKILL.md`

- [ ] **Step 1: Write the skill definition**

Create `skills/health/daily-health/SKILL.md`:

```markdown
---
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
---

# Daily Health Coach

You are Aryan's health coach. You help him track habits, review WHOOP data, and stay consistent.

## Who Is Aryan

See `references/aryan-health-profile.md` for his full health profile. Key points:
- 21M, recovering from smoking + bronchitis, severely deconditioned
- Current phase: Recovery → Phase 1 (fix sleep, walk, supplements, don't smoke)
- Responds to identity-based framing, video game mindset
- Collapses systems on single disruption — "never miss twice" is critical

## How to Respond to /health Messages

When the user sends `/health` followed by natural language, parse and log the event.

### Habit Patterns

| User says | Log as |
|-----------|--------|
| "walked 25 min" | type=habit, subtype=walk, value=25, unit=min |
| "took supplements" | type=habit, subtype=supplement |
| "smoked" or "had a cigarette" | type=habit, subtype=smoke |
| "nebulized" | type=habit, subtype=nebulize |
| "cyclic sighing 5 min" | type=habit, subtype=sighing, value=5, unit=min |
| "weight 71.2" | type=habit, subtype=weight, value=71.2 |
| "had chicken rice eggs" | type=habit, subtype=meal, note="chicken rice eggs", data={"protein_est": <estimate>} |
| "mood 4" or "feeling good" | type=evening, value=<1-5> |
| "wheeze less today" | type=symptom, note="wheeze less today" |
| "clean today" or "didn't smoke" | type=response, data={"smoked": false} |

### How to Log

Run via terminal tool:
```bash
HEALTH_LOG_CMD=log HEALTH_LOG_ARGS='{"type":"habit","subtype":"walk","source":"user","value":25,"unit":"min"}' python ~/.hermes/scripts/health_log_cli.py
```

### Response Style

After logging, confirm briefly:
- Walk: "Logged 25 min walk."
- Supplements: "Logged. Keep stacking."
- Smoked: "Noted. One slip doesn't undo your progress. Don't buy a pack. Tomorrow is a new day."
- Weight: "71.2 kg logged."
- Meal: "Logged. ~45g protein estimate."

**Rules:**
- Direct, not preachy. No lectures.
- Zero judgment on slips. Log it and move on.
- Brief. One line confirmations. No walls of text.
- Identity-based: "You're someone who shows up" not "You need to do X"
- Data-driven: reference actual numbers when available

## Morning Check-In (Cron Job Context)

When running as a cron job for the morning check-in:

1. Call `mcp_whoop_get_recoveries` with limit=1 to get last night's recovery
2. Call `mcp_whoop_get_sleeps` with limit=1 to get last night's sleep
3. Format a brief Telegram message:

```
Good morning. Here's last night:
Recovery: {score}% | HRV: {hrv} | RHR: {rhr} | SpO2: {spo2}%
Sleep: {hours}h {min}min | Deep: {deep} | REM: {rem}

3 things today:
1. Sunlight at window (10 min)
2. Supplements with breakfast
3. Nebulize

Type /health to log habits anytime.
```

4. Log the WHOOP data as a system checkin:
```bash
HEALTH_LOG_CMD=log HEALTH_LOG_ARGS='{"type":"checkin","source":"system","data":{...whoop data...}}' python ~/.hermes/scripts/health_log_cli.py
```

5. Check the script output (injected before prompt). If it says "NEVER" or the timestamp is >48h ago, append:
```
Hey — haven't heard from you in 2 days. Everything okay?
Missing once is fine. Missing twice starts a new habit.
Even just saying /health alive counts.
```

## Evening Reminder (Cron Job Context)

When running as a cron job for the evening reminder:
- Send: "Melatonin time. Take half a tab now. Blue light glasses on in an hour."
- Log as system evening event

## Noon Nudge (Cron Job Context)

When running as a cron job for the noon supplement nudge:
- Send: "Hey — did you take your supplements? Just checking."
- Log as system nudge event (subtype: noon)
```

- [ ] **Step 2: Verify skill loads in Hermes**

```bash
cd /Users/aryanbhatia/Documents/0DevProjects/hermes-agent
# List skills to confirm daily-health appears
python -c "
import sys; sys.path.insert(0, '.')
from agent.skill_utils import find_skill
result = find_skill('daily-health')
print('Found:', result)
"
```

- [ ] **Step 3: Commit**

```bash
git add skills/health/daily-health/SKILL.md
git commit -m "feat(health): add daily-health skill definition"
```

---

### Task 5: WHOOP MCP Configuration

**Files:**
- Modify: `~/.hermes/config.yaml`

- [ ] **Step 1: Create mcp-hub symlink (if not on PATH)**

```bash
which mcp-hub 2>/dev/null || ln -sf ~/Documents/0DevProjects/mcp-hub/.venv/bin/mcp-hub /usr/local/bin/mcp-hub
which mcp-hub
# Expected: /usr/local/bin/mcp-hub (or existing path)
```

- [ ] **Step 2: Add WHOOP MCP to config.yaml**

Read `~/.hermes/config.yaml`, then add the `mcp_servers` section:

```yaml
mcp_servers:
  whoop:
    command: mcp-hub
    args: ["serve", "-s", "whoop", "--transport", "stdio"]
    timeout: 120
    connect_timeout: 60
```

- [ ] **Step 3: Test WHOOP MCP connection**

```bash
mcp-hub serve -s whoop --transport stdio <<< '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' 2>/dev/null | head -5
```

Expected: JSON response listing WHOOP tools

- [ ] **Step 4: Commit (config is outside repo — note in commit message)**

No git commit needed — config.yaml is at `~/.hermes/config.yaml` (outside repo).

---

### Task 6: Register Cron Jobs

**Files:**
- Modify: `~/.hermes/cron/jobs.json` (via Hermes cron tool or direct edit)

- [ ] **Step 1: Install wrapper scripts**

```bash
python skills/health/daily-health/scripts/install_wrappers.py
```

- [ ] **Step 2: Create morning check-in cron job**

Use Hermes CLI or direct edit. The job:

```json
{
  "name": "health-morning-checkin",
  "schedule": "30 10 * * *",
  "skills": ["daily-health"],
  "prompt": "Run the morning health check-in. Pull last night's WHOOP data via mcp_whoop_get_recoveries (limit=1) and mcp_whoop_get_sleeps (limit=1). Format as a brief Telegram summary. Add 3 daily tasks from current phase priorities. Log the WHOOP data as a system checkin event via the terminal tool. Check the script output for last user interaction time — if it says NEVER or the timestamp is >48h ago, append the never-miss-twice nudge. Do NOT ask questions — this is informational only.",
  "deliver": "telegram",
  "script": "health_morning_query.py"
}
```

- [ ] **Step 3: Create evening reminder cron job**

```json
{
  "name": "health-evening-reminder",
  "schedule": "30 19 * * *",
  "skills": ["daily-health"],
  "prompt": "Send the evening melatonin reminder: 'Melatonin time. Take half a tab now. Blue light glasses on in an hour.' Log this as a system evening event via the terminal tool. Do NOT ask questions.",
  "deliver": "telegram"
}
```

- [ ] **Step 4: Create noon supplement nudge cron job**

```json
{
  "name": "health-noon-nudge",
  "schedule": "0 12 * * *",
  "skills": ["daily-health"],
  "prompt": "Send a brief supplement nudge: 'Hey — did you take your supplements? Just checking.' Log this as a system nudge event (subtype: noon) via the terminal tool.",
  "deliver": "telegram"
}
```

- [ ] **Step 5: Verify cron jobs are registered**

```bash
cd /Users/aryanbhatia/Documents/0DevProjects/hermes-agent
python -c "
import json
from pathlib import Path
jobs = json.loads((Path.home() / '.hermes/cron/jobs.json').read_text())
health_jobs = [j for j in jobs if j.get('name','').startswith('health-')]
for j in health_jobs:
    print(f\"{j['name']}: {j['schedule']} deliver={j.get('deliver')}\")
print(f'Total health jobs: {len(health_jobs)}')
"
```

Expected: 3 health jobs listed

---

### Task 7: End-to-End Verification

**Files:** None (testing only)

- [ ] **Step 1: Test health_log.py via CLI wrapper**

```bash
# Log a test event
HEALTH_LOG_CMD=log HEALTH_LOG_ARGS='{"type":"habit","subtype":"walk","source":"user","value":20,"unit":"min","note":"test walk"}' python ~/.hermes/scripts/health_log_cli.py
# Expected: OK

# Check today's events
HEALTH_LOG_CMD=today python ~/.hermes/scripts/health_log_cli.py
# Expected: JSON array with the walk event

# Check last interaction
HEALTH_LOG_CMD=last_interaction python ~/.hermes/scripts/health_log_cli.py
# Expected: UTC timestamp

# Check morning response
python ~/.hermes/scripts/health_noon_query.py
# Expected: NO_RESPONSE (no system checkin today)
```

- [ ] **Step 2: Test morning cron job manually**

Trigger the morning check-in cron job. This requires the Hermes gateway to be running with WHOOP MCP loaded:

```bash
# Restart gateway to pick up WHOOP MCP config
# Then trigger:
hermes cron run health-morning-checkin
```

Verify:
- Telegram message arrives with WHOOP data
- `~/.hermes/health/health.db` has a system checkin event
- Cron output saved to `~/.hermes/cron/output/`

- [ ] **Step 3: Test /health interaction**

Start a Hermes session and test:
```
/health walked 20 min
/health took supplements
/health mood 4
```

Verify each logs to the DB:
```bash
HEALTH_LOG_CMD=today python ~/.hermes/scripts/health_log_cli.py
```

- [ ] **Step 4: Test evening reminder**

```bash
hermes cron run health-evening-reminder
```

Verify Telegram message arrives.

- [ ] **Step 5: Test noon nudge**

```bash
hermes cron run health-noon-nudge
```

Verify Telegram message arrives.

- [ ] **Step 6: Test never-miss-twice detection**

Clear the DB and verify the morning cron detects no prior user interaction:

```bash
# Check with empty DB (no user events)
python ~/.hermes/scripts/health_morning_query.py
# Expected: NEVER

# Trigger morning cron — should include the nudge
hermes cron run health-morning-checkin
# Verify Telegram message includes "haven't heard from you"
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "feat(health): complete daily health module MVP"
```
