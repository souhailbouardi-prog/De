---
sidebar_position: 1
title: "Telegram"
description: "将 Hermes Agent 设置为 Telegram 机器人"
---

# Telegram 设置

Hermes Agent 作为功能齐全的对话机器人与 Telegram 集成。连接后，您可以从任何设备与您的智能体聊天，发送自动转录的语音备忘录，接收计划任务结果，并在群聊中使用智能体。该集成基于 [python-telegram-bot](https://python-telegram-bot.org/) 构建，支持文本、语音、图像和文件附件。

## 步骤 1：通过 BotFather 创建机器人

每个 Telegram 机器人都需要由 [@BotFather](https://t.me/BotFather)（Telegram 的官方机器人管理工具）颁发的 API 令牌。

1. 打开 Telegram 并搜索 **@BotFather**，或访问 [t.me/BotFather](https://t.me/BotFather)
2. 发送 `/newbot`
3. 选择一个**显示名称**（例如，"Hermes Agent"）— 这可以是任何内容
4. 选择一个**用户名** — 这必须是唯一的，并且以 `bot` 结尾（例如，`my_hermes_bot`）
5. BotFather 会回复您的**API 令牌**。它看起来像这样：

```
123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

:::warning
请保持您的机器人令牌保密。任何拥有此令牌的人都可以控制您的机器人。如果泄露，请立即通过 BotFather 中的 `/revoke` 命令撤销它。
:::

## 步骤 2：自定义您的机器人（可选）

这些 BotFather 命令可以改善用户体验。向 @BotFather 发送消息并使用：

| 命令 | 用途 |
|---------|---------|
| `/setdescription` | 用户开始聊天前显示的"此机器人能做什么？"文本 |
| `/setabouttext` | 机器人个人资料页面上的简短文本 |
| `/setuserpic` | 为您的机器人上传头像 |
| `/setcommands` | 定义命令菜单（聊天中的 `/` 按钮） |
| `/setprivacy` | 控制机器人是否看到所有群消息（见步骤 3） |

:::tip
对于 `/setcommands`，一个有用的起始设置：

```
help - 显示帮助信息
new - 开始新对话
sethome - 将此聊天设置为主频道
```
:::

## 步骤 3：隐私模式（对群组至关重要）

Telegram 机器人默认启用**隐私模式**。这是在群组中使用机器人时最常见的混淆来源。

**启用隐私模式**时，您的机器人只能看到：
- 以 `/` 命令开头的消息
- 直接回复机器人自己的消息
- 服务消息（成员加入/离开、置顶消息等）
- 机器人作为管理员的频道中的消息

**禁用隐私模式**时，机器人会接收群组中的每一条消息。

### 如何禁用隐私模式

1. 向 **@BotFather** 发送消息
2. 发送 `/mybots`
3. 选择您的机器人
4. 转到 **Bot Settings → Group Privacy → Turn off**

:::warning
**更改隐私设置后，您必须从任何群组中移除并重新添加机器人**。Telegram 在机器人加入群组时缓存隐私状态，直到机器人被移除并重新添加，它才会更新。
:::

:::tip
禁用隐私模式的替代方法：将机器人提升为**群组管理员**。管理员机器人始终接收所有消息，无论隐私设置如何，这避免了需要切换全局隐私模式。
:::

## 步骤 4：找到您的用户 ID

Hermes Agent 使用数字 Telegram 用户 ID 来控制访问。您的用户 ID **不是**您的用户名 — 它是一个像 `123456789` 这样的数字。

**方法 1（推荐）：** 向 [@userinfobot](https://t.me/userinfobot) 发送消息 — 它会立即回复您的用户 ID。

**方法 2：** 向 [@get_id_bot](https://t.me/get_id_bot) 发送消息 — 另一个可靠的选择。

保存这个数字；下一步您会需要它。

## 步骤 5：配置 Hermes

### 选项 A：交互式设置（推荐）

```bash
hermes gateway setup
```

在提示时选择 **Telegram**。向导会询问您的机器人令牌和允许的用户 ID，然后为您写入配置。

### 选项 B：手动配置

将以下内容添加到 `~/.hermes/.env`：

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_ALLOWED_USERS=123456789    # 多个用户用逗号分隔
```

### 启动网关

```bash
hermes gateway
```

机器人应该在几秒钟内上线。在 Telegram 上向它发送消息以验证。

## Webhook 模式

默认情况下，Hermes 使用**长轮询**连接到 Telegram — 网关向 Telegram 的服务器发出出站请求以获取新更新。这适用于本地和始终开启的部署。

对于**云部署**（Fly.io、Railway、Render 等），**webhook 模式**更具成本效益。这些平台可以在入站 HTTP 流量时自动唤醒暂停的机器，但不能在出站连接时唤醒。由于轮询是出站的，轮询机器人永远不能休眠。Webhook 模式翻转了方向 — Telegram 将更新推送到您机器人的 HTTPS URL，实现空闲时休眠的部署。

| | 轮询（默认） | Webhook |
|---|---|---|
| 方向 | 网关 → Telegram（出站） | Telegram → 网关（入站） |
| 最适合 | 本地、始终开启的服务器 | 具有自动唤醒功能的云平台 |
| 设置 | 无需额外配置 | 设置 `TELEGRAM_WEBHOOK_URL` |
| 空闲成本 | 机器必须保持运行 | 机器可以在消息之间休眠 |

### 配置

将以下内容添加到 `~/.hermes/.env`：

```bash
TELEGRAM_WEBHOOK_URL=https://my-app.fly.dev/telegram
# TELEGRAM_WEBHOOK_PORT=8443        # 可选，默认 8443
# TELEGRAM_WEBHOOK_SECRET=mysecret  # 可选，推荐
```

| 变量 | 是否必需 | 描述 |
|----------|----------|-------------|
| `TELEGRAM_WEBHOOK_URL` | 是 | Telegram 将发送更新的公共 HTTPS URL。URL 路径会自动提取（例如，从上面的示例中提取 `/telegram`）。 |
| `TELEGRAM_WEBHOOK_PORT` | 否 | webhook 服务器监听的本地端口（默认：`8443`）。 |
| `TELEGRAM_WEBHOOK_SECRET` | 否 | 用于验证更新确实来自 Telegram 的密钥令牌。**强烈推荐**用于生产部署。 |

当设置了 `TELEGRAM_WEBHOOK_URL` 时，网关会启动 HTTP webhook 服务器而不是轮询。当未设置时，使用轮询模式 — 与之前版本相比没有行为变化。

### 云部署示例（Fly.io）

1. 将环境变量添加到您的 Fly.io 应用秘密中：

```bash
fly secrets set TELEGRAM_WEBHOOK_URL=https://my-app.fly.dev/telegram
fly secrets set TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

2. Expose the webhook port in your `fly.toml`:

```toml
[[services]]
  internal_port = 8443
  protocol = "tcp"

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

3. Deploy:

```bash
fly deploy
```

网关日志应该显示：`[telegram] Connected to Telegram (webhook mode)`。

## Home Channel

使用任何 Telegram 聊天（私信或群组）中的 `/sethome` 命令来指定它作为**主频道**。计划任务（cron 作业）会将其结果传递到此频道。

您也可以在 `~/.hermes/.env` 中手动设置：

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="My Notes"
```

:::tip
群组聊天 ID 是负数（例如，`-1001234567890`）。您的个人私信聊天 ID 与您的用户 ID 相同。
:::

## Voice Messages

### 传入语音（语音转文字）

您在 Telegram 上发送的语音消息会自动由 Hermes 配置的 STT 提供商转录并作为文本注入到对话中。

- `local` 使用运行 Hermes 的机器上的 `faster-whisper` — 不需要 API 密钥
- `groq` 使用 Groq Whisper，需要 `GROQ_API_KEY`
- `openai` 使用 OpenAI Whisper，需要 `VOICE_TOOLS_OPENAI_KEY`

### 传出语音（文字转语音）

When the agent generates audio via TTS, it's delivered as native Telegram **voice bubbles** — the round, inline-playable kind.

- **OpenAI and ElevenLabs** produce Opus natively — no extra setup needed
- **Edge TTS** (the default free provider) outputs MP3 and requires **ffmpeg** to convert to Opus:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

Without ffmpeg, Edge TTS audio is sent as a regular audio file (still playable, but uses the rectangular player instead of a voice bubble).

在您的 `config.yaml` 中的 `tts.provider` 键下配置 TTS 提供商。

## Group Chat Usage

Hermes Agent 在 Telegram 群组聊天中工作，需要注意以下几点：

- **隐私模式**决定机器人可以看到哪些消息（请参阅[步骤 3](#step-3-privacy-mode-critical-for-groups)）
- `TELEGRAM_ALLOWED_USERS` 仍然适用 — 只有授权用户可以触发机器人，即使在群组中
- 您可以使用 `telegram.require_mention: true` 让机器人不响应普通的群组闲聊
- 使用 `telegram.require_mention: true` 时，群组消息在以下情况下会被接受：
  - 斜杠命令
  - 回复机器人的消息之一
  - `@botusername` 提及其
  - 匹配您在 `telegram.mention_patterns` 中配置的正则表达式唤醒词之一
- 如果 `telegram.require_mention` 未设置或为 false，Hermes 会保持之前开放的群组行为并响应它可以看到的一般群组消息

### 示例群组触发配置

将此添加到 `~/.hermes/config.yaml`：

```yaml
telegram:
  require_mention: true
  mention_patterns:
    - "^\\s*chompy\\b"
```

此示例允许所有通常的直接触发加上以 `chompy` 开头的消息，即使它们不使用 `@提及`。

### Notes on `mention_patterns`

- Patterns use Python regular expressions
- Matching is case-insensitive
- Patterns are checked against both text messages and media captions
- 无效的正则表达式模式会在网关日志中显示警告并被忽略，而不是导致机器人崩溃
- 如果您希望模式仅在消息开头匹配，请使用 `^` 锚定它

## Private Chat Topics (Bot API 9.4)

Telegram Bot API 9.4（2026年2月）引入了**私人聊天话题** — 机器人可以直接在1对1私信中创建论坛风格的话题线程，无需超级群组。这允许您在现有的与 Hermes 的私信中运行多个隔离的工作空间。

### 使用场景

如果您从事多个长期运行的项目，话题可以保持它们的上下文分离：

- **"网站"话题** — 处理您的生产网络服务
- **"研究"话题** — 文献综述和论文探索
- **"一般"话题** — 杂项任务和快速问题

每个话题都有自己独立的会话、历史和上下文 — 彼此完全隔离。

### 配置

在 `~/.hermes/config.yaml` 中的 `platforms.telegram.extra.dm_topics` 下添加话题：

```yaml
platforms:
  telegram:
    extra:
      dm_topics:
      - chat_id: 123456789        # 您的 Telegram 用户 ID
        topics:
        - name: General
          icon_color: 7322096
        - name: Website
          icon_color: 9367192
        - name: Research
          icon_color: 16766590
          skill: arxiv              # 在此话题中自动加载技能
```

**字段：**

| 字段 | 必需 | 描述 |
|-------|----------|-------------|
| `name` | Yes | Topic display name |
| `icon_color` | No | Telegram icon color code (integer) |
| `icon_custom_emoji_id` | No | Custom emoji ID for the topic icon |
| `skill` | No | Skill to auto-load on new sessions in this topic |
| `thread_id` | No | Auto-populated after topic creation — don't set manually |

### How it works

1. On gateway startup, Hermes calls `createForumTopic` for each topic that doesn't have a `thread_id` yet
2. The `thread_id` is saved back to `config.yaml` automatically — subsequent restarts skip the API call
3. Each topic maps to an isolated session key: `agent:main:telegram:dm:{chat_id}:{thread_id}`
4. Messages in each topic have their own conversation history, memory flush, and context window

### Skill binding

Topics with a `skill` field automatically load that skill when a new session starts in the topic. This works exactly like typing `/skill-name` at the start of a conversation — the skill content is injected into the first message, and subsequent messages see it in the conversation history.

For example, a topic with `skill: arxiv` will have the arxiv skill pre-loaded whenever its session resets (due to idle timeout, daily reset, or manual `/reset`).

:::tip
在配置之外创建的话题（例如，通过手动调用 Telegram API）在 `forum_topic_created` 服务消息到达时会自动发现。您也可以在网关运行时将话题添加到配置中 — 它们会在下一次缓存未命中时被获取。
:::

## Group Forum Topic Skill Binding

已启用**话题模式**的超级群组（也称为"论坛话题"）已经获得每个话题的会话隔离 — 每个 `thread_id` 映射到自己的对话。但您可能希望在特定群组话题中收到消息时**自动加载技能**，就像私信话题技能绑定一样工作。

### 使用场景

一个带有不同工作流论坛话题的团队超级群组：

- **工程**话题 → 自动加载 `software-development` 技能
- **研究**话题 → 自动加载 `arxiv` 技能
- **一般**话题 → 无技能，通用助手

### 配置

在 `~/.hermes/config.yaml` 中的 `platforms.telegram.extra.group_topics` 下添加话题绑定：

```yaml
platforms:
  telegram:
    extra:
      group_topics:
      - chat_id: -1001234567890       # 超级群组 ID
        topics:
        - name: Engineering
          thread_id: 5
          skill: software-development
        - name: Research
          thread_id: 12
          skill: arxiv
        - name: General
          thread_id: 1
          # 无技能 — 通用目的
```

**字段：**

| 字段 | 必需 | 描述 |
|-------|----------|-------------|
| `chat_id` | Yes | The supergroup's numeric ID (negative number starting with `-100`) |
| `name` | No | Human-readable label for the topic (informational only) |
| `thread_id` | Yes | Telegram forum topic ID — visible in `t.me/c/<group_id>/<thread_id>` links |
| `skill` | No | Skill to auto-load on new sessions in this topic |

### How it works

1. When a message arrives in a mapped group topic, Hermes looks up the `chat_id` and `thread_id` in `group_topics` config
2. If a matching entry has a `skill` field, that skill is auto-loaded for the session — identical to DM topic skill binding
3. Topics without a `skill` key get session isolation only (existing behavior, unchanged)
4. Unmapped `thread_id` values or `chat_id` values fall through silently — no error, no skill

### Differences from DM Topics

| | DM Topics | Group Topics |
|---|---|---|
| Config key | `extra.dm_topics` | `extra.group_topics` |
| Topic creation | Hermes creates topics via API if `thread_id` is missing | Admin creates topics in Telegram UI |
| `thread_id` | Auto-populated after creation | Must be set manually |
| `icon_color` / `icon_custom_emoji_id` | Supported | Not applicable (admin controls appearance) |
| Skill binding | ✓ | ✓ |
| Session isolation | ✓ | ✓ (already built-in for forum topics) |

:::tip
要找到话题的 `thread_id`，在 Telegram Web 或 Desktop 中打开话题并查看 URL：`https://t.me/c/1234567890/5` — 最后的数字（`5`）就是 `thread_id`。超级群组的 `chat_id` 是群组 ID 前面加 `-100`（例如，群组 `1234567890` 变成 `-1001234567890`）。
:::

## Recent Bot API Features

- **Bot API 9.4（2026年2月）：** 私人聊天话题 — 机器人可以通过 `createForumTopic` 在1对1私信中创建论坛话题。请参阅上面的[私人聊天话题](#private-chat-topics-bot-api-94)。
- **隐私政策：** Telegram 现在要求机器人具有隐私政策。通过 BotFather 使用 `/setprivacy_policy` 设置一个，否则 Telegram 可能会自动生成占位符。如果您的机器人是面向公众的，这尤其重要。
- **消息流式传输：** Bot API 9.x 添加了对长响应流式传输的支持，这可以改善冗长智能体回复的感知延迟。

## Interactive Model Picker

当您在 Telegram 聊天中发送不带参数的 `/model` 时，Hermes 会显示一个交互式内联键盘用于切换模型：

1. **提供商选择** — 显示每个可用提供商的按钮，带有模型数量（例如，"OpenAI (15)"，"✓ Anthropic (12)" 表示当前提供商）。
2. **模型选择** — 带 **Prev**/**Next** 导航的分页模型列表，一个 **Back** 按钮返回提供商，以及 **Cancel**。

当前模型和提供商显示在顶部。所有导航都通过就地编辑同一条消息来完成（不会弄乱聊天）。

:::tip
如果您知道确切的模型名称，直接输入 `/model <name>` 可以跳过选择器。您也可以输入 `/model <name> --global` 以跨会话持久化更改。
:::

## Webhook Mode

默认情况下，Telegram 适配器通过**长轮询**连接 — 网关向 Telegram 的服务器发出出站连接。这在任何地方都能工作，但会保持持久连接打开。

**Webhook 模式**是一种替代方案，Telegram 通过 HTTPS 将更新推送到您的服务器。这非常适合**无服务器和云部署**（Fly.io、Railway 等），因为入站 HTTP 可以唤醒暂停的机器。

### 配置

设置 `TELEGRAM_WEBHOOK_URL` 环境变量以启用 webhook 模式：

```bash
# 必需 — 您的公共 HTTPS 端点
TELEGRAM_WEBHOOK_URL=https://app.fly.dev/telegram

# 可选 — 本地监听端口（默认：8443）
TELEGRAM_WEBHOOK_PORT=8443

# 可选 — 用于更新验证的密钥令牌（如果未设置则自动生成）
TELEGRAM_WEBHOOK_SECRET=my-secret-token
```

或在 `~/.hermes/config.yaml` 中：

```yaml
telegram:
  webhook_mode: true
```

When `TELEGRAM_WEBHOOK_URL` is set, the gateway starts an HTTP server listening on `0.0.0.0:<port>` and registers the webhook URL with Telegram. The URL path is extracted from the webhook URL (defaults to `/telegram`).

:::warning
Telegram 需要 webhook 端点上的**有效 TLS 证书**。自签名证书将被拒绝。使用反向代理（nginx、Caddy）或提供 TLS 终止的平台（Fly.io、Railway、Cloudflare Tunnel）。
:::

## DNS-over-HTTPS Fallback IPs

在某些受限网络中，`api.telegram.org` 可能会解析到一个无法访问的 IP。Telegram 适配器包含一个**备用 IP**机制，可以透明地重试到备用 IP 的连接，同时保持正确的 TLS 主机名和 SNI。

### 工作原理

1. 如果设置了 `TELEGRAM_FALLBACK_IPS`，则直接使用这些 IP。
2. 否则，适配器自动通过 **Google DNS** 和 **Cloudflare DNS** 的 DNS-over-HTTPS (DoH) 查询，为 `api.telegram.org` 发现备用 IP。
3. DoH 返回的、与系统 DNS 结果不同的 IP 被用作备用。
4. 如果 DoH 也被阻止，则使用硬编码的种子 IP（`149.154.167.220`）作为最后手段。
5. 一旦备用 IP 成功，它就会变得"粘性" — 后续请求直接使用它而不先重试主路径。

### 配置

```bash
# 显式备用 IP（逗号分隔）
TELEGRAM_FALLBACK_IPS=149.154.167.220,149.154.167.221
```

或在 `~/.hermes/config.yaml` 中：

```yaml
platforms:
  telegram:
    extra:
      fallback_ips:
        - "149.154.167.220"
```

:::tip
您通常不需要手动配置这个。通过 DoH 的自动发现可以处理大多数受限网络场景。只有当 DoH 在您的网络上也被阻止时，才需要 `TELEGRAM_FALLBACK_IPS` 环境变量。
:::

## Proxy Support

如果您的网络需要 HTTP 代理来访问互联网（企业环境中常见），Telegram 适配器会自动读取标准代理环境变量并通过代理路由所有连接。

### 支持的变量

适配器按顺序检查这些环境变量，使用第一个被设置的：

1. `HTTPS_PROXY`
2. `HTTP_PROXY`
3. `ALL_PROXY`
4. `https_proxy` / `http_proxy` / `all_proxy`（小写变体）

### 配置

在启动网关之前在您的环境中设置代理：

```bash
export HTTPS_PROXY=http://proxy.example.com:8080
hermes gateway
```

或将其添加到 `~/.hermes/.env`：

```bash
HTTPS_PROXY=http://proxy.example.com:8080
```

代理适用于主传输和所有备用 IP 传输。不需要额外的 Hermes 配置 — 如果环境变量被设置，它会自动使用。

:::note
这涵盖了 Hermes 用于 Telegram 连接的自定义备用传输层。其他地方使用的标准 `httpx` 客户端本身已经原生尊重代理环境变量。
:::

## Message Reactions

机器人可以向消息添加 emoji 反应作为视觉处理反馈：

- 👀 当机器人开始处理您的消息时
- ✅ 当响应成功传递时
- 如果处理过程中发生错误

反应**默认禁用**。在 `config.yaml` 中启用它们：

```yaml
telegram:
  reactions: true
```

Or via environment variable:

```bash
TELEGRAM_REACTIONS=true
```

:::note
Unlike Discord (where reactions are additive), Telegram's Bot API replaces all bot reactions in a single call. The transition from 👀 to ✅/❌ happens atomically — you won't see both at once.
:::

:::tip
如果机器人没有在群组中添加反应的权限，反应调用会静默失败，消息处理会正常继续。
:::

## Troubleshooting

| 问题 | 解决方案 |
|---------|----------|
| 机器人完全不响应 | 验证 `TELEGRAM_BOT_TOKEN` 是否正确。检查 `hermes gateway` 日志中的错误。 |
| 机器人回复"未授权" | 您的用户 ID 不在 `TELEGRAM_ALLOWED_USERS` 中。使用 @userinfobot 仔细检查。 |
| 机器人忽略群组消息 | 隐私模式可能已开启。禁用它（第3步）或让机器人成为群组管理员。**更改隐私设置后记得移除并重新添加机器人。** |
| 语音消息未转录 | 验证 STT 是否可用：安装 `faster-whisper` 进行本地转录，或在 `~/.hermes/.env` 中设置 `GROQ_API_KEY` / `VOICE_TOOLS_OPENAI_KEY`。 |
| 语音回复是文件而非气泡 | 安装 `ffmpeg`（Edge TTS Opus 转换需要）。 |
| 机器人令牌被撤销/无效 | 通过 BotFather 中的 `/revoke` 然后 `/newbot` 或 `/token` 生成新令牌。更新您的 `.env` 文件。 |
| Webhook 未收到更新 | 验证 `TELEGRAM_WEBHOOK_URL` 是否公开可访问（用 `curl` 测试）。确保您的平台/反向代理将来自 URL 端口的入站 HTTPS 流量路由到 `TELEGRAM_WEBHOOK_PORT` 配置的本地监听端口（它们不需要是相同的数字）。确保 SSL/TLS 已激活 — Telegram 只发送到 HTTPS URL。检查防火墙规则。 |

## Exec Approval

当智能体尝试运行潜在危险命令时，它会在聊天中请求您的批准：

> ⚠️ 此命令可能有危险（递归删除）。回复 "yes" 以批准。

回复 "yes"/"y" 批准或 "no"/"n" 拒绝。

## Security

:::warning
始终设置 `TELEGRAM_ALLOWED_USERS` 以限制谁可以与您的机器人交互。没有它，网关默认拒绝所有用户作为安全措施。
:::

永远不要公开分享您的机器人令牌。如果泄露，立即通过 BotFather 的 `/revoke` 命令撤销它。

有关更多详细信息，请参阅[安全文档](/user-guide/security)。您也可以使用[私信配对](/user-guide/messaging#dm-pairing-alternative-to-allowlists) 来获得更动态的用户授权方法。