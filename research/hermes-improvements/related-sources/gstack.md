# Garry Tan — gstack

**Source:** https://github.com/garrytan/gstack

## What it is

An opinionated Claude Code plugin pack (marketed as "15 tools," currently 23 slash commands) built by YC CEO Garry Tan. Each command encodes a *role* from a functional startup — CEO review, eng review, design review, QA lead, release engineer, security officer — and scripts Claude to play that role against the current codebase.

The core bet: **a solo builder with the right structured prompts can move at the velocity of a 20-person team** because the bottleneck isn't capacity, it's the discipline to switch hats.

## The commands (grouped)

**Planning & review (role plays):**
- `/office-hours` — YC-style founder interrogation (6 forcing questions)
- `/plan-ceo-review` — scope challenge in 4 modes (expand, selective, hold, reduce)
- `/plan-eng-review` — architecture lock-in, data-flow diagrams, edge cases
- `/plan-design-review` — 0-10 dimensional design scoring
- `/plan-devex-review` — developer experience audit
- `/autoplan` — pipelines CEO → eng → design review with decision principles

**Design:**
- `/design-consultation` — builds a design system from scratch
- `/design-shotgun` — generates 4-6 AI mockup variants for comparison
- `/design-html` — converts mockup to production HTML/CSS
- `/design-review` — visual QA with auto-fixes + atomic commits

**Execution & QA:**
- `/review` — staff engineer PR review, auto-fixes obvious bugs
- `/investigate` — 4-phase root-cause debugging (no fix without cause)
- `/qa` — runs and fixes QA; `/qa-only` reports without fixing
- `/cso` — OWASP + STRIDE threat model
- `/benchmark` — Core Web Vitals perf regression
- `/canary` — post-deploy anomaly watch

**Ship & reflect:**
- `/ship`, `/land-and-deploy`, `/document-release`, `/retro`

**Safety:**
- `/careful` (warns on destructive cmds), `/freeze` (scope edits to a dir), `/guard` (both), `/codex` (OpenAI Codex second opinion)

**Infrastructure:**
- `/browse`, `/setup-browser-cookies`, `/learn`, `/pair-agent`

## Core architectural insight

gstack isn't a framework, it's **an opinionated decision-forcing function.** Each command has a fixed structure (e.g., CEO review's 4 modes, office-hours' 6 questions). Claude *must* answer those specific prompts — improvisation is designed out.

This is the inverse of obra/superpowers' auto-triggering. gstack wants the builder to explicitly invoke the right role at the right moment; superpowers wants skills to fire based on context. Both are valid; they optimize different things:
- **gstack optimizes for quality per stage** — every stage has a definitive review before moving on.
- **superpowers optimizes for autonomy duration** — the agent can run for hours without hand-holding because the rails are built in.

The secondary insight is **CLAUDE.md as router.** gstack installs itself into `CLAUDE.md` with trigger descriptions that teach Claude *when to suggest* each skill. The skills aren't just callable — they're *recommendable* by the agent itself.

## How it relates to Hermes

Aryan's global `~/.claude/CLAUDE.md` already references `/browse` from gstack. Beyond that, Hermes has no structured review layer — skills execute, write to SQLite, and exit. There's no equivalent of `/plan-ceo-review` asking "is this the right problem?" before acting.

Key overlap with Hermes primitives:

| gstack concept | Hermes equivalent | Gap |
|----------------|-------------------|-----|
| Role-based commands | Skill scripts | Hermes skills are capability-based, not role-based |
| CLAUDE.md router with trigger descriptions | Project `.claude/CLAUDE.md` | Present but under-used for skill discovery |
| Pre-commit review gates | None | No forcing function before skill output is committed to KV or sent to user |
| Retrospective (`/retro`) | None | No weekly reflection on what Hermes did and whether it helped |

## What Aryan could borrow

1. **Role-based reflection cron.** Add a weekly `/retro`-style Hermes cron that reviews the last 7 days of skill invocations and asks: what helped? what was noise? which skills fired and weren't needed? Not a code review — a *usage* review.

2. **Decision-forcing skill for life decisions.** The life-advisor skill currently synthesizes. A stronger variant would force the 4-mode CEO-review shape: *Expand (what bigger bet does this point to?), Selective (what piece of the bigger bet is ready now?), Hold (keep current scope, here's why), Reduce (this is the wrong frame, narrow it).* That shape is directly transplantable.

3. **`/freeze` and `/careful` for skill development.** When Aryan iterates on a skill (e.g., the health_log threading fix), scope edits to `skills/health/` and warn on anything that touches production data. Borrow the patterns, not the tools.

4. **The autoplan pipeline as a model for Hermes cron chains.** autoplan runs CEO → eng → design review sequentially with decision principles. The behavioral morning digest could be structured the same way: gather data → review frame → challenge assumption → ship insight.

## Not borrow

The full 23-command surface. Aryan isn't shipping a SaaS; most commands (design-shotgun, canary, land-and-deploy) don't apply. Borrow the *shape* (role-based, decision-forcing, CLAUDE.md-routed) for Hermes-relevant use cases only.

The other non-borrow is gstack's *density.* gstack assumes you're actively writing code in a single project. Hermes runs in the background, across many projects. Skill triggers need to work without the user explicitly invoking them — which is why obra/superpowers' auto-trigger model (next file) is a better template for cron-driven workflows.

## Key insight for Hermes

**CLAUDE.md is the router.** Whatever skills Hermes has, the `CLAUDE.md` at the project root is where Claude learns *which skills exist, when to use them, and what order to chain them.* gstack's most copyable artifact isn't any single skill — it's the structured trigger-description format in its CLAUDE.md.
