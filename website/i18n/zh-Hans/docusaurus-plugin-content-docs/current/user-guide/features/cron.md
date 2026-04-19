---
sidebar_position: 5
title: "定时任务（Cron）"
description: "使用自然语言安排自动化任务，使用一个 cron 工具管理它们，并附加一个或多个技能"
---

# 定时任务（Cron）

使用自然语言或 cron 表达式安排自动运行的任务。Hermes 通过单个 `cronjob` 工具公开 cron 管理，该工具使用动作式操作，而不是单独的调度/列表/删除工具。

## Cron 现在可以做什么

Cron 作业可以：

- 安排一次性或重复任务
- 暂停、恢复、编辑、触发和删除作业
- 为作业附加零个、一个或多个技能
- 将结果传递回原始聊天、本地文件或配置的平台目标
- 在具有正常静态工具列表的新智能体会话中运行

:::warning
Cron 运行的会话不能递归创建更多 cron 作业。Hermes 在 cron 执行中禁用 cron 管理工具，以防止失控的调度循环。
:::

## 创建定时任务

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

cron 作业可以在运行提示之前加载一个或多个技能。

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

技能按顺序加载。提示成为叠加在这些技能之上的任务指令。

```python
cronjob(
    action="create",
    skills=["blogwatcher", "find-nearby"],
    prompt="Look for new local events and interesting nearby places, then combine them into one short brief.",
    schedule="every 6h",
    name="Local brief",
)
```

这在您希望计划的智能体继承可重用工作流而不将完整技能文本填入 cron 提示本身时非常有用。

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

注意：

- 重复的 `--skill` 会替换作业的附加技能列表
- `--add-skill` 会追加到现有列表而不替换它
- `--remove-skill` 会移除特定的附加技能
- `--clear-skills` 会移除所有附加技能

## 生命周期操作

Cron 作业现在有比创建/删除更完整的生命周期。

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
hermes cron pause &lt;job_id&gt;
hermes cron resume &lt;job_id&gt;
hermes cron run &lt;job_id&gt;
hermes cron remove &lt;job_id&gt;
```
hermes cron resume &lt;job_id&gt;
hermes cron run &lt;job_id&gt;
hermes cron remove &lt;job_id&gt;
hermes cron status
hermes cron tick
```

它们的作用：

- `pause` — 保留作业但停止调度
- `resume` — 重新启用作业并计算下一个未来运行时间
- `run` — 在下次调度器滴答时触发作业
- `remove` — 完全删除它

## 工作原理

**Cron 执行由网关守护进程处理。** 网关每 60 秒滴答一次调度器，在隔离的智能体会话中运行任何到期的作业。

```bash
hermes gateway install     # 作为用户服务安装
sudo hermes gateway install --system   # Linux: 服务器的启动时系统服务
hermes gateway             # 或在前台运行

hermes cron list
hermes cron status
```

### 网关调度器行为

在每次滴答时，Hermes：

1. 从 `~/.hermes/cron/jobs.json` 加载作业
2. 将 `next_run_at` 与当前时间进行比较
3. 为每个到期的作业启动一个新的 `AIAgent` 会话
4. 可选地将一个或多个附加技能注入到该新会话中
5. 运行提示直到完成
6. 传递最终响应
7. 更新运行元数据和下一个计划时间

`~/.hermes/cron/.tick.lock` 处的文件锁防止重叠的调度器滴答重复运行同一批作业。

## 传递选项

安排作业时，您可以指定输出的去向：

| 选项 | 描述 | 示例 |
|--------|-------------|---------|
| `"origin"` | 返回创建作业的地方 | 消息平台上的默认值 |
| `"local"` | 仅保存到本地文件（`~/.hermes/cron/output/`） | CLI 上的默认值 |
| `"telegram"` | Telegram 主频道 | 使用 `TELEGRAM_HOME_CHANNEL` |
| `"telegram:123456"` | 按 ID 指定 Telegram 聊天 | 直接传递 |
| `"telegram:-100123:17585"` | 特定 Telegram 主题 | `chat_id:thread_id` 格式 |
| `"discord"` | Discord 主频道 | 使用 `DISCORD_HOME_CHANNEL` |
| `"discord:#engineering"` | 特定 Discord 频道 | 按频道名称 |
| `"slack"` | Slack 主频道 | |
| `"whatsapp"` | WhatsApp 主页 | |
| `"signal"` | Signal | |
| `"matrix"` | Matrix 主房间 | |
| `"mattermost"` | Mattermost 主频道 | |
| `"email"` | 电子邮件 | |
| "sms" | 通过 Twilio 的短信 | |
| "homeassistant" | Home Assistant | |
| "dingtalk" | 钉钉 | |
| "feishu" | 飞书/Lark | |
| "wecom" | 企业微信 | |
| "weixin" | 微信 | |
| "bluebubbles" | BlueBubbles (iMessage) | |
| "qqbot" | QQ 机器人（腾讯 QQ） | |

智能体的最终响应会自动传递。您不需要在 cron 提示中调用 `send_message`。

### 响应包装

默认情况下，传递的 cron 输出会用页眉和页脚包装，以便接收者知道它来自定时任务：

```
Cronjob Response: Morning feeds
-------------

<智能体输出在这里>

注意：智能体无法看到此消息，因此无法回复。
```

要传递没有包装器的原始智能体输出，请将 `cron.wrap_response` 设置为 `false`：

```yaml
# ~/.hermes/config.yaml
cron:
  wrap_response: false
```

### 静默抑制

如果智能体的最终响应以 `` 开头，则传递会被完全抑制。输出仍会在本地保存以供审计（在 `~/.hermes/cron/output/` 中），但不会向传递目标发送消息。

这对于只在出现问题时才报告的监控作业很有用：

```text
Check if nginx is running. If everything is healthy, respond with only .
Otherwise, report the issue.
```

失败的作业总是会传递，无论 `` 标记如何 — 只有成功的运行可以被静默。

## 脚本超时

预运行脚本（通过 `script` 参数附加）的默认超时为 120 秒。如果您的脚本需要更长时间 — 例如，包含随机延迟以避免机器人式的时间模式 — 您可以增加此值：

```yaml
# ~/.hermes/config.yaml
cron:
  script_timeout_seconds: 300   # 5 分钟
```

或设置 `HERMES_CRON_SCRIPT_TIMEOUT` 环境变量。解析顺序是：环境变量 → config.yaml → 120 秒默认值。

## 提供商恢复

Cron 作业继承您配置的备用提供商和凭证池轮换。如果主 API 密钥被速率限制或提供商返回错误，cron 智能体可以：

- **回退到备用提供商** 如果您在 `config.yaml` 中配置了 `fallback_providers`（或传统的 `fallback_model`）
- **轮换到下一个凭证** 在同一提供商的[凭证池](/docs/user-guide/configuration#credential-pool-strategies)中

这意味着在高频运行或高峰时段运行的 cron 作业更加弹性 — 单个被速率限制的密钥不会导致整个运行失败。

## 调度格式

智能体的最终响应会自动传递 — 您**不需要**在 cron 提示中为同一目的地包含 `send_message`。如果 cron 运行调用 `send_message` 到调度器已经会传递到的确切目标，Hermes 会跳过该重复发送，并告诉模型将面向用户的内容放在最终响应中。仅对其他或不同目标使用 `send_message`。

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
0 0 * * 0       → 每个周日午夜
```

### ISO 时间戳

```text
2026-03-15T09:00:00    → 2026 年 3 月 15 日上午 9:00 一次性运行
```

## 重复行为

| 调度类型 | 默认重复 | 行为 |
|--------------|----------------|----------|
| 一次性（`30m`，时间戳） | 1 | 运行一次 |
| 间隔（`every 2h`） | 永远 | 运行直到被移除 |
| Cron 表达式 | 永远 | 运行直到被移除 |

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

智能体面向的 API 是一个工具：

```python
cronjob(action="create", ...)
cronjob(action="list")
cronjob(action="update", job_id="...")
cronjob(action="pause", job_id="...")
cronjob(action="resume", job_id="...")
cronjob(action="run", job_id="...")
cronjob(action="remove", job_id="...")
```

对于 `update`，传递 `skills=[]` 以移除所有附加技能。

## 作业存储

作业存储在 `~/.hermes/cron/jobs.json` 中。作业运行的输出保存到 `~/.hermes/cron/output/{job_id}/{timestamp}.md`。

存储使用原子文件写入，因此中断的写入不会留下部分写入的作业文件。

## 自包含提示仍然重要

:::warning 重要
Cron 作业在完全新的智能体会话中运行。提示必须包含智能体所需的所有内容，这些内容不是由附加技能提供的。
:::

**错误：** `"Check on that server issue"`

**GOOD:** `"SSH into server 192.168.1.100 as user 'deploy', check if nginx is running with 'systemctl status nginx', and verify https://example.com returns HTTP 200."`

## 安全性

计划任务提示在创建和更新时会扫描提示注入和凭证窃取模式。包含不可见 Unicode 技巧、SSH 后门尝试或明显的秘密窃取有效载荷的提示会被阻止。