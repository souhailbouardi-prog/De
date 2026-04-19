---
sidebar_position: 4
title: "Slack"
description: "使用 Socket Mode 将 Hermes Agent 设置为 Slack 机器人"
---

# Slack 设置

使用 Socket Mode 将 Hermes Agent 作为机器人连接到 Slack。Socket Mode 使用 WebSockets 而不是公共 HTTP 端点，因此您的 Hermes 实例不需要公开可访问 — 它可以在防火墙后面、您的笔记本电脑上或私有服务器上工作。

:::warning 经典 Slack 应用已弃用
经典 Slack 应用（使用 RTM API）在 2025 年 3 月**完全弃用**。Hermes 使用带有 Socket Mode 的现代 Bolt SDK。如果您有旧的经典应用，必须按照以下步骤创建新应用。
:::

## 概述

| 组件 | 值 |
|-----------|-------|
| **库** | `slack-bolt` / `slack_sdk` for Python（Socket Mode） |
| **连接** | WebSocket — 不需要公共 URL |
| **所需的认证令牌** | 机器人令牌 (`xoxb-`) + 应用级别令牌 (`xapp-`) |
| **用户标识** | Slack 成员 ID（例如 `U01ABC2DEF3`） |

---

## 步骤 1：创建 Slack 应用

1. 前往 [https://api.slack.com/apps](https://api.slack.com/apps)
2. 点击 **Create New App**
3. 选择 **From scratch**
4. 输入应用名称（例如 "Hermes Agent"）并选择您的工作区
5. 点击 **Create App**

您将进入应用的 **Basic Information** 页面。

---

## 步骤 2：配置机器人令牌范围

在侧边栏中导航到 **Features → OAuth & Permissions**。滚动到 **Scopes → Bot Token Scopes** 并添加以下内容：

| 范围 | 用途 |
|-------|---------|
| `chat:write` | 以机器人身份发送消息 |
| `app_mentions:read` | 检测在频道中何时被 @提及 |
| `channels:history` | 读取机器人所在的公共频道中的消息 |
| `channels:read` | 列出和获取有关公共频道的信息 |
| `groups:history` | 读取机器人被邀请到的私有频道中的消息 |
| `im:history` | 读取直接消息历史 |
| `im:read` | 查看基本 DM 信息 |
| `im:write` | 打开和管理 DM |
| `users:read` | 查找用户信息 |
| `files:read` | 读取和下载附加文件，包括语音笔记/音频 |
| `files:write` | 上传文件（图像、音频、文档） |

:::caution 缺少范围 = 缺少功能
没有 `channels:history` 和 `groups:history`，机器人**将不会在频道中接收消息** — 它只会在 DM 中工作。这些是最常被遗漏的范围。
:::

**可选范围：**

| 范围 | 用途 |
|-------|---------|
| `groups:read` | 列出和获取有关私有频道的信息 |

---

## 步骤 3：启用 Socket Mode

Socket Mode 允许机器人通过 WebSocket 连接，而不需要公共 URL。

1. 在侧边栏中，前往 **Settings → Socket Mode**
2. 将 **Enable Socket Mode** 切换为 ON
3. 系统会提示您创建一个 **App-Level Token**：
   - 给它起一个名字，例如 `hermes-socket`（名称无关紧要）
   - 添加 **`connections:write`** 范围
   - 点击 **Generate**
4. **复制令牌** — 它以 `xapp-` 开头。这是您的 `SLACK_APP_TOKEN`

:::tip
您始终可以在 **Settings → Basic Information → App-Level Tokens** 下找到或重新生成应用级别令牌。
:::

---

## 步骤 4：订阅事件

此步骤至关重要 — 它控制机器人可以看到哪些消息。

1. 在侧边栏中，前往 **Features → Event Subscriptions**
2. 将 **Enable Events** 切换为 ON
3. 展开 **Subscribe to bot events** 并添加：

| 事件 | 是否必需？ | 用途 |
|-------|-----------|---------|
| `message.im` | **是** | 机器人接收直接消息 |
| `message.channels` | **是** | 机器人接收它被添加到的**公共**频道中的消息 |
| `message.groups` | **推荐** | 机器人接收它被邀请到的**私有**频道中的消息 |
| `app_mention` | **是** | 防止在机器人被 @提及时 Bolt SDK 出错 |

4. 点击页面底部的 **Save Changes**

:::danger 缺少事件订阅是 #1 设置问题
如果机器人在 DM 中工作但**不在频道中**工作，您几乎肯定忘记添加 `message.channels`（用于公共频道）和/或 `message.groups`（用于私有频道）。没有这些事件，Slack 根本不会向机器人传递频道消息。
:::

---

## 步骤 5：启用消息选项卡

此步骤启用对机器人的直接消息。没有它，用户在尝试 DM 机器人时会看到 **"Sending messages to this app has been turned off"**。

1. 在侧边栏中，前往 **Features → App Home**
2. 滚动到 **Show Tabs**
3. 将 **Messages Tab** 切换为 ON
4. 勾选 **"Allow users to send Slash commands and messages from the messages tab"**

:::danger 没有此步骤，DM 完全被阻止
即使有所有正确的范围和事件订阅，Slack 也不会允许用户向机器人发送直接消息，除非启用了消息选项卡。这是 Slack 平台要求，不是 Hermes 配置问题。
:::

---

## 步骤 6：安装应用到工作区

1. 在侧边栏中，前往 **Settings → Install App**
2. 点击 **Install to Workspace**
3. 查看权限并点击 **Allow**
4. 授权后，您会看到一个以 `xoxb-` 开头的 **Bot User OAuth Token**
5. **复制此令牌** — 这是您的 `SLACK_BOT_TOKEN`

:::tip
如果您以后更改范围或事件订阅，**必须重新安装应用**才能使更改生效。Install App 页面会显示一个横幅提示您这样做。
:::

---

## 步骤 7：查找允许列表的用户 ID

Hermes 使用 Slack **成员 ID**（不是用户名或显示名称）作为允许列表。

查找成员 ID：

1. 在 Slack 中，点击用户的名称或头像
2. 点击 **View full profile**
3. 点击 **⋮**（更多）按钮
4. 选择 **Copy member ID**

成员 ID 看起来像 `U01ABC2DEF3`。您至少需要自己的成员 ID。

---

## 步骤 8：配置 Hermes

将以下内容添加到您的 `~/.hermes/.env` 文件：

```bash
# 必需
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_ALLOWED_USERS=U01ABC2DEF3              # 逗号分隔的成员 ID

# 可选
SLACK_HOME_CHANNEL=C01234567890              # cron/计划消息的默认频道
SLACK_HOME_CHANNEL_NAME=general              # 主频道的人类可读名称（可选）
```

或运行交互式设置：

```bash
hermes gateway setup    # 提示时选择 Slack
```

然后启动网关：

```bash
hermes gateway              # 前台
hermes gateway install      # 作为用户服务安装
sudo hermes gateway install --system   # 仅限 Linux：启动时系统服务
```

---

## 步骤 9：邀请机器人到频道

启动网关后，您需要**邀请机器人**到任何您希望它响应的频道：

```
/invite @Hermes Agent
```

机器人**不会**自动加入频道。您必须单独邀请它到每个频道。

---

## 机器人如何响应

了解 Hermes 在不同上下文中的行为：

| 上下文 | 行为 |
|---------|----------|
| **DM** | 机器人响应每条消息 — 不需要 @提及 |
| **频道** | 机器人**只在被 @提及时响应**（例如 `@Hermes Agent what time is it?`）。在频道中，Hermes 会在该消息附带的线程中回复。 |
| **线程** | 如果您在现有线程中 @提及 Hermes，它会在同一线程中回复。一旦机器人在线程中有活动会话，**该线程中的后续回复不需要 @提及** — 机器人自然地跟随对话。 |

:::tip
在频道中，始终 @提及机器人以开始对话。一旦机器人在线程中活跃，您可以在该线程中回复而不提及它。在线程外，没有 @提及的消息会被忽略，以防止在繁忙频道中产生噪音。
:::

---

## 配置选项

除了步骤 8 中的必需环境变量外，您还可以通过 `~/.hermes/config.yaml` 自定义 Slack 机器人行为。

### 线程和回复行为

```yaml
platforms:
  slack:
    # 控制多部分响应如何线程化
    # "off"   — 从不将回复线程化到原始消息
    # "first" — 第一个块线程化到用户消息（默认）
    # "all"   — 所有块线程化到用户消息
    reply_to_mode: "first"

    extra:
      # 是否在线程中回复（默认：true）。
      # 当为 false 时，频道消息会获得直接频道回复，而不是线程。
      # 现有线程内的消息仍然在线程中回复。
      reply_in_thread: true

      # 也将线程回复发布到主频道
      # （Slack 的 "Also send to channel" 功能）。
      # 只有第一个回复的第一个块被广播。
      reply_broadcast: false
```

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `platforms.slack.reply_to_mode` | `"first"` | 多部分消息的线程模式：`"off"`、`"first"` 或 `"all"` |
| `platforms.slack.extra.reply_in_thread` | `true` | 当为 `false` 时，频道消息会获得直接回复，而不是线程。现有线程内的消息仍然在线程中回复。 |
| `platforms.slack.extra.reply_broadcast` | `false` | 当为 `true` 时，线程回复也会发布到主频道。只有第一个块被广播。 |

### 会话隔离

```yaml
# 全局设置 — 适用于 Slack 和所有其他平台
group_sessions_per_user: true
```

当为 `true`（默认）时，共享频道中的每个用户都会获得自己的隔离对话会话。在 `#general` 中与 Hermes 交谈的两个人会有单独的历史和上下文。

如果您想要协作模式，其中整个频道共享一个对话会话，请设置为 `false`。请注意，这意味着用户共享上下文增长和令牌成本，一个用户的 `/reset` 会清除所有人的会话。

### 提及和触发行为

```yaml
slack:
  # 在频道中需要 @提及（这是默认行为；
  # Slack 适配器无论如何都会在频道中强制执行 @提及门控，
  # 但您可以为与其他平台的一致性明确设置此值）
  require_mention: true

  # 触发机器人的自定义提及模式
  # （除了默认的 @提及检测）
  mention_patterns:
    - "hey hermes"
    - "hermes,"

  # 每个传出消息的前缀文本
  reply_prefix: ""
```

:::info
与 Discord 和 Telegram 不同，Slack 没有 `free_response_channels` 等效项。Slack 适配器需要 `@提及` 来在频道中开始对话。但是，一旦机器人在线程中有活动会话，后续的线程回复不需要提及。在 DM 中，机器人总是不需要提及就响应。
:::

### 未授权用户处理

```yaml
slack:
  # 当未授权用户（不在 SLACK_ALLOWED_USERS 中）DM 机器人时会发生什么
  # "pair"   — 提示他们输入配对代码（默认）
  # "ignore" — 静默丢弃消息
  unauthorized_dm_behavior: "pair"
```

您也可以为所有平台全局设置：

```yaml
unauthorized_dm_behavior: "pair"
```

`slack:` 下的平台特定设置优先于全局设置。

### 语音转录

```yaml
# 全局设置 — 启用/禁用传入语音消息的自动转录
stt_enabled: true
```

当为 `true`（默认）时，传入的音频消息会在被代理处理之前使用配置的 STT 提供商自动转录。

### 完整示例

```yaml
# 全局网关设置
group_sessions_per_user: true
unauthorized_dm_behavior: "pair"
stt_enabled: true

# Slack 特定设置
slack:
  require_mention: true
  unauthorized_dm_behavior: "pair"

# 平台配置
platforms:
  slack:
    reply_to_mode: "first"
    extra:
      reply_in_thread: true
      reply_broadcast: false
```

---

## 主频道

将 `SLACK_HOME_CHANNEL` 设置为一个频道 ID，Hermes 将在其中传递计划消息、cron 作业结果和其他主动通知。要查找频道 ID：

1. 在 Slack 中右键点击频道名称
2. 点击 **View channel details**
3. 滚动到底部 — 频道 ID 显示在那里

```bash
SLACK_HOME_CHANNEL=C01234567890
```

确保机器人已**被邀请到频道**（`/invite @Hermes Agent`）。

---

## 多工作区支持

Hermes 可以使用单个网关实例同时连接到**多个 Slack 工作区**。每个工作区使用其自己的机器人用户 ID 独立认证。

### 配置

在 `SLACK_BOT_TOKEN` 中提供多个机器人令牌作为**逗号分隔的列表**：

```bash
# 多个机器人令牌 — 每个工作区一个
SLACK_BOT_TOKEN=xoxb-workspace1-token,xoxb-workspace2-token,xoxb-workspace3-token

# 仍使用单个应用级别令牌进行 Socket Mode
SLACK_APP_TOKEN=xapp-your-app-token
```

或在 `~/.hermes/config.yaml` 中：

```yaml
platforms:
  slack:
    token: "xoxb-workspace1-token,xoxb-workspace2-token"
```

### OAuth 令牌文件

除了环境或配置中的令牌外，Hermes 还从**OAuth 令牌文件**加载令牌：

```
~/.hermes/slack_tokens.json
```

此文件是一个 JSON 对象，将团队 ID 映射到令牌条目：

```json
{
  "T01ABC2DEF3": {
    "token": "xoxb-workspace-token-here",
    "team_name": "My Workspace"
  }
}
```

来自此文件的令牌会与通过 `SLACK_BOT_TOKEN` 指定的任何令牌合并。重复的令牌会自动去重。

### 工作原理

- **第一个令牌**是主要令牌，用于 Socket Mode 连接（AsyncApp）。
- 每个令牌在启动时通过 `auth.test` 进行认证。网关将每个 `team_id` 映射到其自己的 `WebClient` 和 `bot_user_id`。
- 当消息到达时，Hermes 使用正确的工作区特定客户端进行响应。
- 主 `bot_user_id`（来自第一个令牌）用于与期望单个机器人身份的功能向后兼容。

---

## 语音消息

Hermes 支持 Slack 上的语音：

- **传入：** 语音/音频消息使用配置的 STT 提供商自动转录：本地 `faster-whisper`、Groq Whisper (`GROQ_API_KEY`) 或 OpenAI Whisper (`VOICE_TOOLS_OPENAI_KEY`)
- **传出：** TTS 响应作为音频文件附件发送

---

## 按频道提示

为特定的 Slack 频道分配临时系统提示。提示在运行时每次轮次注入 — 从不持久化到对话历史 — 因此更改会立即生效。

```yaml
slack:
  channel_prompts:
    "C01RESEARCH": |
      你是一个研究助手。专注于学术来源、
      引用和简洁的综合。
    "C02ENGINEERING": |
      代码审查模式。精确关注边缘情况和
      性能影响。
```

键是 Slack 频道 ID（通过频道详细信息 → "About" → 滚动到底部找到）。匹配频道中的所有消息都会将提示作为临时系统指令注入。

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| 机器人不响应 DM | 验证 `message.im` 在您的事件订阅中，并且应用已重新安装 |
| 机器人在 DM 中工作但不在频道中 | **最常见问题。** 添加 `message.channels` 和 `message.groups` 到事件订阅，重新安装应用，并使用 `/invite @Hermes Agent` 邀请机器人到频道 |
| 机器人不响应频道中的 @提及 | 1) 检查 `message.channels` 事件是否已订阅。2) 机器人必须被邀请到频道。3) 确保添加了 `channels:history` 范围。4) 在范围/事件更改后重新安装应用 |
| 机器人忽略私有频道中的消息 | 添加 `message.groups` 事件订阅和 `groups:history` 范围，然后重新安装应用并 `/invite` 机器人 |
| DM 中 "Sending messages to this app has been turned off" | 在 App Home 设置中启用 **Messages Tab**（见步骤 5） |
| "not_authed" 或 "invalid_auth" 错误 | 重新生成您的 Bot Token 和 App Token，更新 `.env` |
| 机器人响应但无法在频道中发帖 | 使用 `/invite @Hermes Agent` 邀请机器人到频道 |
| "missing_scope" 错误 | 在 OAuth & Permissions 中添加所需范围，然后**重新安装**应用 |
| Socket 频繁断开 | 检查您的网络；Bolt 会自动重连，但不稳定的连接会导致延迟 |
| 更改了范围/事件但没有变化 | 您**必须**在任何范围或事件订阅更改后将应用**重新安装**到您的工作区 |

### 快速检查表

如果机器人在频道中不工作，请验证**所有**以下内容：

1. ✅ 订阅了 `message.channels` 事件（用于公共频道）
2. ✅ 订阅了 `message.groups` 事件（用于私有频道）
3. ✅ 订阅了 `app_mention` 事件
4. ✅ 添加了 `channels:history` 范围（用于公共频道）
5. ✅ 添加了 `groups:history` 范围（用于私有频道）
6. ✅ 添加范围/事件后**重新安装**了应用
7. ✅ 机器人已**被邀请**到频道（`/invite @Hermes Agent`）
8. ✅ 您在消息中**@提及**了机器人

---

## 安全性

:::warning
**始终设置 `SLACK_ALLOWED_USERS`** 带有授权用户的成员 ID。没有此设置，网关会**默认拒绝所有消息**作为安全措施。永远不要分享您的机器人令牌 — 像对待密码一样对待它们。
:::

- 令牌应存储在 `~/.hermes/.env` 中（文件权限 `600`）
- 通过 Slack 应用设置定期轮换令牌
- 审核谁可以访问您的 Hermes 配置目录
- Socket Mode 意味着没有公共端点被暴露 — 减少了一个攻击面