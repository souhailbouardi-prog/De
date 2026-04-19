# Handoff: Health Phase 2/3 + KV Integration — Complete

**Date:** 2026-04-11
**Purpose:** Extended health module with tracking, insights, phase transitions, and knowledge-vault life advisor.

---

## Current State

**All three workstreams complete, merged, tested (33/33), and pushed.**

Branch: `claude/20260410-153325` on origin (aryanbhats/hermes-agent)

### What Was Built

**Phase 2 — Tracking & Weekly Review:**
- Extended `health_log.py` with 4 new event types (mood, weight, bloodwork, summary) and 4 new subtypes (weekly, appointment, result, photo)
- 4 new query functions: `weight_trend()`, `mood_trend()`, `weekly_summary()`, `bloodwork_status()`
- Updated `health_log_cli.py` with 4 new commands
- New cron query scripts: `health_weekly_query.py`, `health_bloodwork_query.py`
- Updated SKILL.md with mood/weight/bloodwork parsing patterns, weekly review cron context, blood work reminder cron context

**Phase 3 — Smart Insights & Phase Transition:**
- New `health_insights.py` with 5 analysis functions:
  - `sleep_recovery_correlation()` — avg recovery above/below 7.5h threshold
  - `hrv_trend_analysis()` — 7-day rolling average + direction
  - `detect_illness_signals()` — RHR spike, HRV drop, SpO2 dip detection
  - `habit_recovery_correlation()` — per-habit recovery delta
  - `check_phase_transition()` — evaluates Phase 1→2 and 2→3 criteria with blockers
- New `health_insights_cli.py` — env-var CLI wrapper (insights, phase_check)
- Updated SKILL.md with smart insight + phase transition steps in weekly review

**Knowledge-Vault Integration:**
- New `skills/advisor/life-advisor/SKILL.md` — life advisor skill that queries KV for strategic frameworks
- Added KV bridge to health SKILL.md — optional motivational framework queries when user slips
- Added `knowledge-vault` MCP server to `~/.hermes/config.yaml`

**Bug Fix:**
- Fixed pre-existing concurrency bug in `log_event()` — DB connection now opened inside threading lock

## Key Files

### New Files
- `skills/health/daily-health/scripts/health_insights.py` — correlation engine + phase transition
- `skills/health/daily-health/scripts/health_insights_cli.py` — CLI wrapper for insights
- `skills/health/daily-health/scripts/health_weekly_query.py` — cron pre-run script for weekly review
- `skills/health/daily-health/scripts/health_bloodwork_query.py` — cron pre-run script for blood work
- `skills/advisor/life-advisor/SKILL.md` — life advisor skill
- `tests/test_health_insights.py` — 12 insight tests

### Modified Files
- `skills/health/daily-health/scripts/health_log.py` — extended types/subtypes, 4 new functions, concurrency fix
- `skills/health/daily-health/scripts/health_log_cli.py` — 4 new commands
- `skills/health/daily-health/SKILL.md` — mood/weight/bloodwork patterns, weekly review, blood work reminder, KV bridge
- `tests/test_health_log.py` — 11 new tests (21 total)

### Config (outside repo)
- `~/.hermes/config.yaml` — added knowledge-vault MCP server

## Next Steps (Not Yet Done)

1. **Register cron jobs** — Add weekly review (Sunday 7PM) and blood work reminder (Wednesday 10AM) to `~/.hermes/cron/jobs.json`
2. **Install wrapper symlinks** — Run `install_wrappers.py` to create symlinks for new scripts in `~/.hermes/scripts/`
3. **Sync skills** — Run `python -c "from tools.skills_sync import sync_skills; sync_skills()"` to register advisor skill
4. **Restart gateway** — Required for new MCP tools + skills discovery
5. **Test via Telegram** — Send `/health mood 7`, `/health weight 72.1`, `/advisor how should I handle...` to verify end-to-end
6. **Fix KV MCP in Claude Code** — Config updated in `~/.claude/claude_code_config.json` with `KV_API_KEY: dev-kv-api-key`, but requires Claude Code restart to take effect
7. **KV bot Telegram fix** — Fixed: TELEGRAM_BOT_TOKEN was missing from `.env.production` on htz-sp server. Added and restarted. Bot is live.

## Gotchas

- **KV API key is `dev-kv-api-key`** — The key in `credentials.md` (`NIIUfGRV54FYbmV1pFNNioVdo4uGdgRa`) is stale. The dev key works against prod.
- **KV bot was crash-looping** — TELEGRAM_BOT_TOKEN was missing from `.env.production`. Fixed by appending to env file and recreating container (`docker compose up -d bot`). `docker restart` alone doesn't reload env files.
- **Concurrent writes bug** — `_get_conn()` was called outside `_lock` in `log_event()`, causing SQLite file-level lock contention under concurrent writes. Fixed by moving inside the lock.
- **Test xdist parallelism** — Tests run with 10 workers by default (pyproject.toml). Use `-o "addopts="` to override for sequential runs if debugging.
- **package-lock.json** has a pre-existing diff — not from this session, don't commit it.
