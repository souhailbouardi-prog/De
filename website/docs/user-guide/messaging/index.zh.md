---
sidebar_position: 1
title: "消息网关"
description: "从Telegram、Discord、Slack、WhatsApp、Signal、SMS、Email、Home Assistant、Mattermost、Matrix、钉钉、Webhooks或任何OpenAI兼容的前端通过API服务器与Hermes聊天 — 架构和设置概述"
---

# 消息网关

从Telegram、Discord、Slack、WhatsApp、Signal、SMS、Email、Home Assistant、Mattermost、Matrix、钉钉、飞书/Lark、企业微信、微信、BlueBubbles (iMessage)、QQ或您的浏览器与Hermes聊天。网关是一个单一的后台进程，连接到所有配置的平台，处理会话，运行定时任务，并传递语音消息。

对于完整的语音功能集 — 包括CLI麦克风模式、消息中的语音回复和Discord语音频道对话 — 请参阅[语音模式](/docs/user-guide/features/voice-mode)和[在Hermes中使用语音模式](/docs/guides/use-voice-mode-with-hermes)。

## 平台比较

| 平台 | 语音 | 图像 | 文件 | 线程 | 反应 | 输入 | 流式 |
|----------|:-----:|:------:|:-----:|:-------:|:---------:|:------:|:---------:|
| Telegram | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| Discord | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Slack | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| WhatsApp | — | ✅ | ✅ | — | — | ✅ | ✅ |
| Signal | — | ✅ | ✅ | — | — | ✅ | ✅ |
| SMS | — | — | — | — | — | — | — |
| Email | — | ✅ | ✅ | ✅ | — | — | — |
| Home Assistant | — | — | — | — | — | — | — |
| Mattermost | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| Matrix | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 钉钉 | — | ✅ | ✅ | — | ✅ | — | ✅ |
| 飞书/Lark | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 企业微信 | ✅ | ✅ | ✅ | — | — | ✅ | ✅ |
| 企业微信回调 | — | — | — | — | — | — | — |
| 微信 | ✅ | ✅ | ✅ | — | — | ✅ | ✅ |
| BlueBubbles | — | ✅ | ✅ | — | ✅ | ✅ | — |
| QQ | ✅ | ✅ | ✅ | — | — | ✅ | — |

**语音** = TTS音频回复和/或语音消息转录。**图像** = 发送/接收图像。**文件** = 发送/接收文件附件。**线程** = 线程化对话。**反应** = 消息上的表情反应。**输入** = 处理时的输入指示器。**流式** = 通过编辑进行渐进式消息更新。

## 架构

```mermaid
flowchart TB
    subgraph Gateway["Hermes Gateway"]
        subgraph Adapters["平台适配器"]
            tg[Telegram]
            dc[Discord]
            wa[WhatsApp]
            sl[Slack]
            sig[Signal]
            sms[SMS]
            em[Email]
            ha[Home Assistant]
            mm[Mattermost]
            mx[Matrix]
            dt[钉钉]
    fs[飞书/Lark]
    wc[企业微信]
    wcb[企业微信回调]
    wx[微信]
    bb[BlueBubbles]
    qq[QQ]
            api["API Server<br/>(OpenAI-compatible)"]
            wh[Webhooks]
        end

        store["Session store<br/>per chat"]
        agent["AIAgent<br/>run_agent.py"]
        cron["Cron scheduler<br/>ticks every 60s"]
    end

    tg --> store
    dc --> store
    wa --> store
    sl --> store
    sig --> store
    sms --> store
    em --> store
    ha --> store
    mm --> store
    mx --> store
    dt --> store
    fs --> store
    wc --> store
    wcb --> store
    wx --> store
    bb --> store
    qq --> store
    api --> store
    wh --> store
    store --> agent
    cron --> store
```

每个平台适配器接收消息，通过每聊天会话存储路由它们，并将它们分发给AIAgent进行处理。网关还运行定时任务调度器，每60秒 tick 一次以执行任何到期的任务。

## 快速设置

配置消息平台的最简单方法是交互式向导：

```bash
hermes gateway setup        # 所有消息平台的交互式设置
```

这将引导您通过箭头键选择配置每个平台，显示哪些平台已经配置，并在完成后提供启动/重启网关的选项。

## 网关命令

```bash
hermes gateway              # 在前台运行
hermes gateway setup        # 交互式配置消息平台
hermes gateway install      # 安装为用户服务（Linux）/ launchd服务（macOS）
sudo hermes gateway install --system   # 仅Linux：安装启动时系统服务
hermes gateway start        # 启动默认服务
hermes gateway stop         # 停止默认服务
hermes gateway status       # 检查默认服务状态
hermes gateway status --system         # 仅Linux：明确检查系统服务
```

## 聊天命令（在消息内）

| 命令 | 描述 |
|---------|-------------|
| `/new` 或 `/reset` | 开始新的对话 |
| `/model [provider:model]` | 显示或更改模型（支持 `provider:model` 语法） |
| `/provider` | 显示可用的提供商及其认证状态 |
| `/personality [name]` | 设置个性 |
| `/retry` | 重试最后一条消息 |
| `/undo` | 删除最后一次交换 |
| `/status` | 显示会话信息 |
| `/stop` | 停止运行中的代理 |
| `/approve` | 批准待处理的危险命令 |
| `/deny` | 拒绝待处理的危险命令 |
| `/sethome` | 将此聊天设置为主频道 |
| `/compress` | 手动压缩对话上下文 |
| `/title [name]` | 设置或显示会话标题 |
| `/resume [name]` | 恢复之前命名的会话 |
| `/usage` | 显示此会话的令牌使用情况 |
| `/insights [days]` | 显示使用见解和分析 |
| `/reasoning [level\|show\|hide]` | 更改推理强度或切换推理显示 |
| `/voice [on\|off\|tts\|join\|leave\|status]` | 控制消息语音回复和Discord语音频道行为 |
| `/rollback [number]` | 列出或恢复文件系统检查点 |
| `/background <prompt>` | 在单独的后台会话中运行提示 |
| `/reload-mcp` | 从配置重新加载MCP服务器 |
| `/update` | 将Hermes Agent更新到最新版本 |
| `/help` | 显示可用命令 |
| `/<skill-name>` | 调用任何已安装的技能 |

## 会话管理

### 会话持久性

会话在消息之间持续存在，直到它们重置。代理会记住您的对话上下文。

### 重置策略

会话根据可配置的策略重置：

| 策略 | 默认值 | 描述 |
|--------|---------|-------------|
| 每日 | 4:00 AM | 每天在特定时间重置 |
| 空闲 | 1440 min | 不活动N分钟后重置 |
| 两者 | (组合) | 以先触发的为准 |

在 `~/.hermes/gateway.json` 中配置每个平台的覆盖：

```json
{
  "reset_by_platform": {
    "telegram": { "mode": "idle", "idle_minutes": 240 },
    "discord": { "mode": "idle", "idle_minutes": 60 }
  }
}
```

## 安全性

**默认情况下，网关拒绝所有不在允许列表中或未通过私聊配对的用户。** 这是对具有终端访问权限的机器人的安全默认设置。

```bash
# 限制特定用户（推荐）：
TELEGRAM_ALLOWED_USERS=123456789,987654321
DISCORD_ALLOWED_USERS=123456789012345678
SIGNAL_ALLOWED_USERS=+155****4567,+155****6543
SMS_ALLOWED_USERS=+155****4567,+155****6543
EMAIL_ALLOWED_USERS=trusted@example.com,colleague@work.com
MATTERMOST_ALLOWED_USERS=3uo8dkh1p7g1mfk49ear5fzs5c
MATRIX_ALLOWED_USERS=@alice:matrix.org
DINGTALK_ALLOWED_USERS=user-id-1
FEISHU_ALLOWED_USERS=ou_xxxxxxxx,ou_yyyyyyyy
WECOM_ALLOWED_USERS=user-id-1,user-id-2
WECOM_CALLBACK_ALLOWED_USERS=user-id-1,user-id-2

# 或允许
GATEWAY_ALLOWED_USERS=123456789,987654321

# 或明确允许所有用户（不建议用于具有终端访问权限的机器人）：
GATEWAY_ALLOW_ALL_USERS=true
```

### 私聊配对（允许列表的替代方案）

代替手动配置用户ID，未知用户在私聊机器人时会收到一次性配对码：

```bash
# 用户看到："配对码：XKGH5N7P"
# 您批准他们：
hermes pairing approve telegram XKGH5N7P

# 其他配对命令：
hermes pairing list          # 查看待处理和已批准的用户
hermes pairing revoke telegram 123456789  # 移除访问权限
```

配对码在1小时后过期，有速率限制，并使用加密随机性。

## 中断代理

在代理工作时发送任何消息以中断它。关键行为：

- **进行中的终端命令立即被终止**（SIGTERM，然后1秒后SIGKILL）
- **工具调用被取消** — 只有当前执行的工具运行，其余被跳过
- **多条消息被合并** — 中断期间发送的消息被合并为一个提示
- **`/stop` 命令** — 中断而不排队后续消息

## 工具进度通知

在 `~/.hermes/config.yaml` 中控制显示多少工具活动：

```yaml
display:
  tool_progress: all    # off | new | all | verbose
  tool_progress_command: false  # 设置为true以在消息中启用 /verbose
```

启用时，机器人在工作时发送状态消息：

```text
💻 `ls -la`...
🔍 web_search...
📄 web_extract...
🐍 execute_code...
```

## 后台会话

在单独的后台会话中运行提示，以便代理独立处理它，同时您的主聊天保持响应：

```
/background 检查集群中的所有服务器并报告任何宕机的服务器
```

Hermes 立即确认：

```
🔄 后台任务已启动："检查集群中的所有服务器..."
   任务ID：bg_143022_a1b2c3
```

### 工作原理

每个 `/background` 提示会生成一个**单独的代理实例**，异步运行：

- **隔离会话** — 后台代理有自己的会话和对话历史。它不知道您当前的聊天上下文，只接收您提供的提示。
- **相同配置** — 继承您当前网关设置中的模型、提供商、工具集、推理设置和提供商路由。
- **非阻塞** — 您的主聊天保持完全交互。在它工作时发送消息、运行其他命令或启动更多后台任务。
- **结果交付** — 任务完成时，结果被发送回您发出命令的**同一聊天或频道**，前缀为"✅ 后台任务完成"。如果失败，您会看到"❌ 后台任务失败"和错误信息。

### 后台进程通知

当运行后台会话的代理使用 `terminal(background=true)` 启动长时间运行的进程（服务器、构建等）时，网关可以向您的聊天推送状态更新。通过 `~/.hermes/config.yaml` 中的 `display.background_process_notifications` 控制：

```yaml
display:
  background_process_notifications: all    # all | result | error | off
```

| 模式 | 您收到的内容 |
|------|-----------------|
| `all` | 运行输出更新**和**最终完成消息（默认） |
| `result` | 仅最终完成消息（无论退出代码如何） |
| `error` | 仅当退出代码非零时的最终消息 |
| `off` | 完全没有进程监视消息 |

您也可以通过环境变量设置：

```bash
HERMES_BACKGROUND_NOTIFICATIONS=result
```

### 使用场景

- **服务器监控** — "/background 检查所有服务的健康状况，如果有任何问题提醒我"
- **长构建** — "/background 构建并部署暂存环境"，同时继续聊天
- **研究任务** — "/background 研究竞争对手定价并以表格形式总结"
- **文件操作** — "/background 按日期将 ~/Downloads 中的照片组织到文件夹中"

:::tip
消息平台上的后台任务是即发即忘的 — 您不需要等待或检查它们。任务完成时，结果会自动到达同一聊天。
:::

## 服务管理

### Linux (systemd)

```bash
hermes gateway install               # 安装为用户服务
hermes gateway start                 # 启动服务
hermes gateway stop                  # 停止服务
hermes gateway status                # 检查状态
journalctl --user -u hermes-gateway -f  # 查看日志

# 启用持久化（登出后保持运行）
sudo loginctl enable-linger $USER

# 或安装启动时系统服务，仍然以您的用户身份运行
sudo hermes gateway install --system
sudo hermes gateway start --system
sudo hermes gateway status --system
journalctl -u hermes-gateway -f
```

在笔记本电脑和开发盒上使用用户服务。在VPS或无头主机上使用系统服务，这些主机应在启动时恢复，而不依赖于systemd linger。

除非您真的有意，否则避免同时安装用户和系统网关单元。如果Hermes检测到两者，它会发出警告，因为启动/停止/状态行为会变得模糊。

:::info 多个安装
如果您在同一台机器上运行多个Hermes安装（使用不同的 `HERMES_HOME` 目录），每个安装都有自己的systemd服务名称。默认的 `~/.hermes` 使用 `hermes-gateway`；其他安装使用 `hermes-gateway-<hash>`。`hermes gateway` 命令会自动针对您当前 `HERMES_HOME` 的正确服务。
:::

### macOS (launchd)

```bash
hermes gateway install               # 安装为launchd代理
hermes gateway start                 # 启动服务
hermes gateway stop                  # 停止服务
hermes gateway status                # 检查状态
tail -f ~/.hermes/logs/gateway.log   # 查看日志
```

生成的plist位于 `~/Library/LaunchAgents/ai.hermes.gateway.plist`。它包含三个环境变量：

- **PATH** — 安装时的完整shell PATH，带有venv `bin/` 和 `node_modules/.bin` 前缀。这确保用户安装的工具（Node.js、ffmpeg等）可用于网关子进程，如WhatsApp桥接器。
- **VIRTUAL_ENV** — 指向Python虚拟环境，以便工具可以正确解析包。
- **HERMES_HOME** — 将网关范围限定到您的Hermes安装。

:::tip 安装后PATH更改
launchd plists是静态的 — 如果您在设置网关后安装新工具（例如通过nvm安装新的Node.js版本，或通过Homebrew安装ffmpeg），请再次运行 `hermes gateway install` 以捕获更新的PATH。网关将检测到过时的plist并自动重新加载。
:::

:::info 多个安装
与Linux systemd服务一样，每个 `HERMES_HOME` 目录都有自己的launchd标签。默认的 `~/.hermes` 使用 `ai.hermes.gateway`；其他安装使用 `ai.hermes.gateway-<suffix>`。
:::

## 平台特定工具集

每个平台都有自己的工具集：

| 平台 | 工具集 | 功能 |
|----------|---------|--------------|
| CLI | `hermes-cli` | 完全访问 |
| Telegram | `hermes-telegram` | 完整工具，包括终端 |
| Discord | `hermes-discord` | 完整工具，包括终端 |
| WhatsApp | `hermes-whatsapp` | 完整工具，包括终端 |
| Slack | `hermes-slack` | 完整工具，包括终端 |
| Signal | `hermes-signal` | 完整工具，包括终端 |
| SMS | `hermes-sms` | 完整工具，包括终端 |
| Email | `hermes-email` | 完整工具，包括终端 |
| Home Assistant | `hermes-homeassistant` | 完整工具 + HA设备控制（ha_list_entities, ha_get_state, ha_call_service, ha_list_services） |
| Mattermost | `hermes-mattermost` | 完整工具，包括终端 |
| Matrix | `hermes-matrix` | 完整工具，包括终端 |
| 钉钉 | `hermes-dingtalk` | 完整工具，包括终端 |
| 飞书/Lark | `hermes-feishu` | 完整工具，包括终端 |
| 企业微信 | `hermes-wecom` | 完整工具，包括终端 |
| 企业微信回调 | `hermes-wecom-callback` | 完整工具，包括终端 |
| 微信 | `hermes-weixin` | 完整工具，包括终端 |
| BlueBubbles | `hermes-bluebubbles` | 完整工具，包括终端 |
| QQBot | `hermes-qqbot` | 完整工具，包括终端 |
| API Server | `hermes` (默认) | 完整工具，包括终端 |
| Webhooks | `hermes-webhook` | 完整工具，包括终端 |

## 下一步

- [Telegram 设置](telegram.md)
- [Discord 设置](discord.md)
- [Slack 设置](slack.md)
- [WhatsApp 设置](whatsapp.md)
- [Signal 设置](signal.md)
- [SMS 设置 (Twilio)](sms.md)
- [Email 设置](email.md)
- [Home Assistant 集成](homeassistant.md)
- [Mattermost 设置](mattermost.md)
- [Matrix 设置](matrix.md)
- [钉钉 设置](dingtalk.md)
- [飞书/Lark 设置](feishu.md)
- [企业微信 设置](wecom.md)
- [企业微信回调 设置](wecom-callback.md)
- [微信 设置](weixin.md)
- [BlueBubbles 设置 (iMessage)](bluebubbles.md)
- [QQBot 设置](qqbot.md)
- [Open WebUI + API Server](open-webui.md)
- [Webhooks](webhooks.md)