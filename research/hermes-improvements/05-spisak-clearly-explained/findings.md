# Spisak: "Hermes Agent Clearly Explained" — analysis

**Source**: https://x.com/NickSpisak_/status/2042664522151006664 (141 likes, 12 retweets)
**Captured**: 2026-04-11 (KV ID `f17fb8ec`, enriched)
**Length**: 11,757 chars

## Thesis

> "Hermes Agent hit 50K GitHub stars in two months. Every YouTube video explains what it is. None tells you what to actually do with it on day one."

Spisak positions Hermes as the "automation" agent complementary to Claude Code (the "coding" agent) and a superset of OpenClaw (adds the learning loop). The 10 sections cover: what it is, the learning loop, differentiation vs Claude Code/OpenClaw, and 7 concrete workflows.

## The core primitive: the learning loop

> "Every 15 or so tool calls, Hermes pauses. It looks at what just happened. What worked. What failed. What took too long. Then it writes a skill."

Skills are markdown files at `~/.hermes/skills/` — **inspectable, editable, deletable**. Spisak's framing:

> "Claude Code's memory stores facts about your preferences. Hermes stores executable procedures."

This is the real differentiator — memory vs. procedure. A procedure is reusable. A fact is reference material.

## The 7 workflows Spisak documents

### 1. Morning briefings that learn (§4)
- Connect to Telegram, feed it 2-3 topics + email + calendar
- After 2 weeks, day-30 briefing is unrecognizable vs day-1 — learned which senders matter, which topics trigger follow-ups
- Supports 15+ messaging platforms

### 2. Web monitoring → replace manual review (§5)
- Ships with **Camoufox** (stealth browser that doesn't fingerprint)
- Pair with Firecrawl for extraction
- Use case: monitoring user reports on a live site; agent reads report, checks data, applies fix or logs, replaces manual review queue
- Pattern: **diff-of-what-changed** instead of full re-read

### 3. One agent running an entire company (§6) — anti-multi-agent
> "A fintech founder tried 5 specialized agents. It failed in 48 hours. Skills duplicated. Brand voice inconsistent. Couldn't share context."

Collapsed → one Hermes instance running marketing + outreach + community + briefings. Unified memory = compounding context.

### 4. Knowledge base (llm-wiki pattern) (§7)
- **Karpathy's LLM Wiki pattern built in** as a skill
- 3 layers: raw sources (immutable), wiki pages (agent-maintained), schema file (rules)
- Learning loop maintains the wiki automatically: new source triggers cross-reference update, contradiction flagging
- 643 community skills in the Skills Hub (`/skills` command inside Hermes)

### 5. Auto-research / self-optimizing experiments (§8)
- Give it a metric (email open rate, landing page conversion, lead response time)
- Agent makes small change → tests → keeps wins → iterates
- Production use cases: "automated trading strategies" (brokerage API), "automated token operation on Solana"

### 6. Claude Code MCP interop (§9)
- Hermes v0.8.0 ships native MCP client
- Every MCP server built for Claude Code works in Hermes automatically
- Pattern: **one MCP layer, two agents, zero duplication**
- Spisak runs both: Claude Code for repos/code, Hermes for research/briefings/monitoring

### 7. Model selection (§10) — the #1 setup failure
> "The wrong model choice is the #1 reason Hermes setups feel broken. People blame the framework when it's the model failing at tool calling."

- Gemma 4 26B via Ollama = best current local option, but NOT for these workflows
- For Spisak's workflows: use a **frontier model API**
- Builder ran Hermes 3h continuously post-v0.8.0 — only after switching to frontier model
- Local LLMs hallucinate tool calls that don't exist
- Switch: `hermes model`; diagnose: `hermes doctor`

## The closing advice

> "Install it. Connect Telegram. Give it one recurring job. Let it run for two weeks before judging. The day 30 version of your agent is the one worth evaluating."

## Implicit architecture principles

Extracted from what Spisak chose to highlight:

1. **Skills are executable procedures**, not notes. A skill teaches a workflow, not a fact.
2. **Memory compounds when unified** — splitting across agents destroys this.
3. **MCP is the tool interop layer**; skills are the learned-behavior layer. Don't conflate them.
4. **Messaging platforms are first-class deployment targets** — not a dashboard to build, but chat apps the user already uses.
5. **The learning loop is what justifies running for 2+ weeks** — instant-gratification setups misjudge Hermes's value.
