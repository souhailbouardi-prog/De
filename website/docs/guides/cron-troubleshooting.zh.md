---
sidebar_position: 12
title: "Cron 故障排除"
description: "诊断和修复常见的 Hermes cron 问题 — 任务不触发、交付失败、技能加载错误和性能问题"
---

# Cron 故障排除

当 cron 任务表现不符合预期时，请按顺序进行这些检查。大多数问题属于以下四个类别之一：计时、交付、权限或技能加载。

---

## 任务不触发

### 检查 1：验证任务存在且处于活跃状态

```bash
hermes cron list
```

查找任务并确认其状态为 `[active]`（不是 `[paused]` 或 `[completed]`）。如果显示 `[completed]`，则重复计数可能已耗尽 — 编辑任务以重置它。

### 检查 2：确认计划正确

格式错误的计划会默认为一次性执行或被完全拒绝。测试您的表达式：

| 您的表达式 | 应评估为 |
|----------------|-------------------|
| `0 9 * * *` | 每天上午 9:00 |
| `0 9 * * 1` | 每周一上午 9:00 |
| `every 2h` | 从现在开始每 2 小时 |
| `30m` | 从现在开始 30 分钟 |
| `2025-06-01T09:00:00` | 2025 年 6 月 1 日上午 9:00 UTC |

如果任务触发一次后从列表中消失，则它是一次性计划（`30m`、`1d` 或 ISO 时间戳）— 这是预期行为。

### 检查 3：网关是否运行？

Cron 任务由网关的后台定时器线程触发，该线程每 60 秒触发一次。常规的 CLI 聊天会话**不会**自动触发 cron 任务。

如果您希望任务自动触发，则需要运行网关（`hermes gateway` 或 `hermes serve`）。对于一次性调试，您可以使用 `hermes cron tick` 手动触发一次定时器。

### 检查 4：检查系统时钟和时区

任务使用本地时区。如果您机器的时钟错误或处于与预期不同的时区，任务将在错误的时间触发。验证：

```bash
date
hermes cron list   # 比较 next_run 时间与本地时间
```

---

## 交付失败

### 检查 1：验证交付目标是否正确

交付目标区分大小写，并且需要配置正确的平台。配置错误的目标会静默丢弃响应。

| 目标 | 要求 |
|--------|----------|
| `telegram` | `~/.hermes/.env` 中的 `TELEGRAM_BOT_TOKEN` |
| `discord` | `~/.hermes/.env` 中的 `DISCORD_BOT_TOKEN` |
| `slack` | `~/.hermes/.env` 中的 `SLACK_BOT_TOKEN` |
| `whatsapp` | 配置了 WhatsApp 网关 |
| `signal` | 配置了 Signal 网关 |
| `matrix` | 配置了 Matrix 主服务器 |
| `email` | 在 `config.yaml` 中配置了 SMTP |
| `sms` | 配置了 SMS 提供商 |
| `local` | 对 `~/.hermes/cron/output/` 的写权限 |
| `origin` | 传递到创建任务的聊天 |

其他支持的平台包括 `mattermost`、`homeassistant`、`dingtalk`、`feishu`、`wecom`、`weixin`、`bluebubbles`、`qqbot` 和 `webhook`。您还可以使用 `platform:chat_id` 语法（例如 `telegram:-1001234567890`）定位特定聊天。

如果交付失败，任务仍然运行 — 只是不会发送到任何地方。检查 `hermes cron list` 中的 `last_error` 字段（如果可用）。

### 检查 2：检查 `` 使用

如果您的 cron 任务没有产生输出，或者代理响应 ``，则交付会被抑制。这对于监控任务是有意的 — 但请确保您的提示不会意外抑制所有内容。

一个说 "如果没有变化则用 `` 响应" 的提示也会静默吞噬非空响应。检查您的条件逻辑。

### 检查 3：平台令牌权限

每个消息平台机器人都需要特定权限才能接收消息。如果交付静默失败：

- **Telegram**：机器人必须是目标群组/频道的管理员
- **Discord**：机器人必须有权限在目标频道发送消息
- **Slack**：机器人必须添加到工作区并具有 `chat:write` 范围

### 检查 4：响应包装

默认情况下，cron 响应会用页眉和页脚包装（`config.yaml` 中的 `cron.wrap_response: true`）。某些平台或集成可能无法很好地处理这一点。要禁用：

```yaml
cron:
  wrap_response: false
```

---

## 技能加载失败

### 检查 1：验证技能已安装

```bash
hermes skills list
```

技能必须在安装后才能附加到 cron 任务。如果缺少技能，请先使用 `hermes skills install <skill-name>` 或在 CLI 中通过 `/skills` 安装它。

### 检查 2：检查技能名称与技能文件夹名称

技能名称区分大小写，必须与已安装技能的文件夹名称匹配。如果您的任务指定 `ai-funding-daily-report` 但技能文件夹是 `ai-funding-daily-report`，请从 `hermes skills list` 确认确切名称。

### 检查 3：需要交互工具的技能

Cron 任务在禁用 `cronjob`、`messaging` 和 `clarify` 工具集的情况下运行。这可以防止递归创建 cron、直接发送消息（交付由调度程序处理）和交互式提示。如果技能依赖于这些工具集，它将无法在 cron 上下文中工作。

检查技能的文档以确认它在非交互式（无头）模式下工作。

### 检查 4：多技能排序

使用多个技能时，它们按顺序加载。如果技能 A 依赖于技能 B 的上下文，请确保 B 先加载：

```bash
/cron add "0 9 * * *" "..." --skill context-skill --skill target-skill
```

在此示例中，`context-skill` 在 `target-skill` 之前加载。

---

## 任务错误和失败

### 检查 1：查看最近的任务输出

如果任务运行并失败，您可能会在以下位置看到错误上下文：

1. 任务交付的聊天（如果交付成功）
2. `~/.hermes/logs/agent.log` 中的调度程序消息（或 `errors.log` 中的警告）
3. 通过 `hermes cron list` 查看任务的 `last_run` 元数据

### 检查 2：常见错误模式

**脚本的 "No such file or directory"**
`script` 路径必须是绝对路径（或相对于 Hermes 配置目录的路径）。验证：
```bash
ls ~/.hermes/scripts/your-script.py   # 必须存在
hermes cron edit <job_id> --script ~/.hermes/scripts/your-script.py
```

**任务执行时 "Skill not found"**
技能必须安装在运行调度程序的机器上。如果您在机器之间移动，技能不会自动同步 — 使用 `hermes skills install <skill-name>` 重新安装它们。

**任务运行但不交付任何内容**
可能是交付目标问题（参见上面的交付失败）或静默抑制的响应（``）。

**任务挂起或超时**
调度程序使用基于不活动的超时（默认 600 秒，可通过 `HERMES_CRON_TIMEOUT` 环境变量配置，`0` 表示无限制）。只要代理积极调用工具，它就可以运行 — 计时器仅在持续不活动后触发。长时间运行的任务应使用脚本来处理数据收集并仅交付结果。

### 检查 3：锁竞争

调度程序使用基于文件的锁定来防止重叠的定时器。如果运行两个网关实例（或 CLI 会话与网关冲突），任务可能会延迟或跳过。

杀死重复的网关进程：
```bash
ps aux | grep hermes
# 杀死重复进程，只保留一个
```

### 检查 4：jobs.json 的权限

任务存储在 `~/.hermes/cron/jobs.json` 中。如果此文件不可被您的用户读取/写入，调度程序将静默失败：

```bash
ls -la ~/.hermes/cron/jobs.json
chmod 600 ~/.hermes/cron/jobs.json   # 您的用户应该拥有它
```

---

## 性能问题

### 任务启动缓慢

每个 cron 任务都会创建一个新的 AIAgent 会话，这可能涉及提供商认证和模型加载。对于时间敏感的计划，添加缓冲时间（例如，使用 `0 8 * * *` 而不是 `0 9 * * *`）。

### 太多重叠任务

调度程序在每个定时器内顺序执行任务。如果多个任务同时到期，它们会一个接一个地运行。考虑错开计划（例如，使用 `0 9 * * *` 和 `5 9 * * *` 而不是都在 `0 9 * * *`）以避免延迟。

### 大型脚本输出

转储数兆字节输出的脚本会减慢代理速度并可能达到令牌限制。在脚本级别过滤/汇总 — 只发出代理需要推理的内容。

---

## 诊断命令

```bash
hermes cron list                    # 显示所有任务、状态、next_run 时间
hermes cron run <job_id>            # 安排在下一个定时器执行（用于测试）
hermes cron edit <job_id>           # 修复配置问题
hermes logs                         # 查看最近的 Hermes 日志
hermes skills list                  # 验证已安装的技能
```

---

## 获取更多帮助

如果您已完成本指南中的步骤但问题仍然存在：

1. 使用 `hermes cron run <job_id>` 运行任务（在下一个网关定时器触发）并在聊天输出中观察错误
2. 检查 `~/.hermes/logs/agent.log` 中的调度程序消息和 `~/.hermes/logs/errors.log` 中的警告
3. 在 [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) 上打开一个 issue，包含：
   - 任务 ID 和计划
   - 交付目标
   - 您的预期与实际发生的情况
   - 日志中的相关错误消息

---

*有关完整的 cron 参考，请参阅 [使用 Cron 自动化任何事情](/docs/guides/automate-with-cron) 和 [计划任务 (Cron)](/docs/user-guide/features/cron)。*