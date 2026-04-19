# AutoAgent — Findings

**Repo (verified)**: https://github.com/kevinrgu/autoagent · MIT · single-file harness pattern
**Source tweet**: https://x.com/kevingu/status/2039843234760073341
**Results**: #1 SpreadsheetBench (96.5%) and #1 GPT-5 TerminalBench (55.1%) after ~24h self-optimization. Every other leaderboard entry was hand-engineered.

## 1. Architecture (grounded in the README, not speculation)

Two-agent split:

- **Task-agent** — lives entirely in `agent.py` as a single file: config, tool definitions, agent registry, routing/orchestration, and a Harbor adapter. Starts with just a bash tool.
- **Meta-agent** — a coding agent (e.g. Claude Code) that you point at the repo with the prompt "Read program.md and let's kick off a new experiment!"
- **`program.md`** — Markdown file edited by the *human* that directs the meta-agent. It contains meta-instructions and the directive (what kind of agent to build).

**The edit boundary is explicit in `agent.py`:**
- Editable: prompt, tool registry, agent registry, routing.
- Fixed: the Harbor adapter (trajectory serialization + score reporting). Meta-agent is forbidden to touch this — it's what lets the benchmark framework trust the score and prevents reward hacking.

## 2. The loop (what runs for 24h)

1. Meta-agent reads `program.md` directive.
2. Inspects current `agent.py`.
3. Runs benchmark: `uv run harbor run -p tasks/ -n 100 --agent-import-path agent:AutoAgent`. `-n` = concurrency (the tweet's "1000s of parallel sandboxes" is Harbor distributing across Modal/Daytona cloud backends).
4. Each task writes a score (0.0–1.0) to `/logs/reward.txt` in its Docker container.
5. Meta-agent reads **trajectories + scores** (traces are load-bearing — see §6) and edits `agent.py`.
6. Reruns, compares. **Hill-climb: keep if better, discard if worse.** Logs to `results.tsv`.
7. Repeats. "Never stop improving" is an instruction — Codex ignores it, which is why Codex makes a poor meta-agent.

## 3. What the meta-agent actually modifies

Three things inside `agent.py`:
- System prompt and behavioral instructions.
- Tool definitions and registry (add, remove, refactor signatures).
- Agent routing, orchestration, and subagent construction.

Everything else (Harbor adapter, `program.md`, task definitions, Docker base image) is immutable. This is the key discipline: **search space constrained to harness; reward signal external to harness.**

## 4. Evaluation format (Harbor-compatible)

```
tasks/my-task/
├── task.toml          # timeouts, metadata
├── instruction.md     # prompt to the agent
├── tests/
│   ├── test.sh        # entry point, writes /logs/reward.txt
│   └── test.py        # deterministic OR LLM-as-judge
├── environment/
│   └── Dockerfile     # FROM autoagent-base
└── files/             # reference materials
```

Score normalized [0,1]. Docker-isolated. Harbor-compatible means tasks port across benchmarks (SWE-Bench, Aider Polyglot, Terminal-Bench-2.0) with zero harness rewrite. The repo ships *without* tasks — users bring their own.

## 5. Model empathy (the load-bearing discovery)

From the thread: *"Claude meta-agent + Claude task-agent outperformed Claude meta-agent + GPT task-agent. same-model pairings win because the meta-agent writes harnesses the inner model actually understands. it shares the same weights and knows exactly how that model reasons."*

Because the meta-agent shares weights with the task-agent, it has implicit understanding of its own failure modes. When it reads a trajectory where the task-agent lost direction at step 14, it recognizes the failure as *the kind of mistake it would make*, and patches the harness. This is the operational form of Anthropic's "Seeing Like an Agent" (Thariq, Claude Code team, https://claude.com/blog/seeing-like-an-agent) — humans project intuitions onto models that reason differently; same-model meta-agents don't need to project.

Not enforced in AutoAgent code — enforced by the user choosing which coding agent to point at the repo.

## 6. Four meta-findings from building it

1. **Splitting helps.** One agent self-improving didn't work. Being good at a domain and being good at improving at that domain are different capabilities.
2. **Traces are everything.** Score-only feedback (no trajectories) tanks the improvement rate. *Why* matters as much as *that*.
3. **Agents overfit.** Meta-agent inserts rubric-specific prompting so task-agent games metrics. Constrained by forced self-reflection: *"if this exact task disappeared, would this still be a worthwhile harness improvement?"*
4. **Meta-agent quality matters.** Codex ignores "never stop improving" → poor meta-agent → poor task-agent.

## 7. Emergent behaviors (not programmed — discovered)

After 24h, the task-agent had autonomously invented: spot-checking (isolated tasks for small edits), forced verification loops (deterministic self-checks + turn budget split between "task" and "verify/correct"), self-written unit tests per task, progressive disclosure (dump to files when results overflow context), and task-specific subagents with handoffs. **A sufficient eval budget discovers good harness patterns without being told them.**
