# Anthropic — Scaling Managed Agents: Decoupling the Brain from the Hands

**Source:** https://www.anthropic.com/engineering/managed-agents

## What it is

Anthropic's engineering post on the production architecture behind their "Managed Agents" product (`/v1/messages` with tool use abstracted away, targeted at developers who don't want to build harnesses themselves). The post is a systems-design argument: treat the agent harness the way OS designers treat hardware — *virtualize it through stable interfaces so the implementation can change without breaking callers.*

## Core architectural insight

**Brain/hands decoupling via three interface-bounded components:**

1. **Session** — an append-only event log that lives *outside* the harness. Durable state, queryable, immune to harness crashes.
2. **Harness** — the inference loop. Now stateless. Wakes on demand (`wake(sessionId)`), pulls the event log, resumes.
3. **Sandbox** — the code-execution environment. Treated as just-another-tool via `execute(name, input) → string`. Multiple sandboxes per session ("many hands"). Container failure is a catchable tool error, not session death.

Three design consequences matter:

- **Time-to-first-token dropped ~60% at p50, >90% at p95** because the harness no longer blocks on container provisioning. Inference starts immediately; containers spin up only when Claude requests one.
- **Credentials never touch the sandbox.** Either bundled into resources (git tokens initialize a clone; subsequent push/pull don't see the token) or proxied through an MCP vault. Structural defense against prompt injection.
- **Brains can pass hands to each other.** Claude-to-Claude delegation becomes trivial because hands are just tools with a uniform interface.

The deeper lesson: harness designs encode assumptions about model capability ("context anxiety" workarounds, single-container coupling). Those assumptions become "dead weight" as models improve. The fix is to virtualize so that future harness designs — ones "yet unthought of" — plug into the same interfaces.

## How it relates to Hermes

Hermes already has three of the ingredients, but they're coupled:

| Managed-agents primitive | Hermes equivalent | Coupling issue |
|--------------------------|-------------------|----------------|
| Session (external event log) | `hermes_state.py` + SQLite + FTS5 | Tightly bound to the current harness process. Crash = lose in-flight turn. |
| Harness (stateless inference loop) | Hermes CLI / Gateway / Cron entrypoints | Each entrypoint owns its own state handling; not replaceable. |
| Sandbox (tool-shaped execution) | Skill scripts (`skills/health/...`) | Runs in-process. No isolation; no credential boundary. |

The health_log contention bug Aryan just fixed (`ccc4460b fix(health): move DB connection inside threading lock to prevent SQLite contention`) is a symptom of this coupling — the session store and the harness share a process and compete for the same lock.

## What Aryan could borrow

1. **Make skill invocation look like `execute(name, input) → string` at the boundary.** Even if skills still run in-process for now, the interface should be indistinguishable from one that runs in a remote sandbox. Lets you swap in a real sandbox later (firecracker, E2B, Modal) without touching skill code.

2. **Move credentials out of the skill path entirely.** WHOOP API keys, KV API keys (`dev-kv-api-key`), Telegram tokens — none of these should appear in skill env vars. Put them behind an MCP proxy; the skill calls `mcp__whoop__get_recoveries()` and never sees auth. (Most of this is already how the Hermes MCP wiring works — the gap is skills that directly read `os.environ` for credentials.)

3. **Externalize session from harness.** The behavioral morning digest cron and the Telegram gateway currently each maintain their own context. A single append-only session log (separate from skill data) would let a crashed cron resume mid-digest and let the gateway replay context for "what did you tell me yesterday?"

4. **Design for "harnesses yet unthought of."** Aryan's Hermes vision (life advisor, not task agent) is a different harness than what ships today. If skills stay clean of harness assumptions, swapping is cheap.

## Not borrow

The full virtualization stack is overkill for a single-user agent. Container-per-sandbox provisioning, vault + MCP proxy for every credential — that's Anthropic-scale infra for Anthropic-scale adversarial surface. Aryan runs one user. Take the *interface discipline*, skip the infra.

## Key quote

> "We're unopinionated about the *specific* harness, but opinionated about the shape of these interfaces."

This is the right posture for Hermes: the skills framework is the interface contract; the harness (Claude Code, CLI, cron, future voice-only mode) is replaceable.
