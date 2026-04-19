---
sidebar_position: 11
title: "Cron 内部机制"
description: "Hermes 如何存储、调度、编辑、暂停、技能加载和交付 cron 作业"
---

# Cron 内部机制

cron 子系统提供计划任务执行 — 从简单的一次性延迟到具有技能注入和跨平台交付的重复 cron 表达式作业。

## 关键文件

| 文件 | 用途 |
|------|---------|
| `cron/jobs.py` | 作业模型、存储、对 `jobs.json` 的原子读写 |
| `cron/scheduler.py` | 调度器循环 — 到期作业检测、执行、重复跟踪 |
| `tools/cronjob_tools.py` | 面向模型的 `cronjob` 工具注册和处理器 |
| `gateway/run.py` | 网关集成 — 在长时间运行循环中的 cron 滴答 |
| `hermes_cli/cron.py` | CLI `hermes cron` 子命令 |

## 调度模型

支持四种调度格式：

| 格式 | 示例 | 行为 |
|--------|---------|----------|
| **相对延迟** | `30m`, `2h`, `1d` | 一次性，在指定持续时间后触发 |
| **间隔** | `every 2h`, `every 30m` | 重复，以固定间隔触发 |
| **Cron 表达式** | `0 9 * * *` | 标准 5 字段 cron 语法（分钟、小时、日、月、工作日） |
| **ISO 时间戳** | `2025-01-15T09:00:00` | 一次性，在确切时间触发 |

面向模型的表面是一个单一的 `cronjob` 工具，具有操作式操作：`create`, `list`, `update`, `pause`, `resume`, `run`, `remove`。

## 作业存储

作业存储在 `~/.hermes/cron/jobs.json` 中，具有原子写入语义（写入临时文件，然后重命名）。每个作业记录包含：

```json
{
  "id": "a1b2c3d4e5f6",
  "name": "每日简报",
  "prompt": "总结今天的 AI 新闻和融资轮次",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "display": "0 9 * * *"
  },
  "skills": ["ai-funding-daily-report"],
  "deliver": "telegram:-1001234567890",
  "repeat": {
    "times": null,
    "completed": 42
  },
  "state": "scheduled",
  "enabled": true,
  "next_run_at": "2025-01-16T09:00:00Z",
  "last_run_at": "2025-01-15T09:00:00Z",
  "last_status": "ok",
  "created_at": "2025-01-01T00:00:00Z",
  "model": null,
  "provider": null,
  "script": null
}
```

### Job Lifecycle States

| State | Meaning |
|-------|---------|
| `scheduled` | Active, will fire at next scheduled time |
| `paused` | Suspended — won't fire until resumed |
| `completed` | Repeat count exhausted or one-shot that has fired |
| `running` | Currently executing (transient state) |

### Backward Compatibility

Older jobs may have a single `skill` field instead of the `skills` array. The scheduler normalizes this at load time — single `skill` is promoted to `skills: [skill]`.

## Scheduler Runtime

### Tick Cycle

The scheduler runs on a periodic tick (default: every 60 seconds):

```text
tick()
  1. Acquire scheduler lock (prevents overlapping ticks)
  2. Load all jobs from jobs.json
  3. Filter to due jobs (next_run <= now AND state == "scheduled")
  4. For each due job:
     a. Set state to "running"
     b. Create fresh AIAgent session (no conversation history)
     c. Load attached skills in order (injected as user messages)
     d. Run the job prompt through the agent
     e. Deliver the response to the configured target
     f. Update run_count, compute next_run
     g. If repeat count exhausted → state = "completed"
     h. Otherwise → state = "scheduled"
  5. Write updated jobs back to jobs.json
  6. Release scheduler lock
```

### Gateway Integration

In gateway mode, the scheduler tick is integrated into the gateway's main event loop. The gateway calls `scheduler.tick()` on its periodic maintenance cycle, which runs alongside message handling.

In CLI mode, cron jobs only fire when `hermes cron` commands are run or during active CLI sessions.

### Fresh Session Isolation

Each cron job runs in a completely fresh agent session:

- No conversation history from previous runs
- No memory of previous cron executions (unless persisted to memory/files)
- The prompt must be self-contained — cron jobs cannot ask clarifying questions
- The `cronjob` toolset is disabled (recursion guard)

## Skill-Backed Jobs

A cron job can attach one or more skills via the `skills` field. At execution time:

1. Skills are loaded in the specified order
2. Each skill's SKILL.md content is injected as context
3. The job's prompt is appended as the task instruction
4. The agent processes the combined skill context + prompt

This enables reusable, tested workflows without pasting full instructions into cron prompts. For example:

```
Create a daily funding report → attach "ai-funding-daily-report" skill
```

### Script-Backed Jobs

Jobs can also attach a Python script via the `script` field. The script runs *before* each agent turn, and its stdout is injected into the prompt as context. This enables data collection and change detection patterns:

```python
# ~/.hermes/scripts/check_competitors.py
import requests, json
# Fetch competitor release notes, diff against last run
# Print summary to stdout — agent analyzes and reports
```

The script timeout defaults to 120 seconds. `_get_script_timeout()` resolves the limit through a three-layer chain:

1. **Module-level override** — `_SCRIPT_TIMEOUT` (for tests/monkeypatching). Only used when it differs from the default.
2. **Environment variable** — `HERMES_CRON_SCRIPT_TIMEOUT`
3. **Config** — `cron.script_timeout_seconds` in `config.yaml` (read via `load_config()`)
4. **Default** — 120 seconds

### Provider Recovery

`run_job()` passes the user's configured fallback providers and credential pool into the `AIAgent` instance:

- **Fallback providers** — reads `fallback_providers` (list) or `fallback_model` (legacy dict) from `config.yaml`, matching the gateway's `_load_fallback_model()` pattern. Passed as `fallback_model=` to `AIAgent.__init__`, which normalizes both formats into a fallback chain.
- **Credential pool** — loads via `load_pool(provider)` from `agent.credential_pool` using the resolved runtime provider name. Only passed when the pool has credentials (`pool.has_credentials()`). Enables same-provider key rotation on 429/rate-limit errors.

This mirrors the gateway's behavior — without it, cron agents would fail on rate limits without attempting recovery.

## Delivery Model

Cron job results can be delivered to any supported platform:

| Target | Syntax | Example |
|--------|--------|---------|
| Origin chat | `origin` | Deliver to the chat where the job was created |
| Local file | `local` | Save to `~/.hermes/cron/output/` |
| Telegram | `telegram` or `telegram:<chat_id>` | `telegram:-1001234567890` |
| Discord | `discord` or `discord:#channel` | `discord:#engineering` |
| Slack | `slack` | Deliver to Slack home channel |
| WhatsApp | `whatsapp` | Deliver to WhatsApp home |
| Signal | `signal` | Deliver to Signal |
| Matrix | `matrix` | Deliver to Matrix home room |
| Mattermost | `mattermost` | Deliver to Mattermost home |
| Email | `email` | Deliver via email |
| SMS | `sms` | Deliver via SMS |
| Home Assistant | `homeassistant` | Deliver to HA conversation |
| DingTalk | `dingtalk` | Deliver to DingTalk |
| Feishu | `feishu` | Deliver to Feishu |
| WeCom | `wecom` | Deliver to WeCom |
| Weixin | `weixin` | Deliver to Weixin (WeChat) |
| BlueBubbles | `bluebubbles` | Deliver to iMessage via BlueBubbles |
| QQ Bot | `qqbot` | Deliver to QQ (Tencent) via Official API v2 |

For Telegram topics, use the format `telegram:<chat_id>:<thread_id>` (e.g., `telegram:-1001234567890:17585`).

### Response Wrapping

By default (`cron.wrap_response: true`), cron deliveries are wrapped with:
- A header identifying the cron job name and task
- A footer noting the agent cannot see the delivered message in conversation

The `[SILENT]` prefix in a cron response suppresses delivery entirely — useful for jobs that only need to write to files or perform side effects.

### Session Isolation

Cron deliveries are NOT mirrored into gateway session conversation history. They exist only in the cron job's own session. This prevents message alternation violations in the target chat's conversation.

## Recursion Guard

Cron-run sessions have the `cronjob` toolset disabled. This prevents:
- A scheduled job from creating new cron jobs
- Recursive scheduling that could explode token usage
- Accidental mutation of the job schedule from within a job

## Locking

The scheduler uses file-based locking to prevent overlapping ticks from executing the same due-job batch twice. This is important in gateway mode where multiple maintenance cycles could overlap if a previous tick takes longer than the tick interval.

## CLI Interface

The `hermes cron` CLI provides direct job management:

```bash
hermes cron list                    # Show all jobs
hermes cron create                  # Interactive job creation (alias: add)
hermes cron edit <job_id>           # Edit job configuration
hermes cron pause <job_id>          # Pause a running job
hermes cron resume <job_id>         # Resume a paused job
hermes cron run <job_id>            # Trigger immediate execution
hermes cron remove <job_id>         # Delete a job
```

## Related Docs

- [Cron Feature Guide](/docs/user-guide/features/cron)
- [Gateway Internals](./gateway-internals.md)
- [Agent Loop Internals](./agent-loop.md)