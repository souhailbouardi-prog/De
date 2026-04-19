# Related Sources — Index

Six ecosystem sources cross-referenced from the five core Hermes-improvement articles. These aren't the headline pieces — they're the supporting structure: the engineering philosophy (Anthropic, Thariq), the tool-curation archetypes (gstack, obra/superpowers), and the production exemplars (last30days, gkisokay's self-directed Hermes).

## The six sources

| # | Source | Type | Central claim |
|---|--------|------|---------------|
| 1 | [Anthropic — Managed Agents](anthropic-managed-agents.md) | Engineering blog | Decouple brain (harness) from hands (sandbox) via stable interfaces so harness designs don't fossilize as models improve. |
| 2 | [Thariq — Seeing Like an Agent](seeing-like-an-agent.md) | Design philosophy | Tool design is empathy for the model; observe Claude's behavior, don't extrapolate from human reasoning. |
| 3 | [Garry Tan — gstack](gstack.md) | Opinionated skill pack | 23 slash commands that turn Claude Code into a virtual engineering team with YC-style review gates. |
| 4 | [obra/superpowers](obra-superpowers.md) | Skills framework | Mandatory TDD + systematic debugging workflow; skills auto-trigger based on context, not explicit invocation. |
| 5 | [mvanhorn/last30days-skill](last30days-skill.md) | Production skill | Pattern for multi-source research synthesis: entity resolution → parallel fanout → dedupe-and-rank. |
| 6 | [gkisokay — Self-Directed Hermes](gkisokay-self-directed-agent.md) | Production exemplar | Two-mind architecture: a second Hermes profile ("Dreamer") that freely associates, then promotes ideas to builds when they survive multiple walks. |

## How they connect

**Architecture axis (1, 2):** Anthropic's managed-agents post is the systems view — what interfaces make agent infrastructure outlive any specific model. Thariq's "Seeing Like an Agent" is the same principle one level up: what interface (tool) design outlives changes in model capability. Both converge on *don't bake current-model workarounds into load-bearing surfaces.*

**Skill-framework axis (3, 4):** gstack and superpowers are competing takes on "what should a curated Claude skill pack look like." gstack is role-based (CEO review, eng review, QA) and optimizes for solo builder velocity. superpowers is methodology-based (TDD, brainstorming, systematic debugging) and optimizes for agent discipline. They aren't rivals — they overlap on ~40% of primitives (review, plan, ship) but diverge on whether skills are *opt-in tools* (gstack) or *mandatory process gates* (superpowers).

**Production-pattern axis (5, 6):** last30days-skill is the canonical multi-source research synthesizer — a template any Hermes skill needs when pulling from Reddit/X/YouTube/KV simultaneously. gkisokay's dreamer is the canonical self-directed agent — a template for Hermes if it's to pick its own projects rather than only respond to Aryan's prompts.

## Direct implications for Hermes

1. **Brain/hands separation (from #1):** Hermes's cron + SQLite state + skills is already partially decoupled. The remaining work is making the *harness* replaceable — so a future Hermes could run the same skills under Opus 4.6, Qwen 3.5, or Gemini without rewrites.

2. **Tool design for the model (from #2):** Every Hermes skill (health_log, life-advisor, behavioral morning digest) should be evaluated with Thariq's lens: does Claude *actually* invoke it correctly? Log invocation failures, not just outputs.

3. **Skill curation (from #3, #4):** Both gstack and superpowers demonstrate that raw skill count is a liability — a curated set with strong trigger descriptions beats a sprawling library. Hermes's current skills/ directory should be audited for dead weight.

4. **Multi-source synthesis (from #5):** The life-advisor + KV + WHOOP + behavioral digest combo *is* a multi-source research problem. last30days's entity-resolution → parallel-fanout → dedupe-rank pipeline is a direct blueprint.

5. **Self-direction (from #6):** gkisokay shows Hermes can *already* do what Aryan is implicitly asking for — "life advisor, not task agent" — by running a second profile at high temperature on cheap local hardware that promotes ideas only after repeated reflection. Most tractable upgrade on this list.

## Priority for Aryan

- **Immediate borrow:** gkisokay's dreamer pattern (source #6). Direct fit for Hermes vision; uses infrastructure Aryan already has.
- **Next:** last30days's synthesis pipeline (source #5) applied to KV + health data fusion.
- **Continuous:** Thariq's "observe, don't assume" discipline (source #2) applied to every skill Aryan ships.
- **Architectural north star:** Anthropic's brain/hands decoupling (source #1) — aspirational, not immediate refactor.
- **Reference only:** gstack and superpowers (sources #3, #4) — study for skill-design patterns, don't adopt wholesale.
