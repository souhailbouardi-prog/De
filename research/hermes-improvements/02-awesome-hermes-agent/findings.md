# awesome-hermes-agent — Ecosystem Map

**Source tweet**: https://x.com/nyk_builderz/status/2035958826973733150
**Repo**: https://github.com/0xNyk/awesome-hermes-agent (1.2k stars, 80+ entries)
**Captured**: 2026-04-11 (KV ID `71c64a9f`)

> Note: tweet handle is `@nyk_builderz`, repo author is `0xNyk` — same person.

## Category breakdown

| Category | Count | Theme |
|---|---|---|
| Official Resources | 8 | Core infrastructure (Nous-maintained) |
| Community Skills | 8 | Hermes-specific |
| agentskills.io Ecosystem | 10 | Cross-platform skills standard |
| Plugins | 7 | Extension points |
| Skill Registries & Discovery | 2 | Distribution |
| Tools & Utilities | 10 | Operational |
| Deployment | 4 | Infrastructure |
| Integrations & Bridges | 10 | External systems |
| Multi-Agent & Swarms | 4 | Coordination |
| Domain Applications | 10 | Vertical agents |
| Forks & Derivatives | 4 | Specialized variants |
| Guides & Documentation | 3 | Learning resources |

**Maturity distribution**: 15 production / 45 beta / 20 experimental — ecosystem is in active experimentation, not stabilization.

## Top 10 community-highlighted projects

1. **Hermes Agent core** (23k+ ⭐) — production
2. **mission-control** (3.7k ⭐) — admin GUI
3. **wondelai/skills** (380+ ⭐) — curated skill pack
4. **Anthropic-Cybersecurity-Skills** (4k+ ⭐) — cross-platform via agentskills.io
5. **hermes-workspace** (500+ ⭐) — workspace GUI
6. **Hindsight** — long-term memory layer
7. **litprog-skill** (75+ ⭐) — literate-programming skill
8. **hermes-plugins** — plugin pack
9. **hermes-agent-docker** — containerized deployment
10. **evey-setup** — setup skeleton

## Key ecosystem observations

1. **Memory has become foundational**, not optional: Honcho, Hindsight, and multiple memory systems all compete. Any serious production Hermes needs a memory strategy.
2. **Multi-modal gateway** is table stakes: Telegram, Discord, Slack, WhatsApp, Signal, Feishu, Lark, WeCom — you deploy where the user already is.
3. **agentskills.io cross-platform standard** is gaining traction (10 entries, endorsed by Chainlink, Black Forest Labs). Skills are becoming portable between frameworks.
4. **Verticalization is real**: robotics, Minecraft, Mars rovers, legal analysis — users are building *specialized* agents, not generalist ones.
5. **Multi-agent coordination** (4 frameworks) suggests single-agent limits are real in production, despite Spisak's "one agent only" advice — there's a real tension here.

## Gaps the ecosystem hasn't filled

| Gap | Evidence |
|---|---|
| **Evaluation frameworks** | Zero benchmarking/scoring tools listed — huge hole given AutoAgent's self-optimization depends on evals |
| **Cost/billing transparency** | Only `hermes-payguard` (payment), no inference cost tracker |
| **GUI fragmentation** | 3 competing workspace solutions (hermes-workspace, mission-control, hermes-webui) — no winner yet |
| **Windows-native support** | Linux-first; only one portable desktop app |
| **Production hardening** | 15/80 production-grade — most community skills are experimental |
