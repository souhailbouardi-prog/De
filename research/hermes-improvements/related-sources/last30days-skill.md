# mvanhorn/last30days-skill

**Source:** https://github.com/mvanhorn/last30days-skill

## What it is

A production Claude Code skill that researches any topic by querying 13+ sources in parallel (Reddit, X, YouTube, Hacker News, Polymarket, GitHub, TikTok, Instagram, Threads, Pinterest, Bluesky, Perplexity Sonar, the open web), deduplicates across sources, ranks by actual user engagement, and returns a synthesized brief.

It's the cleanest public example of a **multi-source research synthesis skill** — the exact shape Hermes needs for life-advisor + KV + WHOOP + behavioral data fusion.

## Core architectural insight

**Three phases, each with a specific design choice:**

### Phase 1: Entity resolution (pre-research)

Before any API fires, a Python "pre-research brain" interprets the query to identify the *right entities* to search for.

Example: query `"OpenClaw"` resolves to:
- X handle `@steipete`
- Subreddits `r/openclaw`, `r/ClaudeCode`
- GitHub repos
- YouTube channels

This is huge. Most research agents search literal strings and return junk. last30days does **bidirectional entity disambiguation** (person ↔ company, product ↔ founder) before any expensive call.

### Phase 2: Parallel multi-source fanout

13+ sources queried concurrently:
- **Free:** Reddit (with comment threads), Hacker News, Polymarket, GitHub
- **Browser-authenticated:** X/Twitter, YouTube (via yt-dlp)
- **API:** TikTok, Instagram, Threads, Pinterest, Bluesky (via ScrapeCreators)
- **Grounded:** Perplexity Sonar (via OpenRouter)

The key design choice is *heterogeneous source handling* — each source has different auth, different rate limits, different result shapes, but they're all normalized to a common record.

### Phase 3: Dedupe, rank, synthesize

- **Cross-source deduplication** — same story on Reddit/X/YouTube becomes one cluster
- **Engagement scoring** — upvotes, likes, views, betting odds normalized into a single rank
- **Per-author cap (max 3 items per voice)** — prevents single loud accounts from dominating
- **Fun judge** — secondary LLM scores for humor/virality alongside relevance
- **GitHub person-mode** — if researching a person, pulls live PR velocity + release notes
- **ELI5 mode** — rewrites synthesis in plain language post-query

## Project structure

```
skills/last30days/
  SKILL.md              # source-of-truth runtime spec
  scripts/              # Python orchestration
  vendored/bird-client  # JS for X search
  tests/                # 1,012+ test cases
```

Everything runs locally. No analytics, no tracking. SKILL.md is the canonical spec — code is secondary to the spec. This matches Anthropic's recent skill-authoring guidance: the markdown file *is* the skill; scripts are implementation detail.

## How it relates to Hermes

Hermes has the ingredients for a last30days-shaped pipeline but runs them sequentially and without entity resolution:

| last30days phase | Hermes equivalent | Gap |
|------------------|-------------------|-----|
| Entity resolution | None | Skills search literal strings |
| Parallel source fanout | Sequential MCP calls | Each source called one at a time |
| Dedupe across sources | None | KV and WHOOP data don't cross-reference |
| Engagement rank | None | No ranking; last-wins |
| Synthesis | Behavioral morning digest (partial) | Works, but on pre-filtered data |

The behavioral morning digest already *does* multi-source synthesis (WHOOP + mood + weight + KV frameworks). It's just missing the entity-resolution front-end and the dedupe-rank middle.

## What Aryan could borrow

1. **Entity resolver as a dedicated skill.** Add a `resolve_entity(query)` skill that, given a topic Aryan voice-messages about, returns the relevant KV source IDs, WHOOP metrics, contacts, and projects. Example: `"how's the gym going"` → `{whoop: [recovery, strain, workouts_last_30d], kv: [fitness_framework, deload_protocol], health_log: [weight_trend, mood_trend]}`. This is the single most copyable piece of last30days.

2. **Parallel MCP fanout.** Hermes already has knowledge-vault, whoop, and local SQLite MCPs. Most skills call them sequentially. Replace with parallel fanout where possible — especially in the morning digest. For a single-user agent, the wins are latency (digest generates in 2s instead of 8s) and the ability to surface cross-source correlations.

3. **Dedupe across KV sources.** KV collections overlap (a framework cited in multiple sources). Implement the "cluster" pattern — same insight from 3 sources becomes one ranked cluster, not three repeated bullet points.

4. **Per-author cap for KV.** If Aryan's KV is dominated by a single author's frameworks, the life-advisor's output will be monotonous. Borrow the "max 3 per voice" rule for diversification.

5. **SKILL.md as spec.** Audit current Hermes skills — which are spec-driven (SKILL.md is the source of truth) vs. code-driven (scripts are the source, SKILL.md is documentation)? Migrate toward the former. Easier for Claude to reason about, easier to edit without breaking runtime.

## Not borrow

The 13 external sources. Hermes is a life advisor, not a trend aggregator — pulling from TikTok and Polymarket isn't relevant. Borrow the *pipeline shape* (resolve → fanout → dedupe → rank → synthesize) and apply it to Hermes's actual sources: KV, WHOOP, health_log SQLite, calendar, todoist.

Also don't borrow the test suite size (1,012 tests). For a personal agent, ~30 integration tests on the critical synthesis paths are enough.

## Key insight for Hermes

**The morning digest is a last30days-shaped problem.** Right now it runs as one prompt with all data pre-fetched. Restructured as resolve-entities → parallel-fetch → dedupe-rank → synthesize, it becomes:
- Faster (parallel fetch)
- More robust (source failures are local, not catastrophic)
- More relevant (entity resolution pulls the *right* KV frameworks for today's state, not a static list)
- Easier to extend (adding a new source = add a resolver + fetcher, not rewrite the digest prompt)

This is probably the highest-leverage single refactor on the whole related-sources list.
