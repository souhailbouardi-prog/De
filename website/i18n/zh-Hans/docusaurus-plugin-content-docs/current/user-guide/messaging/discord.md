---
sidebar_position: 3
title: "Discord"
description: "将 Hermes Agent 设置为 Discord 机器人"
---

# Discord 设置

Hermes Agent 作为机器人与 Discord 集成，让您通过直接消息或服务器频道与 AI 助手聊天。机器人接收您的消息，通过 Hermes Agent 管道处理（包括工具使用、记忆和推理），并实时响应。它支持文本、语音消息、文件附件和斜杠命令。

在设置之前，这是大多数人想知道的部分：Hermes 在服务器中的行为方式。

## Hermes 的行为方式

| 上下文 | 行为 |
|---------|----------|
| **私信** | Hermes 响应每条消息。不需要 `@提及`。每个私信都有自己的会话。 |
| **服务器频道** | 默认情况下，Hermes 只有在您 `@提及` 它时才会响应。如果您在频道中发帖但没有提及它，Hermes 会忽略该消息。 |
| **自由响应频道** | 您可以使用 `DISCORD_FREE_RESPONSE_CHANNELS` 使特定频道无需提及，或使用 `DISCORD_REQUIRE_MENTION=false` 全局禁用提及。 |
| **线程** | Hermes 在同一线程中回复。提及规则仍然适用，除非该线程或其父频道被配置为自由响应。线程与父频道的会话历史保持隔离。 |
| **多用户共享频道** | 默认情况下，Hermes 为了安全和清晰起见，在频道内为每个用户隔离会话历史。两个在同一频道中交谈的人不会共享一个对话记录，除非您明确禁用此设置。 |
| **提及其他用户的消息** | 当 `DISCORD_IGNORE_NO_MENTION` 为 `true`（默认值）时，如果消息 @提及其他用户但**未**提及机器人，Hermes 会保持沉默。这可以防止机器人介入针对其他人的对话。如果您希望机器人无论提及谁都响应所有消息，请设置为 `false`。这仅适用于服务器频道，不适用于私信。 |

:::tip
如果您想要一个普通的机器人帮助频道，让人们可以在不每次标记的情况下与 Hermes 交谈，请将该频道添加到 `DISCORD_FREE_RESPONSE_CHANNELS`。
:::

### Discord 网关模型

Discord 上的 Hermes 不是无状态回复的 webhook。它通过完整的消息网关运行，这意味着每条传入消息都要经过：

1. 授权（`DISCORD_ALLOWED_USERS`）
2. 提及/自由响应检查
3. 会话查找
4. 会话记录加载
5. 正常的 Hermes 智能体执行，包括工具、记忆和斜杠命令
6. 响应传递回 Discord

这很重要，因为繁忙服务器中的行为取决于 Discord 路由和 Hermes 会话策略。

### Discord 中的会话模型

默认情况下：

- 每个私信都有自己的会话
- 每个服务器线程都有自己的会话命名空间
- 共享频道中的每个用户在该频道内都有自己的会话

因此，如果 Alice 和 Bob 都在 `#research` 中与 Hermes 交谈，默认情况下 Hermes 会将这些视为单独的对话，即使他们使用的是同一个可见的 Discord 频道。

这由 `config.yaml` 控制：

```yaml
group_sessions_per_user: true
```

只有当您明确希望整个房间有一个共享对话时，才将其设置为 `false`：

```yaml
group_sessions_per_user: false
```

共享会话对于协作房间很有用，但它们也意味着：

- 用户共享上下文增长和令牌成本
- 一个人的长时间工具密集型任务会膨胀其他人的上下文
- 一个人的进行中运行会中断同一房间中其他人的后续操作

### 中断和并发

Hermes 按会话密钥跟踪运行中的智能体。

使用默认的 `group_sessions_per_user: true`：

- Alice 中断自己的进行中请求只会影响该频道中 Alice 的会话
- Bob 可以在同一频道中继续交谈，而不会继承 Alice 的历史或中断 Alice 的运行

使用 `group_sessions_per_user: false`：

- 整个房间共享该频道/线程的一个运行智能体槽位
- 不同人的后续消息可能会相互中断或排队

本指南将引导您完成完整的设置过程 — 从在 Discord 开发者门户创建机器人到发送第一条消息。

## 步骤 1：创建 Discord 应用

1. 前往 [Discord 开发者门户](https://discord.com/developers/applications) 并使用您的 Discord 账户登录。
2. 点击右上角的 **New Application**。
3. 输入应用名称（例如，"Hermes Agent"）并接受开发者服务条款。
4. 点击 **Create**。

您将进入 **General Information** 页面。记下 **Application ID** — 稍后构建邀请 URL 时需要它。

## 步骤 2：创建机器人

1. 在左侧边栏中，点击 **Bot**。
2. Discord 会自动为您的应用创建一个机器人用户。您会看到机器人的用户名，您可以自定义它。
3. 在 **Authorization Flow** 下：
   - 将 **Public Bot** 设置为 **ON** — 使用 Discord 提供的邀请链接（推荐）。这允许安装选项卡生成默认授权 URL。
   - 将 **Require OAuth2 Code Grant** 保持为 **OFF**。

:::tip
您可以在此页面为机器人设置自定义头像和横幅。这是用户在 Discord 中看到的内容。
:::

:::info[私人机器人替代方案]
如果您希望保持机器人为私人（Public Bot = OFF），则在步骤 5 中**必须**使用 **Manual URL** 方法，而不是安装选项卡。Discord 提供的链接要求启用 Public Bot。
:::

## 步骤 3：启用特权网关意图

这是整个设置中最关键的步骤。如果没有启用正确的意图，您的机器人将连接到 Discord，但**将无法读取消息内容**。

在 **Bot** 页面上，向下滚动到 **Privileged Gateway Intents**。您会看到三个切换开关：

| 意图 | 目的 | 是否必需？ |
|--------|---------|-----------| 
| **Presence Intent** | 查看用户在线/离线状态 | 可选 |
| **Server Members Intent** | 访问成员列表，解析用户名 | **必需** |
| **Message Content Intent** | 读取消息的文本内容 | **必需** |

通过将它们切换为 **ON** 来**启用 Server Members Intent 和 Message Content Intent**。

- 没有 **Message Content Intent**，您的机器人会接收消息事件，但消息文本为空 — 机器人实际上看不到您输入的内容。
- 没有 **Server Members Intent**，机器人无法为允许的用户列表解析用户名，可能无法识别谁在向它发送消息。

:::warning[这是 Discord 机器人不工作的 #1 原因]
如果您的机器人在线但从不响应消息，**Message Content Intent** 几乎肯定是禁用的。返回 [开发者门户](https://discord.com/developers/applications)，选择您的应用 → Bot → Privileged Gateway Intents，确保 **Message Content Intent** 已切换为 ON。点击 **Save Changes**。
:::

**关于服务器数量：**
- 如果您的机器人在**少于 100 个服务器**中，您可以简单地自由切换意图。
- 如果您的机器人在**100 个或更多服务器**中，Discord 要求您提交验证申请才能使用特权意图。对于个人使用，这不是问题。

点击页面底部的 **Save Changes**。

## 步骤 4：获取机器人令牌

机器人令牌是 Hermes Agent 用于以您的机器人身份登录的凭证。仍在 **Bot** 页面上：

1. 在 **Token** 部分下，点击 **Reset Token**。
2. 如果您的 Discord 账户启用了双因素认证，请输入您的 2FA 代码。
3. Discord 将显示您的新令牌。**立即复制它。**

:::warning[令牌仅显示一次]
令牌仅显示一次。如果您丢失了它，您需要重置它并生成一个新的。切勿公开分享您的令牌或将其提交到 Git — 任何拥有此令牌的人都可以完全控制您的机器人。
:::

将令牌存储在安全的地方（例如，密码管理器）。您将在步骤 8 中需要它。

## 步骤 5：生成邀请 URL

您需要一个 OAuth2 URL 来邀请机器人到您的服务器。有两种方法可以做到这一点：

### 选项 A：使用安装选项卡（推荐）

:::note[需要 Public Bot]
此方法要求在步骤 2 中将 **Public Bot** 设置为 **ON**。如果您将 Public Bot 设置为 OFF，请改用下面的手动 URL 方法。
:::

1. 在左侧边栏中，点击 **Installation**。
2. 在 **Installation Contexts** 下，启用 **Guild Install**。
3. 对于 **Install Link**，选择 **Discord Provided Link**。
4. 在 Guild Install 的 **Default Install Settings** 下：
   - **Scopes**：选择 `bot` 和 `applications.commands`
   - **Permissions**：选择下面列出的权限。

### 选项 B：手动 URL

您可以使用以下格式直接构建邀请 URL：

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot+applications.commands&permissions=274878286912
```

将 `YOUR_APP_ID` 替换为步骤 1 中的应用 ID。

### 必需的权限

这些是您的机器人需要的最低权限：

- **View Channels** — 查看它有权访问的频道
- **Send Messages** — 响应您的消息
- **Embed Links** — 格式化富响应
- **Attach Files** — 发送图像、音频和文件输出
- **Read Message History** — 维护对话上下文

### 推荐的附加权限

- **Send Messages in Threads** — 在线程对话中响应
- **Add Reactions** — 对消息添加反应以确认

### 权限整数

| 级别 | 权限整数 | 包含内容 |
|-------|-------------------|-----------------|
| 最小 | `117760` | View Channels, Send Messages, Read Message History, Attach Files |
| 推荐 | `274878286912` | 以上所有内容加上 Embed Links, Send Messages in Threads, Add Reactions |

## 步骤 6：邀请到您的服务器

1. 在浏览器中打开邀请 URL（来自安装选项卡或您构建的手动 URL）。
2. 在 **Add to Server** 下拉菜单中，选择您的服务器。
3. 点击 **Continue**，然后点击 **Authorize**。
4. 如果提示，请完成 CAPTCHA。

:::info
您需要在 Discord 服务器上拥有 **Manage Server** 权限才能邀请机器人。如果您在下拉菜单中没有看到您的服务器，请让服务器管理员使用邀请链接。
:::

授权后，机器人将出现在您服务器的成员列表中（在您启动 Hermes 网关之前，它会显示为离线）。

## 步骤 7：查找您的 Discord 用户 ID

Hermes Agent 使用您的 Discord 用户 ID 来控制谁可以与机器人交互。要找到它：

1. 打开 Discord（桌面或网页应用）。
2. 前往 **设置** → **高级** → 将 **开发者模式** 切换为 **ON**。
3. 关闭设置。
4. 右键单击您自己的用户名（在消息、成员列表或您的个人资料中）→ **复制用户 ID**。

您的用户 ID 是一个长数字，如 `284102345871466496`。

:::tip
开发者模式还允许您以相同的方式复制 **频道 ID** 和 **服务器 ID** — 右键单击频道或服务器名称并选择复制 ID。如果您想手动设置主频道，您将需要频道 ID。
:::

## 步骤 8：配置 Hermes Agent

### 选项 A：交互式设置（推荐）

运行引导设置命令：

```bash
hermes gateway setup
```

在提示时选择 **Discord**，然后在询问时粘贴您的机器人令牌和用户 ID。

### 选项 B：手动配置

将以下内容添加到您的 `~/.hermes/.env` 文件中：

```bash
# 必需
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_ALLOWED_USERS=284102345871466496

# 多个允许的用户（逗号分隔）
# DISCORD_ALLOWED_USERS=284102345871466496,198765432109876543
```

然后启动网关：

```bash
hermes gateway
```

机器人应该在几秒钟内在 Discord 上线。向它发送消息 — 无论是私信还是在它可以看到的频道中 — 进行测试。

:::tip
您可以在后台运行 `hermes gateway` 或作为 systemd 服务以实现持久运行。有关详细信息，请参阅部署文档。
:::

## 配置参考

Discord 行为通过两个文件控制：**`~/.hermes/.env`** 用于凭据和环境级切换，以及 **`~/.hermes/config.yaml`** 用于结构化设置。当两者都设置时，环境变量始终优先于 config.yaml 值。

### 环境变量（`.env`）

| 变量 | 必需 | 默认值 | 描述 |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | **是** | — | 来自 [Discord 开发者门户](https://discord.com/developers/applications) 的机器人令牌。 |
| `DISCORD_ALLOWED_USERS` | **是** | — | 允许与机器人交互的逗号分隔的 Discord 用户 ID。没有这个，网关默认拒绝所有用户。 |
| `DISCORD_HOME_CHANNEL` | 否 | — | 机器人发送主动消息（cron 输出、提醒、通知）的频道 ID。 |
| `DISCORD_HOME_CHANNEL_NAME` | 否 | `"Home"` | 日志和状态输出中主频道的显示名称。 |
| `DISCORD_REQUIRE_MENTION` | 否 | `true` | 当为 `true` 时，机器人只在服务器频道中被 `@提及` 时才响应。设置为 `false` 以响应每个频道中的所有消息。 |
| `DISCORD_FREE_RESPONSE_CHANNELS` | 否 | — | 机器人无需 `@提及` 即可响应的逗号分隔频道 ID，即使 `DISCORD_REQUIRE_MENTION` 为 `true`。 |
| `DISCORD_IGNORE_NO_MENTION` | 否 | `true` | 当为 `true` 时，如果消息 `@提及` 其他用户但**未**提及机器人，机器人会保持沉默。防止机器人介入针对其他人的对话。仅适用于服务器频道，不适用于私信。 |
| `DISCORD_AUTO_THREAD` | 否 | `true` | 当为 `true` 时，自动为文本频道中的每个 `@提及` 创建一个新线程，以便每个对话都是隔离的（类似于 Slack 行为）。已经在线程或私信中的消息不受此设置影响。 |
| `DISCORD_ALLOW_BOTS` | 否 | `"none"` | 控制机器人如何处理来自其他 Discord 机器人的消息。`"none"` — 忽略所有其他机器人。`"mentions"` — 只接受 `@提及` Hermes 的机器人消息。`"all"` — 接受所有机器人消息。 |
| `DISCORD_REACTIONS` | 否 | `true` | 当为 `true` 时，机器人在处理过程中会向消息添加表情反应（开始时 👀，成功时 ✅，错误时 ❌）。设置为 `false` 以完全禁用反应。 |
| `DISCORD_IGNORED_CHANNELS` | 否 | — | 机器人**从不**响应的逗号分隔频道 ID，即使被 `@提及`。优先于所有其他频道设置。 |
| `DISCORD_NO_THREAD_CHANNELS` | 否 | — | 机器人直接在频道中响应而不是创建线程的逗号分隔频道 ID。仅当 `DISCORD_AUTO_THREAD` 为 `true` 时相关。 |
| `DISCORD_REPLY_TO_MODE` | 否 | `"first"` | 控制回复引用行为：`"off"` — 从不回复原始消息，`"first"` — 仅在第一个消息块上回复引用（默认），`"all"` — 在每个块上回复引用。 |

### 配置文件（`config.yaml`）

`~/.hermes/config.yaml` 中的 `discord` 部分镜像上面的环境变量。Config.yaml 设置被应用为默认值 — 如果已设置等效的环境变量，环境变量优先。

```yaml
# Discord 特定设置
discord:
  require_mention: true           # 在服务器频道中需要 @提及
  free_response_channels: ""      # 逗号分隔的频道 ID（或 YAML 列表）
  auto_thread: true               # 在 @提及时自动创建线程
  reactions: true                 # 在处理过程中添加表情反应
  ignored_channels: []            # 机器人从不响应的频道 ID
  no_thread_channels: []          # 机器人在不创建线程的情况下响应的频道 ID

# 会话隔离（适用于所有网关平台，不仅是 Discord）
group_sessions_per_user: true     # 在共享频道中为每个用户隔离会话
```

#### `discord.require_mention`

**类型：** boolean — **默认值：** `true`

启用时，机器人仅在服务器频道中被直接 `@提及` 时才响应。私信始终会收到响应，无论此设置如何。

#### `discord.free_response_channels`

**类型：** string 或 list — **默认值：** `""`

机器人无需 `@提及` 即可响应所有消息的频道 ID。接受逗号分隔的字符串或 YAML 列表：

```yaml
# 字符串格式
discord:
  free_response_channels: "1234567890,9876543210"

# 列表格式
discord:
  free_response_channels:
    - 1234567890
    - 9876543210
```

如果线程的父频道在此列表中，线程也会变为无需提及。

#### `discord.auto_thread`

**类型：** boolean — **默认值：** `true`

启用时，常规文本频道中的每个 `@提及` 都会自动为对话创建一个新线程。这可以保持主频道整洁，并为每个对话提供自己的隔离会话历史。一旦创建了线程，该线程中的后续消息不需要 `@提及` — 机器人知道它已经参与其中。

在此设置下，在现有线程或私信中发送的消息不受影响。

#### `discord.reactions`

**类型：** boolean — **默认值：** `true`

控制机器人是否向消息添加表情反应作为视觉反馈：
- 👀 在机器人开始处理您的消息时添加
- ✅ 在响应成功传递时添加
- ❌ 在处理过程中发生错误时添加

如果您觉得反应分散注意力，或者机器人的角色没有 **Add Reactions** 权限，请禁用此功能。

#### `discord.ignored_channels`

**类型：** string 或 list — **默认值：** `[]`

机器人**从不**响应的频道 ID，即使被直接 `@提及`。这具有最高优先级 — 如果频道在此列表中，机器人会在那里静默忽略所有消息，无论 `require_mention`、`free_response_channels` 或任何其他设置如何。

```yaml
# 字符串格式
discord:
  ignored_channels: "1234567890,9876543210"

# 列表格式
discord:
  ignored_channels:
    - 1234567890
    - 9876543210
```

如果线程的父频道在此列表中，该线程中的消息也会被忽略。

#### `discord.no_thread_channels`

**类型：** string 或 list — **默认值：** `[]`

机器人直接在频道中响应而不是自动创建线程的频道 ID。这仅在 `auto_thread` 为 `true`（默认值）时有效。在这些频道中，机器人会像普通消息一样内联响应，而不是生成新线程。

```yaml
discord:
  no_thread_channels:
    - 1234567890  # 机器人在此处内联响应
```

对于专门用于机器人交互的频道很有用，其中线程会添加不必要的噪音。

#### `group_sessions_per_user`

**类型：** boolean — **默认值：** `true`

这是一个全局网关设置（不仅限于 Discord），控制同一频道中的用户是否获得隔离的会话历史。

当为 `true` 时：在 `#research` 中交谈的 Alice 和 Bob 各自与 Hermes 有自己的独立对话。当为 `false` 时：整个频道共享一个对话记录和一个运行智能体槽位。

```yaml
group_sessions_per_user: true
```

有关每种模式的完整含义，请参阅上面的 [会话模型](#session-model-in-discord) 部分。

#### `display.tool_progress`

**类型：** string — **默认值：** `"all"` — **值：** `off`, `new`, `all`, `verbose`

控制机器人在处理过程中是否在聊天中发送进度消息（例如，"读取文件..."，"运行终端命令..."）。这是一个适用于所有平台的全局网关设置。

```yaml
display:
  tool_progress: "all"    # off | new | all | verbose
```

- `off` — 无进度消息
- `new` — 仅显示每轮的第一个工具调用
- `all` — 显示所有工具调用（在网关消息中截断为 40 个字符）
- `verbose` — 显示完整的工具调用详细信息（可能产生长消息）

#### `display.tool_progress_command`

**类型：** boolean — **默认值：** `false`

启用时，在网关中提供 `/verbose` 斜杠命令，让您无需编辑 config.yaml 即可循环通过工具进度模式（`off → new → all → verbose → off`）。

```yaml
display:
  tool_progress_command: true
```

## 交互式模型选择器

在 Discord 频道中发送 `/model` 不带参数，打开基于下拉菜单的模型选择器：

1. **提供商选择** — 显示可用提供商的选择下拉菜单（最多 25 个）。
2. **模型选择** — 为所选提供商显示模型的第二个下拉菜单（最多 25 个）。

选择器在 120 秒后超时。只有授权用户（`DISCORD_ALLOWED_USERS` 中的用户）可以与之交互。如果您知道模型名称，直接输入 `/model <name>`。

## 技能的原生斜杠命令

Hermes 自动将安装的技能注册为**原生 Discord 应用命令**。这意味着技能会出现在 Discord 的自动完成 `/` 菜单中，与内置命令一起。

- 每个技能都成为 Discord 斜杠命令（例如，`/code-review`，`/ascii-art`）
- 技能接受可选的 `args` 字符串参数
- Discord 每个机器人限制 100 个应用命令 — 如果您的技能超过可用槽位，额外的技能会被跳过，并在日志中显示警告
- 技能在机器人启动时与 `/model`、`/reset` 和 `/background` 等内置命令一起注册

无需额外配置 — 通过 `hermes skills install` 安装的任何技能都会在下次网关重启时自动注册为 Discord 斜杠命令。

## 主频道

您可以指定一个"主频道"，机器人会在其中发送主动消息（例如 cron 作业输出、提醒和通知）。有两种设置方法：

### 使用斜杠命令

在机器人所在的任何 Discord 频道中输入 `/sethome`。该频道成为主频道。

### 手动配置

将这些添加到您的 `~/.hermes/.env` 中：

```bash
DISCORD_HOME_CHANNEL=123456789012345871466496
DISCORD_HOME_CHANNEL_NAME="#bot-updates"
```

将 ID 替换为实际的频道 ID（右键单击 → 在开发者模式下复制频道 ID）。

## 语音消息

Hermes Agent 支持 Discord 语音消息：

- **传入语音消息** 使用配置的 STT 提供商自动转录：本地 `faster-whisper`（无密钥）、Groq Whisper（`GROQ_API_KEY`）或 OpenAI Whisper（`VOICE_TOOLS_OPENAI_KEY`）。
- **文本转语音**：使用 `/voice tts` 让机器人在文本回复的同时发送语音响应。
- **Discord 语音频道**：Hermes 还可以加入语音频道，监听用户说话，并在频道中回话。

有关完整的设置和操作指南，请参阅：
- [语音模式](/docs/user-guide/features/voice-mode)
- [使用语音模式与 Hermes](/docs/guides/use-voice-mode-with-hermes)

## 故障排除

### 机器人在线但不响应消息

**原因**：Message Content Intent 被禁用。

**解决方法**：前往 [开发者门户](https://discord.com/developers/applications) → 您的应用 → Bot → Privileged Gateway Intents → 启用 **Message Content Intent** → 保存更改。重启网关。

### 启动时出现 "Disallowed Intents" 错误

**原因**：您的代码请求的意图在开发者门户中未启用。

**解决方法**：在 Bot 设置中启用所有三个特权网关意图（Presence、Server Members、Message Content），然后重启。

### 机器人无法在特定频道中看到消息

**原因**：机器人的角色没有查看该频道的权限。

**解决方法**：在 Discord 中，前往频道的设置 → 权限 → 添加机器人的角色，并启用 **View Channel** 和 **Read Message History**。

### 403 Forbidden 错误

**原因**：机器人缺少必需的权限。

**解决方法**：使用步骤 5 中的 URL 重新邀请机器人，并授予正确的权限，或在服务器设置 → 角色中手动调整机器人的角色权限。

### 机器人离线

**原因**：Hermes 网关未运行，或令牌不正确。

**解决方法**：检查 `hermes gateway` 是否运行。验证 `~/.hermes/.env` 文件中的 `DISCORD_BOT_TOKEN`。如果您最近重置了令牌，请更新它。

### "User not allowed" / 机器人忽略您

**原因**：您的用户 ID 不在 `DISCORD_ALLOWED_USERS` 中。

**解决方法**：将您的用户 ID 添加到 `~/.hermes/.env` 中的 `DISCORD_ALLOWED_USERS` 并重启网关。

### 同一频道中的人意外共享上下文

**原因**：`group_sessions_per_user` 被禁用，或者平台无法为此上下文中的消息提供用户 ID。

**解决方法**：在 `~/.hermes/config.yaml` 中设置以下内容并重启网关：

```yaml
group_sessions_per_user: true
```

如果您有意希望共享房间对话，请保持其关闭 — 只是要预期共享的对话记录历史和共享的中断行为。

## 安全性

:::warning
始终设置 `DISCORD_ALLOWED_USERS` 以限制谁可以与机器人交互。没有它，网关默认拒绝所有用户作为安全措施。只添加您信任的人的用户 ID — 授权用户拥有智能体能力的完全访问权限，包括工具使用和系统访问。
:::

有关保护 Hermes Agent 部署的更多信息，请参阅 [安全指南](../security.md)。