# Handoff: Health Module MVP — Complete & Live

**Date:** 2026-04-10
**Purpose:** Daily health coach module for Hermes is built, tested, and running on Telegram with WHOOP integration.

---

## Current State

**MVP is complete and live.** All Phase 1 features from the brief are working:
- Morning WHOOP check-in (10:30 AM cron) — pulls recovery, HRV, RHR, SpO2, sleep data via mcp-hub
- Evening melatonin reminder (7:30 PM cron)
- Noon supplement nudge (12:00 PM cron)
- `/health` command for conversational habit logging with parsed-field echo-back
- "Never miss twice" detection (>48h no user interaction → nudge)
- SQLite storage with WAL mode, source attribution (system/user), idempotency
- Input validation (rejects invalid types/subtypes)
- Codex adversarial review applied (8 findings fixed in spec v2)

**Kimi K2.5 configured** as the LLM provider for Hermes (via kimi-coding provider, auto-routes to api.kimi.com/coding/v1).

**Fork setup:** origin → aryanbhats/hermes-agent, upstream → NousResearch/hermes-agent.

## Key Files

### Skill (in repo)
- `skills/health/daily-health/SKILL.md` — skill definition (name: health, triggers: /health)
- `skills/health/daily-health/scripts/health_log.py` — SQLite event library (5 public functions)
- `skills/health/daily-health/scripts/health_log_cli.py` — CLI wrapper (env var based)
- `skills/health/daily-health/scripts/health_morning_query.py` — cron pre-run script
- `skills/health/daily-health/scripts/health_noon_query.py` — cron pre-run script
- `skills/health/daily-health/scripts/install_wrappers.py` — symlink installer
- `skills/health/daily-health/references/aryan-health-profile.md` — condensed health profile
- `tests/test_health_log.py` — 10 unit tests (all passing)

### Design docs (in repo)
- `docs/superpowers/specs/2026-04-10-daily-health-module-design.md` — design spec v2
- `docs/superpowers/plans/2026-04-10-daily-health-module.md` — implementation plan

### Config (outside repo)
- `~/.hermes/config.yaml` — model (kimi-k2.5), mcp_servers (whoop + gws), telegram home channel
- `~/.hermes/scripts/health_*.py` — symlinks to skill scripts (created by install_wrappers.py)
- `~/.hermes/cron/jobs.json` — 3 health cron jobs registered
- `~/.hermes/health/health.db` — SQLite database with health events

### Brief (separate project)
- `/Users/aryanbhatia/Documents/0DevProjects/aryan-health/hermes-health-agent-brief.md` — original brief

## Next Steps

1. **Phase 2 features** (from brief):
   - Weekly review (Sunday evening — pull 7 days WHOOP, summarize trends, insights)
   - Blood work appointment tracking (remind weekly until booked)
   - Mood logging with trend tracking
   - Weight logging integration

2. **Phase 3 features** (future):
   - Smart insights (correlate sleep time with recovery scores)
   - Phase transition detection (suggest Phase 1 → Phase 2 when recovery gates met)

3. **Broader Hermes vision** — knowledge-vault MCP integration for life advisor capabilities (see memory: project_hermes_vision.md)

## Gotchas

- **Skill name must be "health" not "daily-health"** — Telegram sanitizes dashes to underscores, so `daily-health` became `/daily_health` which users couldn't find. Fixed to `name: health`.
- **mcp-hub needs absolute path** in config.yaml — bare `mcp-hub` command wasn't on the gateway's PATH. Use `/Users/aryanbhatia/Documents/0DevProjects/mcp-hub/.venv/bin/mcp-hub`.
- **Gateway restart required** after adding MCP servers or updating skills — MCP tools discovered at startup only.
- **Skills must be synced** — run `python -c "from tools.skills_sync import sync_skills; sync_skills()"` after modifying skill files, then restart gateway.
- **Cron scripts must be zero-arg** — Hermes runs `python <path>` with no CLI args. Wrapper scripts at `~/.hermes/scripts/` use sys.path.insert + env vars instead.
- **Cron messages are informational only** — cron sessions are isolated from gateway chat. User replies go to different session. Don't ask questions in cron prompts.
- **Kimi API requires User-Agent: KimiCLI/1.3** — Hermes sends this automatically. Direct curl calls to api.kimi.com/coding/v1 without this header get rejected.
- **PR created against NousResearch** (not fork) — PR #7419 at NousResearch/hermes-agent. Won't merge (no write access) but tracks the work.
- **package-lock.json has a pre-existing diff** — not from this session, don't commit it.
- **Branch:** claude/20260410-153325 on origin (aryanbhats/hermes-agent)
