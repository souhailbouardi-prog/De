---
sidebar_position: 5
title: "计划任务（Cron）"
description: "使用自然语言安排自动化任务，使用一个 cron 工具管理它们，并附加一个或多个技能"
---

# 计划任务（Cron）

使用自然语言或 cron 表达式安排任务自动运行。Hermes 通过单个 `cronjob` 工具公开 cron 管理，使用操作风格的操作而不是单独的 schedule/list/remove 工具。

## cron 现在可以做什么

Cron 作业可以：

- 安排一次性或重复任务
- 暂停、恢复、编辑、触发和删除作业
- 为作业附加零个、一个或多个技能
- 将结果交付回原始聊天、本地文件或配置的平台目标
- 在带有正常静态工具列表的新代理会话中运行

:::warning
Cron 运行的会话不能递归创建更多 cron 作业。Hermes 在 cron 执行中禁用 cron 管理工具，以防止失控的计划循环。
:::

## 创建计划任务

### 在聊天中使用 `/cron`

```bash
/cron add 30m "Remind me to check the build"
/cron add "every 2h" "Check server status"
/cron add "every 1h" "Summarize new feed items" --skill blogwatcher
/cron add "every 1h" "Use both skills and combine the result" --skill blogwatcher --skill find-nearby
```

### 从独立 CLI

```bash
hermes cron create "every 2h" "Check server status"
hermes cron create "every 1h" "Summarize new feed items" --skill blogwatcher
hermes cron create "every 1h" "Use both skills and combine the result" \
  --skill blogwatcher \
  --skill find-nearby \
  --name "Skill combo"
```

### 通过自然对话

正常询问 Hermes：

```text
Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.
```

Hermes 将在内部使用统一的 `cronjob` 工具。

## 技能支持的 cron 作业

Cron 作业可以在运行提示之前加载一个或多个技能。

### 单个技能

```python
cronjob(
    action="create",
    skill="blogwatcher",
    prompt="Check the configured feeds and summarize anything new.",
    schedule="0 9 * * *",
    name="Morning feeds",
)
```

### 多个技能

技能按顺序加载。提示成为分层在这些技能之上的任务指令。

```python
cronjob(
    action="create",
    skills=["blogwatcher", "find-nearby"],
    prompt="Look for new local events and interesting nearby places, then combine them into one short brief.",
    schedule="every 6h",
    name="Local brief",
)
```

当您希望计划的代理继承可重用的工作流而不将完整的技能文本塞进 cron 提示本身时，这很有用。

## 编辑作业

您不需要删除和重新创建作业来更改它们。

### 聊天

```bash
/cron edit <job_id> --schedule "every 4h"
/cron edit <job_id> --prompt "Use the revised task"
/cron edit <job_id> --skill blogwatcher --skill find-nearby
/cron edit <job_id> --remove-skill blogwatcher
/cron edit <job_id> --clear-skills
```

### 独立 CLI

```bash
hermes cron edit <job_id> --schedule "every 4h"
hermes cron edit <job_id> --prompt "Use the revised task"
hermes cron edit <job_id> --skill blogwatcher --skill find-nearby
hermes cron edit <job_id> --add-skill find-nearby
hermes cron edit <job_id> --remove-skill blogwatcher
hermes cron edit <job_id> --clear-skills
```

备注：

- 重复的 `--skill` 替换作业的附加技能列表
- `--add-skill` 追加到现有列表而不替换它
- `--remove-skill` 删除特定的附加技能
- `--clear-skills` 删除所有附加技能

## 生命周期操作

Cron 作业现在拥有比仅创建/删除更完整的生命周期。

### 聊天

```bash
/cron list
/cron pause <job_id>
/cron resume <job_id>
/cron run <job_id>
/cron remove <job_id>
```

### 独立 CLI

```bash
hermes cron list
hermes cron pause <job_id>
hermes cron resume <job_id>
hermes cron run <job_id>
hermes cron remove <job_id>
hermes cron status
hermes cron tick
```

它们的作用：

- `pause` — 保留作业但停止安排它
- `resume` — 重新启用作业并计算下一个未来运行
- `run` — 在下一个调度器 tick 上触发作业
- `remove` — 完全删除它

## 工作原理

**Cron 执行由网关守护进程处理。** 网关每 60 秒 tick 一次调度器，在隔离的代理会话中运行任何到期的作业。

```bash
hermes gateway install     # 安装为用户服务
sudo hermes gateway install --system   # Linux：服务器的启动时系统服务
hermes gateway             # 或在前台运行

hermes cron list
hermes cron status
```

### 网关调度器行为

在每个 tick 上 Hermes：

1. 从 `~/.hermes/cron/jobs.json` 加载作业
2. 检查 `next_run_at` 与当前时间
3. 为每个到期的作业启动新的 `AIAgent` 会话
4. 可选地将一个或多个附加技能注入到那个新会话中
5. 运行提示直到完成
6. 交付最终响应
7. 更新运行元数据和下一个计划时间

`~/.hermes/cron/.tick.lock` 处的文件锁防止重叠的调度器 tick 重复运行同一作业批次。

## 交付选项

安排作业时，您指定输出去哪里：

| 选项 | 描述 | 示例 |
|--------|-------------|---------|
| `"origin"` | 回到作业创建的位置 | 消息平台上的默认值 |
| `"local"` | 仅保存到本地文件（`~/.hermes/cron/output/`） | CLI 上的默认值 |
| `"telegram"` | Telegram 家庭频道 | 使用 `TELEGRAM_HOME_CHANNEL` |
| `"telegram:123456"` | 按 ID 的特定 Telegram 聊天 | 直接交付 |
| `"telegram:-100123:17585"` | 特定 Telegram 主题 | `chat_id:thread_id` 格式 |
| `"discord"` | Discord 家庭频道 | 使用 `DISCORD_HOME_CHANNEL` |
| `"discord:#engineering"` | 特定 Discord 频道 | 按频道名称 |
| `"slack"` | Slack 家庭频道 | |
| `"whatsapp"` | WhatsApp 家庭 | |
| `"signal"` | Signal | |
| `"matrix"` | Matrix 家庭房间 | |
| `"mattermost"` | Mattermost 家庭频道 | |
| `"email"` | 电子邮件 | |
| `"sms"` | 通过 Twilio 的 SMS | |
| `"homeassistant"` | Home Assistant | |
| `"dingtalk"` | DingTalk | |
| `"feishu"` | Feishu/Lark | |
| `"wecom"` | WeCom | |
| `"weixin"` | Weixin (WeChat) | |
| `"bluebubbles"` | BlueBubbles (iMessage) | |
| `"qqbot"` | QQ Bot (Tencent QQ) | |

代理的最终响应会自动交付。您不需要在 cron 提示中调用 `send_message`。

### 响应包装

默认情况下，交付的 cron 输出用页眉和页脚包装，以便收件人知道它来自计划任务：

```
Cronjob Response: Morning feeds
-------------

<agent output here>

Note: The agent cannot see this message, and therefore cannot respond to it.
```

要在没有包装的情况下交付原始代理输出，请将 `cron.wrap_response` 设置为 `false`：

```yaml
# ~/.hermes/config.yaml
cron:
  wrap_response: false
```

### 静默抑制

如果代理的最终响应以 `[SILENT]` 开头，交付将被完全抑制。输出仍会在本地保存以供审计（在 `~/.hermes/cron/output/` 中），但不会向交付目标发送消息。

这对于仅应在出现问题时报告的监视作业很有用：

```text
Check if nginx is running. If everything is healthy, respond with only [SILENT].
Otherwise, report the issue.
```

失败的作业无论 `[SILENT]` 标记如何都会始终交付 — 只有成功的运行可以被静默。

## 脚本超时

预运行脚本（通过 `script` 参数附加）的默认超时为 120 秒。如果您的脚本需要更长时间 — 例如，包含避免类似机器人的定时模式的随机延迟 — 您可以增加这个：

```yaml
# ~/.hermes/config.yaml
cron:
  script_timeout_seconds: 300   # 5 分钟
```

或设置 `HERMES_CRON_SCRIPT_TIMEOUT` 环境变量。解析顺序是：环境变量 → config.yaml → 120s 默认值。

## 提供程序恢复

Cron 作业继承您配置的备用提供程序和凭据池轮换。如果主 API 密钥受到速率限制或提供程序返回错误，cron 代理可以：

- **回退到备用提供程序**，如果您在 `config.yaml` 中配置了 `fallback_providers`（或遗留的 `fallback_model`）
- **轮换到同一提供程序的[凭据池](/docs/user-guide/configuration#凭据池策略)中的下一个凭据**

这意味着以高频率或在高峰时段运行的 cron 作业更具弹性 — 单个受速率限制的密钥不会使整个运行失败。

## 计划格式

代理的最终响应会自动交付 — 您**不需要**在 cron 提示中为相同目的地包含 `send_message`。如果 cron 运行调用 `send_message` 到调度器已经将交付到的确切目标，Hermes 会跳过重复发送并告诉模型将面向用户的内容放在最终响应中。仅对额外或不同的目标使用 `send_message`。

### 相对延迟（一次性）

```text
30m     → 30 分钟后运行一次
2h      → 2 小时后运行一次
1d      → 1 天后运行一次
```

### 间隔（重复）

```text
every 30m    → 每 30 分钟
every 2h     → 每 2 小时
every 1d     → 每天
```

### Cron 表达式

```text
0 9 * * *       → 每天上午 9:00
0 9 * * 1-5     → 工作日上午 9:00
0 */6 * * *     → 每 6 小时
30 8 1 * *      → 每月 1 日上午 8:30
0 0 * * 0       → 每周日午夜
```

### ISO 时间戳

```text
2026-03-15T09:00:00    → 2026 年 3 月 15 日上午 9:00 一次性
```

## 重复行为

| 计划类型 | 默认重复 | 行为 |
|--------------|----------------|----------|
| 一次性（`30m`、时间戳） | 1 | 运行一次 |
| 间隔（`every 2h`） | forever | 运行直到删除 |
| Cron 表达式 | forever | 运行直到删除 |

您可以覆盖它：

```python
cronjob(
    action="create",
    prompt="...",
    schedule="every 2h",
    repeat=5,
)
```

## 以编程方式管理作业

面向代理的 API 是一个工具：

```python
cronjob(action="create", ...)
cronjob(action="list")
cronjob(action="update", job_id="...")
cronjob(action="pause", job_id="...")
cronjob(action="resume", job_id="...")
cronjob(action="run", job_id="...")
cronjob(action="remove", job_id="...")
```

对于 `update`，传递 `skills=[]` 以删除所有附加技能。

## 作业存储

作业存储在 `~/.hermes/cron/jobs.json` 中。作业运行的输出保存到 `~/.hermes/cron/output/{job_id}/{timestamp}.md`。

存储使用原子文件写入，因此中断的写入不会留下部分写入的作业文件。

## 自包含提示仍然很重要

:::warning 重要
Cron 作业在完全新的代理会话中运行。提示必须包含代理所需的、尚未由附加技能提供的所有内容。
:::

**不好：** `"Check on that server issue"`

**好：** `"SSH into server 192.168.1.100 as user 'deploy', check if nginx is running with 'systemctl status nginx', and verify https://example.com returns HTTP 200."`

## 安全性

计划任务提示在创建和更新时被扫描提示注入和凭据泄露模式。包含不可见的 Unicode 技巧、SSH 后门尝试或明显的机密泄露有效负载的提示会被阻止。
