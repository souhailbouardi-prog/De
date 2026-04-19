# Model-Empathy Implications for Hermes

## The problem AutoAgent surfaces for Hermes

Hermes is designed to swap providers freely — `hermes model` command, credential pools that rotate across keys (`agent/credential_pool.py`), `fallback-providers.md` docs, OpenRouter as a default for free-tier users. The typical Hermes user runs cron jobs on whatever OpenRouter free-tier model happens to route at that moment — which could be Gemini Flash, DeepSeek, a Llama variant, a Qwen variant, any of them.

AutoAgent's finding: **cross-model pairings lose.** If Hermes writes a skill using Claude Sonnet (via API) but a cron job executes it on `deepseek/deepseek-chat:free` via OpenRouter, the skill's implicit assumptions about how the model reasons won't match the model executing it.

## Three practical implications

**1. Skills are implicitly model-empathic to whatever model wrote them.** When Hermes writes a skill after a session on Claude, that skill's phrasing, tool-call patterns, and decomposition strategy reflect Claude's weights. When a cron job on DeepSeek tries to follow that skill, it's cross-model. Expected: degraded performance vs. a skill written *by* DeepSeek.

**Recommendation:** tag skills with `created_by_model` metadata in frontmatter. Let routing optionally prefer skills written by the same model-family as the currently-loaded model. This is a cheap win — it's just metadata + a preference score.

**2. Cron jobs on free-tier OpenRouter are the worst case for model empathy.** OpenRouter's `:free` endpoints often route to whichever provider has capacity — the model executing your job is non-deterministic. Skills written in that environment are effectively averaged across providers; skills read in that environment are evaluated against a random model.

**Recommendation:** for cron/autonomous workflows, pin to a specific model (not `:free` roulette). Document this as a performance practice. If budget is a constraint, pin to one cheap-and-stable model (e.g. `deepseek-chat`) rather than rotating free tiers — same-model consistency beats marginally-better one-off samples.

**3. If Hermes builds a meta-skill (the AutoAgent pattern), the meta-skill must run on the *same model* as the target skills.** Otherwise you get the Codex-meta-agent problem the thread calls out: a meta-agent that doesn't understand its task-agent produces bad harness edits. The `smart_model_routing.py` cheap-vs-strong split is actually the *wrong* shape for this — you want meta and task to share weights, not diverge.

**Alternative:** let the user configure meta-model and task-model independently but default them to the same model. Warn when they diverge ("Model empathy: consider using the same model for meta-agent and task-agent — see AutoAgent findings").

## Testable prediction

If Hermes ships an eval harness + meta-skill:
- Same-model setup (Claude meta + Claude task, or DeepSeek meta + DeepSeek task) → score climbs.
- Mixed setup (Claude meta + random OpenRouter free-tier task) → score climbs slower or regresses.
- Mixed but logged → skills become model-specific noise rather than reusable procedures.

This is the cleanest empirical validation Hermes could run if it adopts this architecture — it directly reproduces AutoAgent's same-model finding on Hermes's own skills substrate.

## Concrete action items (no code, just direction)

1. Add `created_by_model` and `created_by_provider` to skill frontmatter — retroactively populate from session logs.
2. Document OpenRouter `:free` non-determinism in `docs/user-guide/features/fallback-providers.md` with a warning about cron reliability.
3. If Hermes-Harbor happens: default meta-model = task-model; require explicit opt-in to diverge.
4. Consider a "model empathy score" — how often does a skill get good outcomes on models outside the one that wrote it? Low scores = candidate for model-specific variants.

---

**Aryan's immediate context (2026-04-12):** swapped off Kimi (exhausted) to OpenRouter free tier. GLM-4.5-air made unwanted file edits during a cron run; gpt-oss-120b behaved correctly. This is *exactly* the non-determinism pattern implication #2 warns about. The activation plan's decision to pin to `gpt-oss-120b:free` (rather than letting `:free` roulette) is aligned with AutoAgent's finding.
