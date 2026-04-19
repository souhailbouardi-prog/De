# obra/superpowers

**Source:** https://github.com/obra/superpowers

Author: Jesse Vincent (@obra), longtime Perl/Git contributor, now building agent tooling.

## What it is

A skills framework + embedded development methodology for coding agents (Claude Code, Cursor, Codex, OpenCode, Copilot CLI, Gemini CLI). The framework's defining property is that **skills auto-trigger based on context** — the agent recognizes it's in a coding situation and invokes the right skill without explicit user invocation.

Unlike gstack (explicit slash commands) or agentskills.io (browsable catalog), superpowers treats skills as *mandatory process gates*. The agent can't just start writing code — it has to move through brainstorming → plan → TDD → verification, and each phase has a skill that claims authority.

## The skills (grouped)

**Methodology (the mandatory backbone):**
- `test-driven-development` — RED-GREEN-REFACTOR, forbids code before tests
- `systematic-debugging` — 4-phase root-cause; no fix without cause
- `verification-before-completion` — must run verification commands and quote output before claiming done
- `using-superpowers` — meta-skill that forces Skill tool invocation before *any* response, including clarifying questions

**Planning & execution:**
- `brainstorming` — Socratic intent-and-requirements dialog
- `writing-plans` — multi-step task breakdown
- `executing-plans` — checkpointed plan execution
- `subagent-driven-development` — dispatch fresh subagents per task
- `dispatching-parallel-agents` — for 2+ independent tasks

**Workflow:**
- `using-git-worktrees` — isolated branches for feature work
- `finishing-a-development-branch` — structured merge/PR/cleanup decision
- `requesting-code-review`, `receiving-code-review`

**Meta:**
- `writing-skills` — how to write new superpowers skills

## Core architectural insight

**Trigger descriptions are the control surface.** The auto-triggering works because each skill has a precise "Use when..." clause that describes the context in which it must fire. The agent reads these on every turn and picks the matching skill before doing anything else.

Example: `test-driven-development` triggers *"when implementing any feature or bugfix, before writing implementation code."* That description isn't documentation — it's an instruction to the harness. If Claude sees a bugfix request and doesn't invoke TDD, the meta-skill (`using-superpowers`) catches the violation.

The architectural bet is: **process discipline, encoded as skill triggers, is more reliable than prompt instructions.** Prompts drift; triggers fire on pattern match. This is the same lesson as Thariq's AskUserQuestion tool — *make it a tool, not an instruction.*

The framework claims Claude can run autonomously for hours without plan deviation. That's plausible only if the rails are structural, not prompt-based.

## How it relates to Hermes

Hermes skills currently have description fields but no explicit auto-trigger semantics. The installer (`ce81af42 chore(health): register new wrapper scripts in installer`) registers scripts but doesn't register *contextual triggers* that tell Claude "fire this skill when you see X."

Direct mappings:

| superpowers pattern | Hermes analogue | Status |
|---------------------|-----------------|--------|
| Skills with "Use when..." triggers | Skills with descriptions | Partial — descriptions exist but aren't trigger-shaped |
| Meta-skill enforcement (`using-superpowers`) | None | No gate that forces skill use before response |
| `verification-before-completion` | None | No skill that forces Hermes to quote verification output before claiming a task is done |
| `brainstorming` before implementation | Life-advisor (sort of) | Life-advisor is closer to reflection than pre-implementation dialog |
| `systematic-debugging` | None | When a Hermes skill fails (like the SQLite contention bug), no structured diagnostic path |

## What Aryan could borrow

1. **Rewrite skill description fields as trigger clauses.** Every Hermes skill should start with `Use when...` describing the exact situation in which Claude should fire it. This is the single cheapest improvement — no code change, just prose. Health-log's description should be `Use when the user reports a workout, meal, symptom, or mood, OR when the daily cron fires at 21:00 local time.`

2. **Add a `verification-before-completion` discipline for Hermes skills that ship outputs.** The morning digest skill currently generates insights and sends. A verification gate would force it to *quote the exact KV source and WHOOP data* backing each claim before send — borrowing superpowers' "evidence before assertions" principle.

3. **Systematic debugging as a skill.** The health_log contention fix (`ccc4460b`) was debugged manually. If Hermes had a `systematic-debugging` skill with the 4-phase shape (investigate → analyze → hypothesize → implement), Claude could apply it next time a skill misbehaves.

4. **Brainstorming as a precondition for new skill creation.** Every new Hermes skill Aryan adds should pass through a structured intent-dialog first. Superpowers' `brainstorming` skill is directly copyable.

## vs. gstack

Both are Claude Code skill packs. The design divergence is instructive:

|  | gstack | superpowers |
|--|--------|-------------|
| Invocation | Explicit slash command | Auto-trigger on context |
| Target user | Solo founder shipping features | Agent running unattended |
| Skill granularity | Role-based (CEO, QA, eng) | Methodology-based (TDD, debug, verify) |
| Overlap skills | `/review`, `/investigate`, `/ship` | `requesting-code-review`, `systematic-debugging`, `finishing-a-development-branch` |
| Best for Hermes | Decision-forcing roles | Auto-triggered methodology |

**For Hermes specifically, superpowers' auto-trigger model is the better fit** because Hermes runs on crons and voice input — the user isn't typing slash commands. Skills need to fire based on what Claude sees, not what Aryan types.

## Not borrow

The coding-centric skills (worktrees, TDD, code review) don't apply to Hermes's life-advisor use case. The *auto-trigger pattern* applies universally; the skill *content* is coding-specific.

Also don't borrow the "mandatory" posture. Superpowers' enforcement is aggressive — skills *must* fire, meta-skills police violations. For a single-user life advisor, that's overkill and probably annoying. Borrow the trigger format, skip the enforcement.

## Key quote

> "It starts from the moment you fire up your coding agent. As soon as it sees that you're building something, it *doesn't* just jump into trying to write code."

The Hermes translation: *as soon as Hermes sees Aryan is making a life decision, it doesn't just jump into advising — it runs brainstorming first.*
