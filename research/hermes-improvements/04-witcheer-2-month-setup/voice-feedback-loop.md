# Voice Feedback Loop — Teaching an AI to Write Like You

> "This is the technique I'm most excited about, and it's the one that costs zero dollars." — witcheer

## The problem

Standard approach: write a better prompt. Add more rules, more examples, more constraints.

> "Write in personal experience format." "Use lowercase." "No bullet points." "Vary sentence length."

witcheer had **39,000 characters of content voice instructions**. The model still produced slop.

**Observation:** more prompt rules ≠ better output. After a certain point, the model can't integrate more abstract instructions.

## The fix: correction logging (not better prompts)

Instead of telling the AI *how* to write, **show it what you changed.**

### The cycle

After every post:

1. User types `"I tweaked your draft"` on Telegram.
2. The `voice-learn` skill activates.
3. It reads the original AI draft AND the posted version.
4. It extracts every diff: tone shifts, cuts, additions, word swaps.
5. It saves each lesson to `voice-corrections.md`.
6. Every future drafting cron reads `voice-corrections.md` **before writing**.

### Why corrections beat prompts

**Prompt form (abstract):** "Write in personal experience format."

**Correction form (concrete):** "You wrote 'not saying this is UST 2.0' — I cut that because preemptive hedges undercut expertise. Don't do this again."

witcheer has **151 lines** of "when you did X, I changed it to Y, because Z" in his corrections file. That's 151 concrete examples. **Specific beats abstract, every time.**

### The compounding effect

> "The model still produces AI slop, but it's better AI slop. And the corrections compound. Every draft that passes through the feedback loop adds more examples."

witcheer frames the steady state honestly:
> "The model can't write like a human. But it can write like a slightly-better AI that knows 151 specific things to avoid. And that's enough when the human is doing the final pass."

Editing time drops from 80% rewriting to roughly 50%.

## Architecture — exact mechanics

| Component | Role |
|---|---|
| `voice-corrections.md` | Append-only log of diff lessons |
| `voice-learn` skill (SKILL.md) | Triggered by "I tweaked your draft" → extracts diff, appends entry |
| `check_draft.sh` | Scores new drafts 0-100 against voice rules |
| Drafting crons (e.g. `grimoire-drafter`) | MUST read `voice-corrections.md` BEFORE writing |

A correction entry is shaped as: `"When you did X, I changed it to Y, because Z"` — three parts: pattern, fix, reason.

## Why this is novel

1. **Concrete > abstract** for style learning in LLMs. The 39k-character voice doc didn't work; 151 diff examples did.
2. **Unidirectional in-context learning.** Each cron reads the corrections before drafting — no fine-tuning, no embedding, just context injection. Costs $0.
3. **User-in-the-loop.** The feedback action ("I tweaked your draft") is the most natural UX — the user was going to edit anyway; the system captures the edit as supervision.
4. **Compound asymptote.** The gap between "50% rewrite" and "0% rewrite" may be unreachable with current models, but the delta from 80% → 50% is very real and very cheap.

## Startup tax witcheer is honest about

> "Accept that you'll be rewriting 50-80% of every draft for weeks. The corrections compound, but slowly. **Get 50+ correction entries before expecting usable drafts.**"

So: 50 corrections ≈ usable drafts. 150 corrections ≈ "slightly better AI slop that knows 151 specific things to avoid." Not "writes like you."

## Mapping to Hermes primitives

| Voice-loop element | Hermes primitive | Notes |
|---|---|---|
| `voice-corrections.md` | `memory/<scope>/voice-corrections.md` | Plain markdown append file |
| `voice-learn` skill | `skills/voice/voice-learn/SKILL.md` | Needs Telegram trigger phrase + diff extraction |
| `check_draft.sh` | `skills/<name>/scripts/check_draft.sh` | Rubric-based 0-100 score |
| Cron "read corrections before writing" | Convention in cron prompt | Step 2 of any drafting cron |

## What Aryan could adopt — prioritized

1. **Create `memory/voice/voice-corrections.md`** scoped to whatever domain produces the most human-edited AI output for Aryan (health writeups? advisor outputs? content?).
2. **Build a `voice-learn` skill** triggered by a phrase in the interactive Telegram channel — extracts the diff between Aryan's edit and the AI's original.
3. **Drafting crons read corrections first** — single-line prompt addition.
4. **Start on day 1.** The compounding curve is slow; starting late is the main regret in witcheer's lessons doc.
5. **Don't wait for the skill to be perfect** — the corrections file alone, manually maintained, is already useful.

## Cross-cutting insight

The voice feedback loop is philosophically the same as ALIVE:

- **ALIVE:** structured file that crons read before searching.
- **Voice loop:** structured file that crons read before writing.

Both operate on the "agent loads context file → does work → writes back" loop. Same primitive, different content. The common structural idea: **the cheap, compounding, persistent asset is a markdown file that the agent treats as authoritative.**
