# Hermes Agent Improvement Research

**Date**: 2026-04-12
**Source material**: 5 articles captured in the Knowledge Vault (MCP) + 6 cross-referenced ecosystem sources.
**Goal**: Document patterns, techniques, and experiments worth applying to improve Aryan's Hermes setup.
**Status**: Research only. No implementation. Implementation decisions deferred.

---

## The 5 core articles

| # | Folder | Source | Length |
|---|---|---|---|
| 1 | [`01-garrytan-gbrain-recall/`](./01-garrytan-gbrain-recall/) | Garry Tan — GBrain (perfect total recall over 10k+ md files) | tweet |
| 2 | [`02-awesome-hermes-agent/`](./02-awesome-hermes-agent/) | @nyk_builderz (0xNyk) — awesome-hermes-agent list (80+ entries) | tweet + repo |
| 3 | [`03-autoagent-self-optimizing/`](./03-autoagent-self-optimizing/) | Kevin Gu — AutoAgent (self-optimizing agent harnesses, #1 benchmarks) | long thread |
| 4 | [`04-witcheer-2-month-setup/`](./04-witcheer-2-month-setup/) | witcheer — Living With an AI Agent (2-month retrospective, Hermes stack) | 30k-char guide |
| 5 | [`05-spisak-clearly-explained/`](./05-spisak-clearly-explained/) | Nick Spisak — Hermes Agent Clearly Explained (7 workflows) | 12k-char guide |

## Cross-referenced ecosystem sources

In [`related-sources/`](./related-sources/):

- **Anthropic Managed Agents** — brain/hands decoupling architecture
- **"Seeing Like an Agent"** (Thariq / Claude Code team) — conceptual root of AutoAgent's "model empathy"
- **gstack** (Garry Tan) — 15 opinionated Claude Code tools, companion to GBrain
- **obra/superpowers** — competing agentic skills framework
- **mvanhorn/last30days-skill** — production skill for multi-source research synthesis
- **gkisokay** — self-directed agent that picks its own projects (Hermes + OC)

## Cross-cutting themes

See [`cross-cutting-themes/`](./cross-cutting-themes/) for synthesis across all sources:

- **Memory: unified, persistent, layered** — every source agrees, but disagrees on the implementation
- **Skills vs memory** — Spisak's key distinction: skills are *procedures*, memory stores *facts*
- **One agent vs multi-agent** — Spisak's explicit anti-pattern vs AutoAgent's meta/task pairing
- **Self-optimization as table stakes** — AutoAgent sets the bar; Hermes's built-in learning loop is a lite version of this
- **Model selection is load-bearing** — free/local models fail tool-use; frontier APIs required for production workflows (Aryan is living this constraint)
- **Knowledge base as compounding asset** — wiki layer on top of raw sources, not just storage

## How to read this

1. **Start with each article folder's `findings.md`** — the main analysis
2. **Then `applies-to-hermes.md`** — specific techniques mapped to Aryan's setup (health cron, advisor, KV)
3. **Related sources** for context on references cited across multiple articles
4. **Cross-cutting themes** for the synthesis

## Aryan's current Hermes setup (baseline for "applies-to-hermes" mappings)

- **Gateway**: Hermes on Mac, Telegram bot, OpenRouter free tier (`openai/gpt-oss-120b:free` current; swapped off Kimi 2026-04-12)
- **Custom skills**: `daily-health`, `life-advisor`
- **MCP servers**: whoop, gws, todoist, knowledge-vault
- **Cron jobs** (8 active): `health-morning-checkin`, `health-noon-nudge`, `health-evening-reminder`, `health-weekly-review`, `health-bloodwork-reminder`, `behavioral-morning-digest`, `morning-digest`, `daily-intel-digest`
- **Data stores**: `~/.hermes/health/health.db` (SQLite), `~/.hermes/sessions/`, `~/.hermes/skills/`, Knowledge Vault (remote API)
- **Voice**: faster-whisper STT local, edge-tts TTS
