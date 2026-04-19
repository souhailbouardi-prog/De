# Lessons From 2 Months — Anti-Patterns & What Witcheer Would Do Differently

## The six explicit lessons (verbatim summary)

### 1. Start with local compression from day 1
> "Cloud API compression and rate limits creates silent failure. Sessions grow unbounded and you won't notice until the agent is hanging for 10 minutes per response. Local Ollama compression is free, reliable, and has zero rate limits."

**Anti-pattern avoided:** letting compression call the same rate-limited cloud API the crons use.
**Diagnostic:** if the agent is sending 8 messages of context dump and responses take 10+ min, compression is probably broken.

### 2. Set per-job model config immediately
> "Don't patch the scheduler code. It gets wiped on every update. Set `"model": "glm-4.7"` in each job's config in jobs.json. Survives updates, survives patches, never needs re-applying."

**Anti-pattern avoided:** modifying framework code → fragility across updates.

### 3. Don't trust the AI to write; build the voice feedback loop on day 1
> "Accept that you'll be rewriting 50-80% of every draft for weeks. The corrections compound, but slowly. Get 50+ correction entries before expecting usable drafts."

**Anti-pattern avoided:** waiting for "good enough" prompting before starting corrections. The corrections compound; start early.

### 4. Set session idle timeout to 60 minutes
> "The default is often much longer. Long sessions = bloated context = slow responses. Short sessions = fresh context = fast responses. The research still gets saved to files between sessions."

**Anti-pattern avoided:** trusting the framework default (1440 min = 24h).

### 5. Enforce source diversity in prompts
> "If you don't explicitly force it, the model will use Reddit for everything because Reddit ranks high in search results. Explicit rules: 'fetch Techmeme first, then Hacker News, then Reddit, THEN use web search to fill gaps.' Specify the order."

**Anti-pattern avoided:** assuming web search alone produces diverse results.

### 6. Monitor your compression pipeline
> "It fails silently. If the agent suddenly takes 10 minutes to respond and sends 8 messages of context dump, compression is probably broken. Check the model, check the endpoint, check the manifest. `ollama pull` to force a clean download."

**Anti-pattern avoided:** assuming "slow = network latency" when it might be a broken compression subsystem.

---

## Implicit anti-patterns (read between the lines of the article)

### A. The "one big context" anti-pattern
witcheer originally had sessions running for 24h. Implicit lesson: **short-lived sessions, persistent files.** The file is the long-term state; the session is a short execution window. Don't conflate them.

### B. "More prompt rules = better output" anti-pattern
39,000 characters of voice rules couldn't produce good writing. **Prompt complexity has a ceiling.** Beyond that, you need other mechanisms (correction logs, quality gates, human editing).

### C. "Research without writes" anti-pattern
The explicit step 13 self-check exists because the model will happily do all the research and then not save anything. **Writes must be mandatory and verified.**

### D. "Single model for everything" anti-pattern
Using GLM-5 for crons AND interactive AND compression would blow the 600-prompt rate limit and create silent failures. **Tiered model routing is required, not optional.**

### E. "Fix the scheduler code" anti-pattern
Modifying framework code makes updates destructive. **Configure, don't modify.** Stay on upgrade paths.

### F. "Reddit-default-everything" anti-pattern
Without source ordering rules, the model degrades to Reddit-only. The cure is **imperative ordering in the prompt**, not suggestion.

### G. "Trust the AI to remember" anti-pattern
The compounding-context thesis exists *because* the AI forgets everything between sessions. **Structured files are the only durable memory.**

### H. "Invisible failure" anti-pattern
Compression fails silently. Crons fail silently. Rate limits fail silently. **Active health checks (witcheer's 21:00 cron) are non-optional.**

### I. Hallucinated URL anti-pattern
GLM-4.7 hallucinates URLs ~5% of the time. Cure: prompt rule "did I actually visit this URL?" **Verification prompts for known model failure modes.**

---

## What witcheer would do differently (restated in one list)

1. Local compression from day 1 (not weeks in).
2. Per-job model pins in `jobs.json` (not scheduler patches).
3. `voice-corrections.md` from day 1 (not after 50 bad drafts).
4. Idle timeout = 60 min (not 1440).
5. Source diversity rules in every research prompt.
6. Compression pipeline monitoring (alert on silent failure).

---

## What witcheer does NOT explicitly warn about but probably should

### Single provider risk
All of GLM-5, GLM-4.7, and the cron pipeline run through Z.AI. If Z.AI's coding plan changes terms, the whole system breaks. Hermes only supports single fallback — meaning effectively no redundancy here.

### Walnut corruption risk
Multiple crons writing to the same `log.md` simultaneously. witcheer's `update-walnut.sh` presumably handles this with `flock`, but if not, concurrent prepends could corrupt. Not addressed in the article.

### Nightly-builder autonomy risk
A cron that autonomously writes code "while you sleep" is a remarkable capability and a remarkable failure mode. witcheer mentions it has "fixed broken parsers and created new data pipelines" but not what happens when it creates a regression, introduces a bug, or writes something that exfiltrates data. `github-push-nightly.sh` with 13 regex secret scans is a backstop, but it's regex-based and won't catch subtle secret patterns or semantic issues.

### Cost drift risk
$21/month is today. If cron count scales 18→50, or context usage scales, will the Z.AI plan still cover? No headroom analysis given.

### Backup and disaster recovery
The entire compound-context asset (walnuts, voice-corrections.md, research archives) lives on one Mac Mini. Disk failure = total loss. witcheer mentions `github-push-nightly.sh` which implies the filesystem is under git — but the article doesn't confirm this covers the walnut data.

---

## Applies to Aryan

From Aryan's existing state, the most likely footguns:

| Footgun | Likelihood for Aryan | Mitigation |
|---|---|---|
| Compression death spiral | Medium (depends on current config) | Verify compression endpoint ASAP |
| Default idle timeout = 1440 | High | Set to 60 min |
| Single model for everything | Medium | Audit model routing |
| Research-without-writes | High (if health cron doesn't enforce) | Add step N self-check |
| Reddit-default source bias | High (any web-search cron) | Add source ordering rules |
| Silent cron failures | High (no meta health-check cron yet) | Build one |
| Walnut adoption without compaction | High (if walnuts get added) | Build compact_memory analog |
| KV + walnut duplication | Novel risk | Define boundary up-front |
