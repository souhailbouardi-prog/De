# Graeme (@gkisokay) — I Built an AI Agent That Chooses Its Own Projects and Ships Them (Hermes + OC)

**Source:** https://x.com/gkisokay/status/2042577629161886136 (primary); companion threads at /2040044476060864598 and /2038896951891210309

## What it is

Graeme ("gkisokay") runs a two-profile Hermes setup where the *second* profile — called **Dreamer** — acts as a subconscious for the main agent. Dreamer has its own cron, its own personality file, its own workspace (a directory called "the room"), runs on a cheap local model (Qwen 3.5 9B), and doesn't share context with the main Hermes agent. Every 30 minutes, Dreamer goes for a "walk."

This is the cleanest public demonstration of a **self-directed Hermes** — an agent that decides what to work on rather than waiting for user prompts. It's built on infrastructure Aryan already has.

## The architecture

**Two minds, one framework:**

```
Main Hermes (Claude / Opus) ←— Aryan's prompts, crons, KV, WHOOP
       │
       │  (ideas promoted from Dreamer after survival test)
       │
Dreamer (Qwen 3.5 9B local)
  ├─ Own personality file
  ├─ Own workspace ("the room")
  ├─ Own cron (30-min tick)
  ├─ No internet, no tools during "walks"
  └─ High temperature during walks, low during reviews
```

**The cycle:**

1. **Walk (every 30 min, high temp, no tools, no internet).** Dreamer emits a free-association journal entry. No structure, no goal. This is the "drift" phase.

2. **Tend-the-room (periodic, low temp).** Dreamer re-reads its own recent walks and rates them against each other. This is the self-review phase.

3. **Echo detection (critical, non-negotiable).** Without this, small models fixate on a topic and repeat it for days, inflating scores with repetition. The self-review explicitly checks "have I been looping?" and penalizes echoes.

4. **Promotion.** When a project idea survives *multiple walks on multiple days* with diverse evidence and genuine repeated interest (*not* repetition — actual reinforcement from distinct angles), it earns a **build sprint**. Dreamer hands the project to the main agent, which actually ships it.

## Core architectural insight

**Separate the generator from the evaluator, and separate both from the executor.** This is a well-known pattern (actor-critic, debate, self-consistency) but Graeme's application is unusually crisp:

- **Walks are cheap and unconstrained** → high idea throughput, high variance, no premature convergence.
- **Reviews are cheap but structured** → cheap filter, catches fixation (the "echo" failure mode that small models default to).
- **Builds are expensive and gated** → only triggered after an idea has survived a multi-day evidence accumulation test.

The temporal constraint matters: an idea has to survive *across* walks, not within one walk. This is the agent-scale analog of "sleep on it." Ideas that sound brilliant in one walk often don't re-emerge in the next; the ones that do are the real signal.

The second key insight: **Dreamer runs on cheap hardware.** Qwen 3.5 9B on a local GPU, always on, every 30 min. Total cost near zero. This is possible only because the walks are unconstrained (no tool calls, no retrieval, no expensive context). Cost discipline enables the idea throughput.

The third insight: **Dreamer is a separate Hermes profile, not a subagent of the main one.** They don't share context. This is important — it prevents the main agent's current task focus from contaminating Dreamer's free association.

## How it relates to Hermes

This is the *most directly borrowable* of all six sources. Graeme is literally running Hermes. The primitives he uses are the same Hermes primitives Aryan has:

| Dreamer primitive | Hermes equivalent | Available now? |
|-------------------|-------------------|----------------|
| Second profile | Multiple Hermes profiles | Yes (Hermes supports it) |
| Local model (Qwen 9B) | Any local or cheap API | Yes |
| Own cron (30 min) | Hermes cron/ | Yes |
| Own workspace | `hermes_state.py` scoping | Yes |
| Personality file | Skill / CLAUDE.md | Yes |
| Echo detection | — | Needs implementing |
| Promotion handoff | — | Needs implementing |

There's no infrastructure gap. The work is designing Dreamer's personality, the walk prompt, the tend-the-room review prompt, and the promotion trigger.

## What Aryan could borrow

**Direct implementation plan (v0, minimal):**

1. **Create a second Hermes profile: `hermes-dreamer`.** Give it a cheap model (Qwen, Haiku, or Gemini Flash) and a separate SQLite path.

2. **Dreamer cron: every 30 min, emit a walk.** Prompt: *"High temperature, no tools, no internet. Free-associate on what you've been thinking about lately. Don't optimize for usefulness. Write 200-500 words."* Write to `dreamer/walks/YYYY-MM-DD-HH:MM.md`.

3. **Dreamer review cron: every 6 hours, tend-the-room.** Prompt: *"Re-read the last 12 walks. Score each on (a) originality, (b) persistence across walks, (c) actionability. Penalize any topic that repeats the same framing three times in a row — that's an echo, not reinforcement."* Write to `dreamer/reviews/...`.

4. **Promotion: once a week, summarize surviving ideas.** Prompt: *"Which ideas have survived 5+ walks over 3+ days with diverse framings? List them. For each, propose a minimal build sprint."* Promote by writing to `dreamer/promotions/` which the main Hermes agent reads on Sunday mornings as part of the weekly review.

5. **Echo detection is the single non-optional piece.** Without it, Dreamer will loop on WHOOP recovery scores for a week and you'll get nothing. The review prompt *must* explicitly check for repetition with the same framing.

**Tuning considerations:**

- Dreamer's personality matters. If it's a clone of the main Hermes, it just echoes Aryan's current priorities. It should have a distinct voice — e.g., the skeptical-historian that pulls patterns from KV the main agent wouldn't, or the playful-connector that notices weird links across domains.
- The walk cadence (30 min) is probably too fast for a life advisor (trends are daily/weekly, not hourly). Try 2h walks, 24h reviews, weekly promotions.

## Not borrow

Graeme's dreamer is tuned for shipping code projects — the "build sprint" at the end actually writes code. Aryan's Hermes is a life advisor. The "build sprint" equivalent for a life advisor is proposing a *conversation, experiment, or decision* to Aryan, not shipping code.

Also don't blindly copy the 30-min cadence. Life signals are slower than code signals; cadence should match the domain.

## Strategic importance

Of the six sources researched, this is the one that **most directly advances Aryan's stated Hermes vision** ("life advisor, beyond task agent"). A task agent waits for prompts. A life advisor has its own interior life and brings things to you.

Dreamer is a blueprint for exactly that transition. Aryan could have a v0 running this weekend.

## Key quote (paraphrased from the thread)

> "An idea has to survive multiple walks over multiple days before it earns a build. Echo detection is non-negotiable — without it, small models fixate on a topic and repeat it forever, inflating scores with repetition."

The echo-detection sentence is the engineering lesson compressed to one line.
