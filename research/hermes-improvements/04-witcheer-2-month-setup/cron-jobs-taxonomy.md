# witcheer's 18 Cron Jobs — Taxonomy

All 18 jobs run on **GLM-4.7** via Z.AI (cheap model, protects the interactive GLM-5 quota). All deliver results to Telegram. All read from and write to the ALIVE walnut context system.

## Full table — daily (13 jobs)

| Time | Job | Category | Reads | Writes | Purpose |
|---|---|---|---|---|---|
| 07:00 | morning-briefing | Briefing | All walnuts' `now.md`, project contexts | Telegram | Weather, crypto, stablecoin pegs, RWA moves, overnight research recap, HN/Reddit, priority list |
| 07:30 | competitor-dashboard | Monitoring | yari-finance walnut | Telegram, walnut log | Tracks 11+ CDP/stablecoin protocols: TVL, governance, partnerships |
| 09:00 | dune-monitor (1st) | Monitoring | — | Telegram | On-chain Dune queries |
| 10:00 | grimoire-drafter | Content | voice-corrections.md, walnut insights | Drafts folder | Telegram channel posts (visual-first format) |
| 11:00 | daily-nudge | Priority engine | ALL project context files | Telegram | Priority recommendations across ventures; surfaces cross-project tensions |
| 12:00 | draft-review | Content QA | Drafts folder, voice rules | Telegram | Picks best unposted draft, runs check_draft.sh |
| 14:00 | research-ai | Domain research | oz-agent walnut, voice files, archives | AI research archive, walnut log | arXiv + Reddit + HN + Techmeme + news |
| 16:00 | research-arcana | Domain research | arcana walnut | arcana archive, walnut log | Redacted (consulting domain) |
| 17:00 | dune-monitor (2nd) | Monitoring | — | Telegram | 2nd daily on-chain pass |
| 18:00 | research-defi | Domain research | yari-finance walnut | defi archive, walnut log | Stablecoins, RWA, governance, competitors |
| 20:00 | research-deepdive | Synthesis | Day's findings | Structured report | Picks one topic, goes deep: web-fetch full articles, data compile |
| 21:00 | health-check | Infrastructure | All crons, launchd, disk | Telegram | Monitors cron execution, gateway status, disk, PAT expiry |
| 22:00 | content-performance | Analytics | Social metrics | Performance log | Tracks what posts performed, stores metrics |
| 23:00 | nightly-builder | **Autonomous code** | Research archives, gap reports | New scripts, PRs | **Writes code to fill gaps identified during research** — monitoring scripts, fixed parsers, new data pipelines |

## Periodic (4 jobs)

| Cadence | Job | Purpose |
|---|---|---|
| Mon/Thu 09:00 | outreach-CRM | BD workflow automation |
| Mon 09:00 | weekly-intel | Competitive intelligence brief |
| Sun/Wed 20:00 | learning-digest | Curated week's learning resources |
| Sun 08:00 | weekly-planner | Reads perf + research + project states → produces a weekly content + priority plan |

## Hourly (1 job)

| Cadence | Job | Purpose |
|---|---|---|
| Hourly 9am-8pm | breaking-news | RSS + TVL monitor + stablecoin peg alerts + viral tweet detection |

**Total: 13 daily + 4 periodic + 1 hourly = 18 scheduled jobs.**

## Categorical summary

| Category | Count | Jobs |
|---|---|---|
| Research (domain-specific) | 4 | research-ai, research-arcana, research-defi, research-deepdive |
| Content pipeline | 3 | grimoire-drafter, draft-review, content-performance |
| Monitoring | 4 | competitor-dashboard, dune-monitor (x2), breaking-news |
| Briefing / synthesis | 3 | morning-briefing, daily-nudge, weekly-planner |
| Infrastructure | 2 | health-check, nightly-builder |
| Periodic intel | 2 | weekly-intel, learning-digest |
| BD/ops | 1 | outreach-CRM |

## Anatomy of a research cron — `research-ai`

The prompt is ~3,000 words. 13 explicit steps:

1. **Source verification rules.** "Never include a finding without a URL you actually visited." Reduces hallucinated URLs to near-zero (GLM-4.7 hallucinates URLs ~5% of the time without this).
2. **Context loading.** Agent reads 7 files: persistent memory, operations log, research priorities, content voice guide, voice corrections, AI research archive, relevant project context.
3. **Email check.** Checks bot alerts inbox via Himalaya CLI.
4. **arXiv scan.** Custom Python script via arXiv API.
5. **Nightly-builder check.** Did overnight autonomous build create new tools?
6. **Web search with enforced source diversity.** "Fetch Techmeme FIRST, then HN, then Reddit, THEN web search to fill gaps." Without this order-rule, the agent defaults to Reddit for everything.
7. **Deep read.** Web-fetch 2-3 most interesting articles in full.
8. **WRITE findings.** Mandatory. "A session with no writes is a failure." Writes to AI research archive.
9. **Draft.** If content-worthy, draft in "personal experience" format. Read voice corrections first.
10. **Quality check.** Run `check_draft.sh` — must score ≥70/100 against voice rules.
11. **Operations log.** One line summary.
12. **Context update.** Update project context files with session results.
13. **Self-check.** "Did I write new content to the research archive? If NO, go back and do step 8." Prevents the "researched but forgot to save" failure mode.

## Cross-cutting patterns

1. **Read-before-write-before-read loop.** Every research cron: reads walnut tasks → searches aligned to tasks → writes findings to walnut log → next run reads the enriched log. Compounds over time.
2. **Mandatory writes.** The "session with no writes is a failure" rule is repeated in the research-ai prompt AND enforced by a step 13 self-check. This is the single most important cron-design pattern in the article.
3. **Explicit source ordering.** Reddit ranks high in search, so without an order rule, LLM defaults to Reddit only. Force Techmeme → HN → Reddit → web-search fallback.
4. **URL verification.** Prompt rule: "ask yourself: did I actually visit this URL?" Prevents URL hallucination.
5. **Per-job model pinning.** Each job sets `"model": "glm-4.7"` in jobs.json. Don't patch the scheduler code — it gets wiped on framework updates.
6. **Structured stage with quality gate.** Drafts pass through `check_draft.sh` scoring ≥70/100 before delivery.
7. **Nightly autonomous code-builder is the wildcard.** It looks at gaps identified during research — missing scripts, broken parsers, needed tools — and writes code to fill them. While the human sleeps.

## Implied anti-patterns from cron design

- **Long prompts work.** The research-ai prompt is ~3000 words. witcheer is not minimizing prompts; he's over-specifying because the model needs structure.
- **Self-verification checks inside the prompt** (step 13) compensate for model unreliability.
- **Orthogonal crons, not one mega-cron.** Separate research-ai / research-defi / research-arcana because each reads a different walnut and accumulates into a different archive.
- **Interactive-vs-cron model separation is non-negotiable** given rate limits.

## What Aryan's Hermes should adopt

Aryan currently runs a health cron. Gap analysis:

- ✅ Has: scheduled job, writes to somewhere (KV), delivered via Telegram/channel.
- ❌ Missing: the **mandatory-writes self-check** at the end of the cron prompt.
- ❌ Missing: **source ordering discipline** for any research-type cron.
- ❌ Missing: a **daily-nudge** cron that reads all project context and surfaces tensions (huge value: one job, enormous output, low complexity).
- ❌ Missing: a **weekly-planner** cron.
- ❌ Missing: a **health-check / meta cron** that monitors the other crons.
- ❌ Missing: **nightly-builder**. Likely the highest-leverage single addition.

See `applies-to-hermes.md` for prioritized action list.
