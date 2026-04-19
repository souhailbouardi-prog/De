# Spisak's "Clearly Explained" → what Aryan's Hermes could adopt

## Applied to Aryan's current setup (health + advisor + KV)

### What Aryan already has (maps to Spisak's workflows)

| Spisak workflow | Aryan's equivalent | Status |
|---|---|---|
| Morning briefings | `health-morning-checkin` cron + `morning-digest` | ✅ active |
| Web monitoring | — | ❌ not yet |
| One-agent-everything | ✅ single Hermes gateway | ✅ correct pattern |
| Knowledge base (llm-wiki) | Knowledge Vault MCP + advisor skill | ⚠️ partial — no wiki structure, just sources |
| Auto-research experiments | — | ❌ not yet |
| MCP interop | ✅ 4 MCP servers (whoop, gws, todoist, kv) | ✅ active |
| Model selection | ✅ swapped off Kimi to free OpenRouter tier | ⚠️ free model struggled today |

### The biggest gap: wiki layer on top of KV

Spisak's §7 describes the **3-layer wiki** built on Karpathy's pattern:
1. **Raw sources** (immutable) — Aryan's KV already does this
2. **Wiki pages** (agent-maintained synthesis) — Aryan has **none**
3. **Schema file** (consistency rules) — Aryan has none

Current KV is layer 1 only. To realize compounding, Aryan needs layer 2: the agent reading new KV sources and updating synthesized wiki pages with cross-references.

This is what Spisak means by "after a month of regular use, you have a compounding knowledge base." Without layer 2, each query against KV is a fresh search — no synthesis builds up.

**Concrete next step**: create a cron `kv-wiki-maintain` that runs weekly. It:
- Lists recently-added KV sources since last run
- For each, identifies relevant existing wiki pages (or creates new)
- Updates the pages with new info + cross-refs
- Writes outputs as markdown to a structured folder (e.g. `~/.hermes/wiki/`)

### The learning-loop gap

Spisak's learning loop writes skills every ~15 tool calls. Aryan's system generates skills manually (via Claude Code sessions). The loop works in Hermes automatically — Aryan has **not validated that this is happening** for his actual Hermes instance.

**Concrete check**: `ls ~/.hermes/skills/` — if only the skills Aryan explicitly created are there (health, advisor, +default), the learning loop either isn't running or isn't producing output. That's worth debugging before building more features.

### Model selection pain — Aryan is living this today

Spisak says model selection is the #1 failure mode:
> "People blame the framework when it's the model failing at tool calling."

Aryan's afternoon demonstrated this: GLM-4.5-air:free edited source files unexpectedly during a cron run. gpt-oss-120b:free behaved correctly. **This is not a framework bug — it's a model-quality-of-tool-use issue.**

Per Spisak, a frontier model API is required for production workflows. Aryan's free-tier constraint is fine for noon-nudge-level crons but risky for anything that invokes scripts or edits files. Cron guardrails ("DO NOT edit files") partially mitigate, but a better model is the root fix.

**Decision point**: accept that free-tier Hermes is for message-only crons (health reminders, digests), and reserve a paid tier for any cron that edits/executes. Or: tighten guardrails further so even free models can't do damage.

## Applied to the 7 workflows Aryan could adopt

### Highly recommended (next 1-2 weeks)

1. **Spisak workflow #7 (llm-wiki) ⭐ highest ROI** — as above, KV layer 2 unlocks compounding
2. **Spisak workflow #2 (web monitoring with Camoufox)** — Aryan's current research requires opening X/Twitter threads manually. Camoufox + Firecrawl + a daily cron would auto-summarize threads by handle (@garrytan, @NickSpisak_, @witcheer, etc.) and feed KV directly
3. **Spisak workflow #5 (auto-research)** — start small: a cron that tries one variation of the behavioral-morning-digest format each week, scores user engagement (did Aryan reply? did he log a habit?), keeps winners

### Medium priority

4. **Spisak workflow #4 expansion** — already have morning-digest; behavioral-morning-digest was added today. Consider an **evening reflection** cron (daily close-out) to capture what happened, feeding back to skills.

### Not yet

5. **Autonomous trading / crypto operations** (Spisak §8) — production-real but outside Aryan's current scope.
