# Cost Optimization — The $21/Month Math

## The single line item

**$21/month for the Z.AI coding plan.** Full stop. That's the entire recurring AI cost.

No other recurring AI spend:
- Compression → free (local Ollama on the M4)
- Hardware → one-time ~$600 for Mac Mini M4
- Data-source APIs → free (coingecko, defillama, HN, Reddit, arXiv, Snapshot — no keys needed for most)
- Telegram → free
- FRED → free (API key is free)
- Electricity → negligible for an M4 Mac Mini

## Why Z.AI specifically

> "GLM-5 is the cheapest model with tool calling that actually works."

Critical constraints:
- **Tool calling must work reliably** (not just be advertised). Many cheap models fail here.
- **Follows multi-step instructions** (research crons are 13-step prompts).
- **Known limitation: writing is terrible.** witcheer accepts this and handles writing himself.

The plan has a **600 prompts / 5-hour rate limit** on coding plan. This shapes the architecture.

## Model routing — the three-tier stack

| Tier | Model | Cost | Volume |
|---|---|---|---|
| Interactive | GLM-5 via Z.AI | (share of $21) | ~dozens of prompts/day |
| Cron jobs (18) | GLM-4.7 via Z.AI | (share of $21) | Hundreds of prompts/day across 18 jobs |
| Compression | qwen3.5:4b local | $0 | Every time context threshold hits |

### Why GLM-4.7 for crons, not GLM-5

> "Z.AI has a rate limit: 600 prompts per 5 hours on the coding plan. If the cron jobs used GLM-5, they'd eat through my interactive quota."

GLM-4.7 is cheaper per prompt AND counts on the same rate-limit bucket. So routing all cron volume to 4.7 preserves 5 for the human-in-the-loop interactive use.

### Why local Ollama for compression

The **death spiral** witcheer observed when compression ran on cloud:

1. Cron job runs → generates messages → context grows.
2. Context hits threshold → triggers compression.
3. Compression calls Z.AI → uses API quota.
4. More cron jobs run → more compression calls → more quota used.
5. Rate limit hit → **compression fails silently** → context keeps growing.
6. Context grows unbounded → agent hangs 10+ minutes processing bloated sessions.

Hidden failure, degrading performance, no error. witcheer didn't notice for days.

**Fix:** point compression at local Ollama:
```yaml
# .env
OPENAI_BASE_URL=http://localhost:11434/v1
# config.yaml
summary_model: qwen3.5:4b
compression_threshold: 0.50
ollama_keep_alive: 5m
```

qwen3.5:4b: 3.4GB model, ~20 tok/s on M4 chip. Free. No rate limits. No API dependency. Auto-unloads from RAM after 5 min idle.

## The idle timeout lever

Independent of the compression fix, the default session idle timeout was **1440 minutes (24 hours)** — sessions never reset during the day, growing from 7am briefing through every cron job until next morning.

**Fix:** drop idle timeout to **60 minutes**. Response times went from 10+ minutes during heavy periods to **under 5 seconds**.

> "Imagine your desk gets covered in papers throughout the day but you never clean it. By evening, you can't find anything and every task takes 10x longer... The idle timeout is how often you clean the desk. 24h means you never clean it. 60 min means you clean it every hour."

## Why $21/month is the right budget (not $5 and not $200)

witcheer implies:
- **Sub-$21:** cheaper models have unreliable tool calling, break the cron pipeline.
- **$200+:** Frontier models (Claude, GPT-4+) would be nicer but are overkill for research/coordination and not cheaper for writing (since the human edits anyway).
- **$21 sweet spot:** cheapest model that meets the "tool calling works" bar, accepting writing limitations and handling them with the voice feedback loop.

## Per-job model config as a cost discipline

> "Set per-job model config immediately. Don't patch the scheduler code. It gets wiped on every update. Set `"model": "glm-4.7"` in each job's config in jobs.json. Survives updates, survives patches."

This is both a reliability pattern AND a cost pattern — without per-job pinning, crons may default to GLM-5 on reconfigure and eat the interactive budget.

## Mapping to Aryan's Hermes

| Cost principle | Aryan's current state | Action |
|---|---|---|
| Tiered model (interactive/cron/compression) | Unknown/single model likely | Audit: which model runs each role? |
| Local compression | Unknown | If crons are running on API, verify compression target; route to Ollama |
| Per-job model pin | Likely not set | Set `"model"` per job in jobs.json |
| 60-min idle timeout | Likely default 1440 | Set 60 |
| Free data APIs | KV integration uses APIs — cost unclear | Cost-audit KV API surface |

## Risk analysis of witcheer's cost setup

- **Single-vendor lock-in on Z.AI.** If Z.AI changes pricing or blocks, the whole system breaks. No fallback chain called out (Hermes only supports single fallback anyway).
- **China-based model provider.** May matter for compliance or data-residency in some contexts.
- **Coding plan endpoint gotcha:** "Use `/coding/paas/v4` endpoint, NOT `/paas/v4`. The coding plan key only works on the coding endpoint." Silent-fail if misconfigured.

## If Aryan wanted to match or beat $21/month

Options:
1. **Same plan:** Z.AI coding plan $21/mo.
2. **Bring-your-own OpenAI-compatible:** e.g. DeepSeek, Groq, OpenRouter — can be cheaper or more flexible.
3. **Hybrid:** Use Claude API with prompt caching for interactive (potentially cheaper per-token given caching) + local Ollama for cron or compression.
4. **Aryan already has Claude access via Claude Code** — interactive use could route through Claude Code on-demand, and Hermes crons could run a smaller/cheaper model. This may yield a better quality-to-cost ratio than witcheer's setup.

**Recommendation for Aryan:** do the model audit first. It's possible the KV-integrated advisor should run on a stronger model (Claude) while the routine health cron runs on the cheapest reliable tool-calling model.
