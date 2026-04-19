# Thariq Shihipar — Seeing Like an Agent

**Source:** https://claude.com/blog/seeing-like-an-agent (canonical); thread at https://x.com/trq212/status/2027463795355095314

Author: Thariq Shihipar, MTS at Anthropic working on Claude Code.

## What it is

A short design-philosophy essay from the Claude Code team on how they design tools *for the way Claude actually reasons*, rather than for how a human would expect an API to look. The term "model empathy" (picked up by AutoAgent research and others) originates here.

## Core architectural insight

Tool design for agents is an empirical craft, not a spec-driven one. You cannot deduce a good tool from first principles — you must observe Claude using it, watch it fail, and iterate. The essay phrases it: *"seeing like an agent is an art, not a science."*

Five concrete principles:

1. **Progressive disclosure.** Don't expose all context upfront. Let the model search, then read, then follow references. This tracks how a capable human investigator works — broad-then-narrow — and keeps the context window clean.

2. **The bar for adding a tool is high.** Every new tool is one more option the model must consider on every turn. Prefer composition (subagents, documentation links, existing tools in novel combinations) to proliferation.

3. **Evolve tools as capability improves.** Claude Code's `TodoWrite` helped early models stay organized; once Claude got smarter, `TodoWrite` became *constraining* and was replaced with a `Task` tool that enabled agent-to-agent coordination. Tools that help today will limit you tomorrow.

4. **Structured tools beat prompt-engineered formats.** The canonical example: asking users clarifying questions. Attempts 1 and 2 (embed question in existing tool; instruct Claude to emit markdown with a specific shape) both failed. Attempt 3 (a dedicated `AskUserQuestion` tool that blocks the loop until the user answers) worked immediately. The lesson: *if you need reliable structure, make it a tool, not a prompt instruction.*

5. **Match tool complexity to model capability.** A tool that's too abstract confuses a weaker model. A tool that's too granular wastes turns on a stronger one. The right abstraction is model-specific.

## How it relates to Hermes

Several Hermes skills embed assumptions that Thariq's framework would challenge:

- **`life-advisor` queries KV via formatted prompts**, not via a structured tool interface. When the output drifts (Claude skips sections, adds preamble, reorders) — that's the markdown-formatting failure from Attempt 2 in Thariq's essay, verbatim. Fix: replace free-form KV query with a tool that takes `(intent, frameworks, max_results)` and returns structured JSON.

- **The behavioral morning digest cron** assumes Claude will "read the right context" when given a long prompt dump. That's the *opposite* of progressive disclosure. A better shape: give Claude a `search_yesterday()` tool, a `get_whoop_cycle(days_back)` tool, a `get_kv_framework(name)` tool — let Claude pull what it needs.

- **The health_log skill's output surface** has accumulated over five commits. Is every field Claude adds to the log *actually used* downstream? Thariq's "bar is high" applies: each optional field is cognitive load on every log call.

## What Aryan could borrow

1. **Instrument tool-invocation failures, not just outputs.** When a skill runs but Claude calls it wrong (missing args, wrong types, ignored output), log that as a first-class failure. This is how you "observe ruthlessly." Right now Hermes probably logs skill *results*, not skill *usage patterns.*

2. **Audit Hermes skills against the "tool vs prompt" test.** Anything that relies on Claude emitting a specific markdown shape is a future bug. Convert those surfaces into real tools with schemas.

3. **Kill old tools as capability improves.** The `TodoWrite → Task` story is a reminder: when Aryan upgrades from Opus 4.5 to 4.6 to 5, some skills that currently scaffold Claude will start to constrain it. Review skills quarterly; delete the ones that no longer earn their slot.

4. **Prefer progressive disclosure for KV and health data.** Currently the morning digest likely ingests *everything relevant.* Better: give Claude tools to pull KV sources and WHOOP cycles on demand, and let it decide how deep to go per morning.

## Not borrow

The Anthropic team has hundreds of developers to A/B-test tool designs. Aryan has a user-of-one (himself). The principle transfers; the velocity doesn't. Don't rewrite working skills pre-emptively — apply the discipline at the *next* skill-creation moment.

## Key quote

> "The bar to add a new tool is high, because this gives the model one more option to think about."

The counterpart to every "I should add a skill for X" impulse.
