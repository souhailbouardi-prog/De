---
sidebar_position: 11
title: "Cron 内部原理"
description: "Hermes 如何存储、调度、编辑、暂停、加载技能和交付 cron 任务"
---

# Cron 内部原理

cron 子系统提供定时任务执行功能 — 从简单的一次性延迟到带有技能注入和跨平台交付的重复 cron 表达式任务。

## 关键文件

| 文件 | 用途 |
|------|---------|
| `cron/jobs.py` | 任务模型、存储、对 `jobs.json` 的原子读写 |
| `cron/scheduler.py` | 调度器循环 — 到期任务检测、执行、重复跟踪 |
| `tools/cronjob_tools.py` | 面向模型的 `cronjob` 工具注册和处理程序 |
| `gateway/run.py` | 网关集成 — 在长时间运行的循环中进行 cron 计时 |
| `hermes_cli/cron.py` | CLI `hermes cron` 子命令 |

## 调度模型

支持四种调度格式：

| 格式 | 示例 | 行为 |
|--------|---------|----------|
| **相对延迟** | `30m`、`2h`、`1d` | 一次性，在指定持续时间后触发 |
| **间隔** | `every 2h`、`every 30m` | 重复，以固定间隔触发 |
| **Cron 表达式** | `0 9 * * *` | 标准 5 字段 cron 语法（分钟、小时、日、月、周） |
| **ISO 时间戳** | `2025-01-15T09:00:00` | 一次性，在确切时间触发 |

面向模型的接口是一个带有动作式操作的单一 `cronjob` 工具：`create`、`list`、`update`、`pause`、`resume`、`run`、`remove`。

## 任务存储

任务存储在 `~/.hermes/cron/jobs.json` 中，具有原子写入语义（写入临时文件，然后重命名）。每个任务记录包含：

```json
{
  "id": "a1b2c3d4e5f6",
  "name": "Daily briefing",
  "prompt": "Summarize today's AI news and funding rounds",
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

### 任务生命周期状态

| 状态 | 含义 |
|-------|---------|
| `scheduled` | 活跃，将在下次计划时间触发 |
| `paused` | 暂停 — 直到恢复才会触发 |
| `completed` | 重复次数用尽或已触发的一次性任务 |
| `running` | 当前正在执行（临时状态） |

### 向后兼容性

较旧的任务可能有单个 `skill` 字段而不是 `skills` 数组。调度器在加载时会将其标准化 — 单个 `skill` 会升级为 `skills: [skill]`。

## 调度器运行时

### 计时周期

调度器以周期性计时（默认：每 60 秒）运行：

```text
tick()
  1. 获取调度器锁（防止重叠计时）
  2. 从 jobs.json 加载所有任务
  3. 过滤到期任务（next_run <= now AND state == "scheduled"）
  4. 对于每个到期任务：
     a. 将状态设置为 "running"
     b. 创建全新的 AIAgent 会话（无对话历史）
     c. 按顺序加载附加的技能（作为用户消息注入）
     d. 通过代理运行任务提示
     e. 将响应交付到配置的目标
     f. 更新运行计数，计算下次运行时间
     g. 如果重复次数用尽 → 状态 = "completed"
     h. 否则 → 状态 = "scheduled"
  5. 将更新的任务写回 jobs.json
  6. 释放调度器锁
```

### 网关集成

在网关模式下，调度器计时集成到网关的主事件循环中。网关在其定期维护周期中调用 `scheduler.tick()`，该周期与消息处理并行运行。

在 CLI 模式下，只有在运行 `hermes cron` 命令或活动 CLI 会话期间，cron 任务才会触发。

### 全新会话隔离

每个 cron 任务在完全新鲜的代理会话中运行：

- 没有先前运行的对话历史
- 没有先前 cron 执行的记忆（除非持久化到内存/文件）
- 提示必须自包含 — cron 任务不能询问澄清问题
- `cronjob` 工具集被禁用（递归防护）

## 基于技能的任务

cron 任务可以通过 `skills` 字段附加一个或多个技能。在执行时：

1. 技能按指定顺序加载
2. 每个技能的 SKILL.md 内容作为上下文注入
3. 任务的提示作为任务指令附加
4. 代理处理组合的技能上下文 + 提示

这使得可重用、经过测试的工作流成为可能，而无需将完整指令粘贴到 cron 提示中。例如：

```
创建每日资金报告 → 附加 "ai-funding-daily-report" 技能
```

### 基于脚本的任务

任务还可以通过 `script` 字段附加 Python 脚本。脚本在每次代理轮次*之前*运行，其标准输出作为上下文注入到提示中。这启用了数据收集和变更检测模式：

```python
# ~/.hermes/scripts/check_competitors.py
import requests, json
# 获取竞争对手发布说明，与上次运行进行比较
# 打印摘要到标准输出 — 代理分析并报告
```

脚本超时默认为 120 秒。`_get_script_timeout()` 通过三层链解析限制：

1. **模块级覆盖** — `_SCRIPT_TIMEOUT`（用于测试/猴子补丁）。仅在与默认值不同时使用。
2. **环境变量** — `HERMES_CRON_SCRIPT_TIMEOUT`
3. **配置** — `config.yaml` 中的 `cron.script_timeout_seconds`（通过 `load_config()` 读取）
4. **默认值** — 120 秒

### 提供程序恢复

`run_job()` 将用户配置的回退提供程序和凭据池传递到 `AIAgent` 实例：

- **回退提供程序** — 从 `config.yaml` 读取 `fallback_providers`（列表）或 `fallback_model`（旧格式字典），与网关的 `_load_fallback_model()` 模式匹配。作为 `fallback_model=` 传递给 `AIAgent.__init__`，后者将两种格式标准化为回退链。
- **凭据池** — 使用解析的运行时提供程序名称通过 `agent.credential_pool` 中的 `load_pool(provider)` 加载。仅在池具有凭据时传递 (`pool.has_credentials()`)。启用在 429/速率限制错误时的同提供程序密钥轮换。

这与网关的行为一致 — 没有它，cron 代理会在速率限制时失败而不尝试恢复。

## 交付模型

cron 任务结果可以交付到任何支持的平台：

| 目标 | 语法 | 示例 |
|--------|--------|---------|
| 原始聊天 | `origin` | 交付到创建任务的聊天 |
| 本地文件 | `local` | 保存到 `~/.hermes/cron/output/` |
| Telegram | `telegram` 或 `telegram:<chat_id>` | `telegram:-1001234567890` |
| Discord | `discord` 或 `discord:#channel` | `discord:#engineering` |
| Slack | `slack` | 交付到 Slack 主频道 |
| WhatsApp | `whatsapp` | 交付到 WhatsApp 主页 |
| Signal | `signal` | 交付到 Signal |
| Matrix | `matrix` | 交付到 Matrix 主房间 |
| Mattermost | `mattermost` | 交付到 Mattermost 主页 |
| 电子邮件 | `email` | 通过电子邮件交付 |
| SMS | `sms` | 通过 SMS 交付 |
| Home Assistant | `homeassistant` | 交付到 HA 对话 |
| 钉钉 | `dingtalk` | 交付到钉钉 |
| 飞书 | `feishu` | 交付到飞书 |
| 企业微信 | `wecom` | 交付到企业微信 |
| 微信 | `weixin` | 交付到微信 |
| BlueBubbles | `bluebubbles` | 通过 BlueBubbles 交付到 iMessage |
| QQ 机器人 | `qqbot` | 通过官方 API v2 交付到 QQ（腾讯） |

对于 Telegram 主题，使用格式 `telegram:<chat_id>:<thread_id>`（例如 `telegram:-1001234567890:17585`）。

### 响应包装

默认情况下（`cron.wrap_response: true`），cron 交付会包装有：
- 标识 cron 任务名称和任务的头部
- 注明代理在对话中无法看到已交付消息的尾部

cron 响应中的 `` 前缀会完全抑制交付 — 对于只需要写入文件或执行副作用的任务很有用。

### 会话隔离

Cron 交付不会镜像到网关会话对话历史中。它们仅存在于 cron 任务自己的会话中。这可以防止目标聊天对话中的消息交替违规。

## 递归防护

Cron 运行的会话禁用 `cronjob` 工具集。这可以防止：
- 计划任务创建新的 cron 任务
- 可能导致令牌使用爆炸的递归调度
- 从任务内部意外修改任务调度

## 锁定

调度器使用基于文件的锁定来防止重叠计时执行相同的到期任务批处理两次。这在网关模式下很重要，因为如果前一个计时比计时间隔花费更长时间，多个维护周期可能会重叠。

## CLI 接口

`hermes cron` CLI 提供直接的任务管理：

```bash
hermes cron list                    # 显示所有任务
hermes cron create                  # 交互式任务创建（别名：add）
hermes cron edit <job_id>           # 编辑任务配置
hermes cron pause <job_id>          # 暂停运行中的任务
hermes cron resume <job_id>         # 恢复暂停的任务
hermes cron run <job_id>            # 触发立即执行
hermes cron remove <job_id>         # 删除任务
```

## 相关文档

- [Cron 功能指南](/docs/user-guide/features/cron)
- [网关内部原理](./gateway-internals.md)
- [代理循环内部原理](./agent-loop.md)