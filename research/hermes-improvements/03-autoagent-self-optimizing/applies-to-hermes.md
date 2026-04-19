# AutoAgent → applies to Hermes

## Hermes's existing skills auto-learn loop (grounded in code)

Found in `/Users/aryanbhatia/Documents/0DevProjects/hermes-agent/run_agent.py`:

- Every **15 tool-calling iterations** (`creation_nudge_interval: 15` in `cli-config.yaml.example:429`), Hermes spawns a **background review agent** (`_spawn_background_review`, line 1773).
- Background agent is a full `AIAgent` fork with same model, tools, and conversation snapshot.
- It runs `_SKILL_REVIEW_PROMPT` (line 1749): *"was a non-trivial approach used to complete a task that required trial and error… If a relevant skill already exists, update it with what you learned. Otherwise, create a new skill if the approach is reusable."*
- Writes via `tools/skill_manager_tool.py` (create/edit/patch/delete on `~/.hermes/skills/`).
- Passes through `tools/skills_guard.py` security scanner.

**This is the half-AutoAgent.** Hermes has the "edit the harness" and "read the trace" legs of the loop — but no score, no hill-climb, no revert. Skills are appended; bad skills stay.

## The gap AutoAgent exposes

| AutoAgent | Hermes today | Hermes gap |
|---|---|---|
| Meta-agent reads trajectory + score | Review-agent reads trajectory only | No score |
| Keep if better, revert if worse | Always append | No revert mechanism |
| Harbor task format with deterministic tests | No eval harness | Skills never measured |
| Meta-agent edits `agent.py` (harness) | Review-agent edits skills (a soft harness) | Skills are richer edit surface; closer fit |
| Docker-isolated tasks, 1000s parallel | Subagent delegation via `tools/delegate_tool.py` — already exists | Infrastructure exists, missing orchestrator |

## Concrete mappings Hermes could adopt

**1. Hermes-Harbor — eval harness for skills.** Directory structure that mirrors Harbor:

```
~/.hermes/evals/
└── daily-health-log/
    ├── task.toml
    ├── instruction.md
    ├── tests/test.py       # deterministic or LLM-as-judge
    └── fixtures/
```

A deterministic `test.py` for something like `skills/health/daily-health` could check: "did a row get written to health.db with today's date?" or "does the output contain JSON matching this schema?" Skills without evals stay manual; skills with evals become measurable.

**2. Meta-skill: `optimize-skill`.** A skill that invokes Hermes on itself. Given a target skill + its evals, it:
- Runs the eval N times, records baseline score.
- Reads trajectories from `trajectory_compressor.py` infrastructure (already exists).
- Proposes an edit to SKILL.md via `skill_manager_tool.py` (already exists, already guards with `skills_guard.py`).
- Re-runs eval. **Keeps if score rises, reverts via `patch` action if it drops.**
- Logs delta to `~/.hermes/evals/results.tsv`.

This is literally AutoAgent, but the "harness" is a skill and the "Harbor adapter" is Hermes's `run_agent.AIAgent`. Every piece exists; missing glue is: (a) the eval runner, (b) the hill-climb controller, (c) the revert step.

**3. Bootstrap from bash only.** AutoAgent task-agent starts with just a bash tool. Hermes equivalent: a `hermes --minimal` mode that disables every skill and most tools, runs against a set of domain evals, and lets the meta-skill discover what tools/skills the domain needs. Hermes already has the `enabled_toolsets`/`disabled_toolsets` plumbing — the missing piece is the outer loop that measures domain success.

**4. Trace → score, not just trace.** Hermes's `_SKILL_REVIEW_PROMPT` asks the review-agent to judge subjectively ("was the approach non-trivial?"). Replace with: when a cron job or user task completes, score it (deterministic check, user thumbs up/down via Telegram/Discord, or LLM-judge). Feed score + trace to the review-agent. This is the single biggest improvement leverage — it's the difference between "occasional skills that might be good" and "skills that provably improve outcomes."

**5. Overfitting guard — borrow AutoAgent's line verbatim.** Add to `_SKILL_REVIEW_PROMPT`: *"If this exact task disappeared, would this skill still be worth saving?"* This is a one-line change with evidence it matters.

## What makes Hermes *uniquely* suited

Hermes already has:
- `tools/skill_manager_tool.py` — create/patch/delete surface (✓ AutoAgent's `agent.py` edit surface).
- `tools/skills_guard.py` — security scanner on agent-created skills (✓ bounds search space safely).
- `agent/trajectory.py` + `trajectory_compressor.py` — trajectory capture (✓ AutoAgent's "traces are everything").
- `tools/delegate_tool.py` subagent system — parallel execution (✓ AutoAgent's sandboxes, smaller scale).
- `cron/scheduler.py` — runs jobs on a schedule (✓ could run the optimization loop overnight).
- `agent/smart_model_routing.py` — already has cheap-vs-strong routing (✓ could route meta-agent to strong, task-agent to cheap).

**Hermes is ~70% of the way to AutoAgent-for-personal-workflows.** Missing: an eval harness format, a score-keeping ledger, and a controller that hill-climbs.
