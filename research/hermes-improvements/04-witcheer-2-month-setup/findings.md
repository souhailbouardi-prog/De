# witcheer's 2-Month Hermes Setup — Findings (Main Writeup)

- **Source**: https://x.com/witcheer/status/2037528582298194123
- **Author**: @witcheer — DeFi Growth Lead on Mac Mini M4, early 2026
- **Total cost**: $21/month
- **Length**: 29,791 chars

## TL;DR

**"Persistence × time = compound context."** The AI model (GLM-5/4.7) is mediocre; what works is the infrastructure around it. Four flywheels:

1. **ALIVE walnut filesystem** — crons READ tasks before searching and WRITE findings back to a prepend-only log, so tomorrow's session starts richer (see `alive-context-system.md`)
2. **Voice-corrections log** — 151 diff lessons ("you wrote X, I changed to Y, because Z") beats 39k characters of voice prompts (see `voice-feedback-loop.md`)
3. **Always-on cron pipeline writing to files** — 18 jobs (see `cron-jobs-taxonomy.md`)
4. **Tiered model stack with free local compression** — fixes a silent rate-limit death spiral (see `cost-optimization.md`)

## Section index

1. **Hardware** — Mac Mini M4 16GB, launchd service, 24/7
2. **Hermes framework** — Telegram bot, skills, crons, MCP
3. **Model stack** — GLM-5 interactive / GLM-4.7 crons / `qwen3.5:4b` local compression via Ollama
4. **18 crons** — see `cron-jobs-taxonomy.md`
5. **35 shell scripts** — data sources (8), monitoring (4), content (4), infra (5+)
6. **6 skills** — walnuts, grimoire, yari-intel, arcana-intel, alpha-scanner, voice-learn
7. **ALIVE context system** — see `alive-context-system.md`
8. **Voice feedback loop** — see `voice-feedback-loop.md`
9. **Lessons / anti-patterns** — see `lessons-anti-patterns.md`
10. **Replication** — min 30min setup / full weekend
11. **Philosophy** — "AI is the engine, context is the fuel, fuel compounds"

## Hermes framework gaps witcheer identifies

1. **Walnuts as first-class primitive** — filesystem convention should ship in-box
2. **Multi-model fallback chains** — when primary provider 429s, rotate automatically
3. **Automatic session cleanup** — sessions pile up forever
4. **Default idle timeout 60min not 1440** — prevents cron sessions wasting tokens
5. **Local Ollama compression as default** — silent rate-limit deaths vanish
6. **Source diversity helper for research skills** — force Techmeme → HN → Reddit → web ordering
7. **Ship `voice-corrections.md` skill template** in `optional-skills/`
8. **Ship `nightly-builder.md` skill template** in `optional-skills/`
9. **Document per-job `"model"` config as upgrade-safe pattern** — survives Hermes updates
