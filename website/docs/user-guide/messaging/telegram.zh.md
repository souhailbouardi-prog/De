---
sidebar_position: 1
title: "Telegram"
description: "将 Hermes Agent 设置为 Telegram 机器人"
---

# Telegram 设置

Hermes Agent 作为功能齐全的对话机器人集成到 Telegram 中。连接后，您可以从任何设备与您的代理聊天，发送自动转录的语音备忘录，接收计划任务结果，并在群聊中使用代理。该集成基于 [python-telegram-bot](https://python-telegram-bot.org/)，支持文本、语音、图像和文件附件。

## 步骤 1：通过 BotFather 创建机器人

每个 Telegram 机器人都需要由 [@BotFather](https://t.me/BotFather)（Telegram 的官方机器人管理工具）颁发的 API 令牌。

1. 打开 Telegram 并搜索 **@BotFather**，或访问 [t.me/BotFather](https://t.me/BotFather)
2. 发送 `/newbot`
3. 选择一个 **显示名称**（例如 "Hermes Agent"）— 这可以是任何内容
4. 选择一个 **用户名** — 这必须是唯一的，并且以 `bot` 结尾（例如 `my_hermes_bot`）
5. BotFather 会回复您的 **API 令牌**。它看起来像这样：

```
123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

:::warning
请保持您的机器人令牌保密。任何拥有此令牌的人都可以控制您的机器人。如果泄露，请立即通过 BotFather 中的 `/revoke` 撤销它。
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
对于 `/setcommands`，一个有用的起始集：

```
help - 显示帮助信息
new - 开始新对话
sethome - 将此聊天设置为家庭频道
```
:::

## 步骤 3：隐私模式（群组的关键）

Telegram 机器人有一个 **隐私模式**，默认情况下是**启用**的。这是在群组中使用机器人时最常见的混淆源。

**启用隐私模式时**，您的机器人只能看到：
- 以 `/` 命令开头的消息
- 直接回复机器人自己的消息
- 服务消息（成员加入/离开，固定消息等）
- 机器人作为管理员的频道中的消息

**禁用隐私模式时**，机器人会收到群组中的每一条消息。

### 如何禁用隐私模式

1. 向 **@BotFather** 发送消息
2. 发送 `/mybots`
3. 选择您的机器人
4. 进入 **Bot Settings → Group Privacy → Turn off**

:::warning
**您必须在更改隐私设置后从任何群组中移除并重新添加机器人**。Telegram 在机器人加入群组时缓存隐私状态，直到机器人被移除并重新添加才会更新。
:::

:::tip
禁用隐私模式的替代方法：将机器人提升为 **群组管理员**。管理员机器人无论隐私设置如何始终接收所有消息，这避免了需要切换全局隐私模式。
:::

## 步骤 4：找到您的用户 ID

Hermes Agent 使用数字 Telegram 用户 ID 来控制访问。您的用户 ID **不是**您的用户名 — 它是一个类似 `123456789` 的数字。

**方法 1（推荐）：** 向 [@userinfobot](https://t.me/userinfobot) 发送消息 — 它会立即回复您的用户 ID。

**方法 2：** 向 [@get_id_bot](https://t.me/get_id_bot) 发送消息 — 另一个可靠的选择。

保存这个数字；下一步需要它。

## 步骤 5：配置 Hermes

### 选项 A：交互式设置（推荐）

```bash
hermes gateway setup
```

当提示时选择 **Telegram**。向导会询问您的机器人令牌和允许的用户 ID，然后为您写入配置。

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

默认情况下，Hermes 使用 **长轮询** 连接到 Telegram — 网关向 Telegram 的服务器发出出站请求以获取新更新。这对于本地和始终开启的部署非常有效。

对于 **云部署**（Fly.io、Railway、Render 等），**webhook 模式** 更具成本效益。这些平台可以在入站 HTTP 流量时自动唤醒挂起的机器，但不能在出站连接时唤醒。由于轮询是出站的，轮询机器人永远无法休眠。Webhook 模式翻转了方向 — Telegram 将更新推送到您机器人的 HTTPS URL，实现空闲时休眠的部署。

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
| `TELEGRAM_WEBHOOK_SECRET` | 否 | 用于验证更新确实来自 Telegram 的秘密令牌。**生产部署强烈推荐**。 |

当设置了 `TELEGRAM_WEBHOOK_URL` 时，网关会启动 HTTP webhook 服务器而不是轮询。未设置时，使用轮询模式 — 与之前版本的行为没有变化。

### 云部署示例（Fly.io）

1. 将环境变量添加到您的 Fly.io 应用程序密钥：

```bash
fly secrets set TELEGRAM_WEBHOOK_URL=https://my-app.fly.dev/telegram
fly secrets set TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

2. 在您的 `fly.toml` 中暴露 webhook 端口：

```toml
[[services]]
  internal_port = 8443
  protocol = "tcp"

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

3. 部署：

```bash
fly deploy
```

网关日志应该显示：`[telegram] Connected to Telegram (webhook mode)`。

## 代理支持

如果 Telegram 的 API 被阻止或您需要通过代理路由流量，请设置 Telegram 特定的代理 URL。这优先于通用的 `HTTPS_PROXY` / `HTTP_PROXY` 环境变量。

**选项 1：config.yaml（推荐）**

```yaml
telegram:
  proxy_url: "socks5://127.0.0.1:1080"
```

**选项 2：环境变量**

```bash
TELEGRAM_PROXY=socks5://127.0.0.1:1080
```

支持的方案：`http://`、`https://`、`socks5://`。

代理适用于主 Telegram 连接和回退 IP 传输。如果未设置 Telegram 特定的代理，网关会回退到 `HTTPS_PROXY` / `HTTP_PROXY` / `ALL_PROXY`（或 macOS 系统代理自动检测）。

## 家庭频道

在任何 Telegram 聊天（私信或群组）中使用 `/sethome` 命令将其指定为 **家庭频道**。计划任务（cron 作业）将结果传递到此频道。

您也可以在 `~/.hermes/.env` 中手动设置：

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="My Notes"
```

:::tip
群聊 ID 是负数（例如 `-1001234567890`）。您的个人私信聊天 ID 与您的用户 ID 相同。
:::

## 语音消息

### 传入语音（语音转文本）

您在 Telegram 上发送的语音消息会被 Hermes 配置的 STT 提供商自动转录并作为文本注入到对话中。

- `local` 使用运行 Hermes 的机器上的 `faster-whisper` — 不需要 API 密钥
- `groq` 使用 Groq Whisper，需要 `GROQ_API_KEY`
- `openai` 使用 OpenAI Whisper，需要 `VOICE_TOOLS_OPENAI_KEY`

### 传出语音（文本转语音）

当代理通过 TTS 生成音频时，它会作为原生 Telegram **语音气泡** 传递 — 圆形、内联可播放的那种。

- **OpenAI 和 ElevenLabs** 原生产生 Opus — 无需额外设置
- **Edge TTS**（默认免费提供商）输出 MP3，需要 **ffmpeg** 转换为 Opus：

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

没有 ffmpeg，Edge TTS 音频会作为常规音频文件发送（仍然可播放，但使用矩形播放器而不是语音气泡）。

在 `config.yaml` 中的 `tts.provider` 键下配置 TTS 提供商。

## 群聊使用

Hermes Agent 在 Telegram 群聊中工作，需要考虑以下几点：

- **隐私模式** 决定机器人可以看到什么消息（见 [步骤 3](#step-3-privacy-mode-critical-for-groups)）
- `TELEGRAM_ALLOWED_USERS` 仍然适用 — 只有授权用户可以触发机器人，即使在群组中
- 您可以使用 `telegram.require_mention: true` 防止机器人响应普通群聊
- 当 `telegram.require_mention: true` 时，当群组消息是以下情况时会被接受：
  - 斜杠命令
  - 回复机器人的消息之一
  - `@botusername` 提及
  - 与 `telegram.mention_patterns` 中配置的正则表达式唤醒词匹配
- 使用 `telegram.ignored_threads` 保持 Hermes 在特定 Telegram 论坛主题中保持沉默，即使群组在其他情况下允许自由响应或提及触发的回复
- 如果 `telegram.require_mention` 未设置或为 false，Hermes 保持之前的开放群组行为并响应它可以看到的正常群组消息

### 示例群组触发配置

将此添加到 `~/.hermes/config.yaml`：

```yaml
telegram:
  require_mention: true
  mention_patterns:
    - "^\s*chompy\b"
  ignored_threads:
    - 31
    - "42"
```

此示例允许所有通常的直接触发器以及以 `chompy` 开头的消息，即使它们不使用 `@mention`。
Telegram 主题 `31` 和 `42` 中的消息在提及和自由响应检查运行之前始终被忽略。

### 关于 `mention_patterns` 的说明

- 模式使用 Python 正则表达式
- 匹配不区分大小写
- 模式会针对文本消息和媒体标题进行检查
- 无效的正则表达式模式会被忽略并在网关日志中发出警告，而不是使机器人崩溃
- 如果您希望模式仅在消息开头匹配，请使用 `^` 锚定

## 私人聊天主题（Bot API 9.4）

Telegram Bot API 9.4（2026 年 2 月）引入了 **私人聊天主题** — 机器人可以直接在 1 对 1 私信聊天中创建论坛风格的主题线程，无需超级群组。这让您可以在与 Hermes 的现有私信中运行多个隔离的工作区。

### 用例

如果您处理多个长期项目，主题可以保持它们的上下文分离：

- **主题 "Website"** — 处理您的生产网络服务
- **主题 "Research"** — 文献综述和论文探索
- **主题 "General"** — 杂项任务和快速问题

每个主题都有自己的对话会话、历史记录和上下文 — 与其他主题完全隔离。

### 配置

在 `~/.hermes/config.yaml` 中的 `platforms.telegram.extra.dm_topics` 下添加主题：

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
          skill: arxiv              # 在此主题中自动加载技能
```

**字段：**

| 字段 | 是否必需 | 描述 |
|-------|----------|-------------|
| `name` | 是 | 主题显示名称 |
| `icon_color` | 否 | Telegram 图标颜色代码（整数） |
| `icon_custom_emoji_id` | 否 | 主题图标的自定义表情符号 ID |
| `skill` | 否 | 在此主题的新会话中自动加载的技能 |
| `thread_id` | 否 | 主题创建后自动填充 — 不要手动设置 |

### 工作原理

1. 网关启动时，Hermes 为每个尚未有 `thread_id` 的主题调用 `createForumTopic`
2. `thread_id` 会自动保存回 `config.yaml` — 后续重启会跳过 API 调用
3. 每个主题映射到一个隔离的会话键：`agent:main:telegram:dm:{chat_id}:{thread_id}`
4. 每个主题中的消息有自己的对话历史、内存刷新和上下文窗口

### 技能绑定

带有 `skill` 字段的主题会在主题中启动新会话时自动加载该技能。这与在对话开始时输入 `/skill-name` 完全相同 — 技能内容被注入到第一条消息中，后续消息会在对话历史中看到它。

例如，带有 `skill: arxiv` 的主题会在其会话重置时（由于空闲超时、每日重置或手动 `/reset`）预加载 arxiv 技能。

:::tip
在配置外创建的主题（例如，通过手动调用 Telegram API）会在 `forum_topic_created` 服务消息到达时自动发现。您也可以在网关运行时将主题添加到配置中 — 它们会在下次缓存未命中时被拾取。
:::

## 群组论坛主题技能绑定

启用了 **主题模式** 的超级群组（也称为"论坛主题"）已经获得了每个主题的会话隔离 — 每个 `thread_id` 映射到自己的对话。但您可能希望在特定群组主题中收到消息时 **自动加载技能**，就像私信主题技能绑定一样。

### 用例

一个带有不同工作流论坛主题的团队超级群组：

- **Engineering** 主题 → 自动加载 `software-development` 技能
- **Research** 主题 → 自动加载 `arxiv` 技能
- **General** 主题 → 无技能，通用助手

### 配置

在 `~/.hermes/config.yaml` 中的 `platforms.telegram.extra.group_topics` 下添加主题绑定：

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

| 字段 | 是否必需 | 描述 |
|-------|----------|-------------|
| `chat_id` | 是 | 超级群组的数字 ID（以 `-100` 开头的负数） |
| `name` | 否 | 主题的人类可读标签（仅信息性） |
| `thread_id` | 是 | Telegram 论坛主题 ID — 在 `t.me/c/<group_id>/<thread_id>` 链接中可见 |
| `skill` | 否 | 在此主题的新会话中自动加载的技能 |

### 工作原理

1. 当消息到达映射的群组主题时，Hermes 在 `group_topics` 配置中查找 `chat_id` 和 `thread_id`
2. 如果匹配的条目有 `skill` 字段，该技能会为会话自动加载 — 与私信主题技能绑定相同
3. 没有 `skill` 键的主题只获得会话隔离（现有行为，未更改）
4. 未映射的 `thread_id` 值或 `chat_id` 值会静默通过 — 无错误，无技能

### 与私信主题的区别

| | 私信主题 | 群组主题 |
|---|---|---|
| 配置键 | `extra.dm_topics` | `extra.group_topics` |
| 主题创建 | Hermes 通过 API 创建主题（如果缺少 `thread_id`） | 管理员在 Telegram UI 中创建主题 |
| `thread_id` | 创建后自动填充 | 必须手动设置 |
| `icon_color` / `icon_custom_emoji_id` | 支持 | 不适用（管理员控制外观） |
| 技能绑定 | ✓ | ✓ |
| 会话隔离 | ✓ | ✓（论坛主题已内置） |

:::tip
要找到主题的 `thread_id`，在 Telegram Web 或桌面版中打开主题并查看 URL：`https://t.me/c/1234567890/5` — 最后一个数字（`5`）是 `thread_id`。超级群组的 `chat_id` 是群组 ID 前缀加 `-100`（例如，群组 `1234567890` 变为 `-1001234567890`）。
:::

## 最近的 Bot API 功能

- **Bot API 9.4（2026 年 2 月）：** 私人聊天主题 — 机器人可以通过 `createForumTopic` 在 1 对 1 私信聊天中创建论坛主题。请参见上面的 [私人聊天主题](#private-chat-topics-bot-api-94)。
- **隐私政策：** Telegram 现在要求机器人有隐私政策。通过 BotFather 的 `/setprivacy_policy` 设置一个，否则 Telegram 可能会自动生成一个占位符。如果您的机器人面向公众，这一点尤为重要。
- **消息流式传输：** Bot API 9.x 添加了对长响应流式传输的支持，这可以改善冗长代理回复的感知延迟。

## 交互式模型选择器

当您在 Telegram 聊天中发送 `/model` 无参数时，Hermes 会显示一个交互式内联键盘用于切换模型：

1. **提供商选择** — 按钮显示每个可用提供商及其模型数量（例如，"OpenAI (15)"，当前提供商为 "✓ Anthropic (12)"）。
2. **模型选择** — 分页模型列表，带有 **上一页**/**下一页** 导航，**返回** 按钮返回提供商，以及 **取消**。

当前模型和提供商显示在顶部。所有导航通过就地编辑同一消息进行（无聊天混乱）。

:::tip
如果您知道确切的模型名称，直接输入 `/model <name>` 以跳过选择器。您也可以输入 `/model <name> --global` 以跨会话持久更改。
:::

## Webhook 模式

默认情况下，Telegram 适配器通过 **长轮询** 连接 — 网关向 Telegram 的服务器发出出站连接。这在任何地方都有效，但会保持一个持久连接打开。

**Webhook 模式** 是一种替代方案，其中 Telegram 通过 HTTPS 将更新推送到您的服务器。这是 **无服务器和云部署**（Fly.io、Railway 等）的理想选择，其中入站 HTTP 可以唤醒挂起的机器。

### 配置

设置 `TELEGRAM_WEBHOOK_URL` 环境变量以启用 webhook 模式：

```bash
# 必需 — 您的公共 HTTPS 端点
TELEGRAM_WEBHOOK_URL=https://app.fly.dev/telegram

# 可选 — 本地监听端口（默认：8443）
TELEGRAM_WEBHOOK_PORT=8443

# 可选 — 用于更新验证的秘密令牌（未设置则自动生成）
TELEGRAM_WEBHOOK_SECRET=my-secret-token
```

或在 `~/.hermes/config.yaml` 中：

```yaml
telegram:
  webhook_mode: true
```

当设置了 `TELEGRAM_WEBHOOK_URL` 时，网关会启动一个 HTTP 服务器，监听 `0.0.0.0:<port>` 并向 Telegram 注册 webhook URL。URL 路径从 webhook URL 中提取（默认为 `/telegram`）。

:::warning
Telegram 要求 webhook 端点上有 **有效的 TLS 证书**。自签名证书将被拒绝。使用反向代理（nginx、Caddy）或提供 TLS 终止的平台（Fly.io、Railway、Cloudflare Tunnel）。
:::

## DNS-over-HTTPS 回退 IP

在一些受限网络中，`api.telegram.org` 可能解析到不可达的 IP。Telegram 适配器包含一个 **回退 IP** 机制，在保留正确的 TLS 主机名和 SNI 的同时，透明地对替代 IP 重试连接。

### 工作原理

1. 如果设置了 `TELEGRAM_FALLBACK_IPS`，直接使用这些 IP。
2. 否则，适配器通过 DNS-over-HTTPS (DoH) 自动查询 **Google DNS** 和 **Cloudflare DNS**，以发现 `api.telegram.org` 的替代 IP。
3. DoH 返回的与系统 DNS 结果不同的 IP 用作回退。
4. 如果 DoH 也被阻止，使用硬编码的种子 IP (`149.154.167.220`) 作为最后手段。
5. 一旦回退 IP 成功，它就会"粘性" — 后续请求直接使用它，而不首先重试主路径。

### 配置

```bash
# 显式回退 IP（逗号分隔）
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
您通常不需要手动配置此功能。通过 DoH 的自动发现可以处理大多数受限网络场景。`TELEGRAM_FALLBACK_IPS` 环境变量仅在您的网络也阻止 DoH 时才需要。
:::

## 代理支持

如果您的网络需要 HTTP 代理才能访问互联网（在企业环境中很常见），Telegram 适配器会自动读取标准代理环境变量并通过代理路由所有连接。

### 支持的变量

适配器按顺序检查这些环境变量，使用第一个设置的变量：

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

或添加到 `~/.hermes/.env`：

```bash
HTTPS_PROXY=http://proxy.example.com:8080
```

代理适用于主传输和所有回退 IP 传输。不需要额外的 Hermes 配置 — 如果设置了环境变量，它会被自动使用。

:::note
这涵盖了 Hermes 用于 Telegram 连接的自定义回退传输层。其他地方使用的标准 `httpx` 客户端已经原生尊重代理环境变量。
:::

## 消息反应

机器人可以向消息添加 emoji 反应作为视觉处理反馈：

- 👀 当机器人开始处理您的消息时
- ✅ 当响应成功传递时
- ❌ 如果处理过程中发生错误

反应默认**禁用**。在 `config.yaml` 中启用它们：

```yaml
telegram:
  reactions: true
```

或通过环境变量：

```bash
TELEGRAM_REACTIONS=true
```

:::note
与 Discord（反应是累加的）不同，Telegram 的 Bot API 在单个调用中替换所有机器人反应。从 👀 到 ✅/❌ 的过渡是原子的 — 您不会同时看到两者。
:::

:::tip
如果机器人在群组中没有添加反应的权限，反应调用会静默失败，消息处理继续正常进行。
:::

## 每个频道的提示

为特定 Telegram 群组或论坛主题分配临时系统提示。提示在每一轮运行时注入 — 永远不会持久化到 transcript 历史 — 因此更改立即生效。

```yaml
telegram:
  channel_prompts:
    "-1001234567890": |
      你是一个研究助手。专注于学术来源、
      引用和简洁的综合。
    "42":  |
      此主题用于创意写作反馈。保持温暖和
      建设性。
```

键是聊天 ID（群组/超级群组）或论坛主题 ID。对于论坛群组，主题级提示覆盖群组级提示：

- 群组 `-1001234567890` 内主题 `42` 中的消息 → 使用主题 `42` 的提示
- 主题 `99`（无明确条目）中的消息 → 回退到群组 `-1001234567890` 的提示
- 无条目的群组中的消息 → 不应用频道提示

数字 YAML 键会自动规范化为字符串。

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| 机器人完全没有响应 | 验证 `TELEGRAM_BOT_TOKEN` 是否正确。检查 `hermes gateway` 日志中的错误。 |
| 机器人回复 "unauthorized" | 您的用户 ID 不在 `TELEGRAM_ALLOWED_USERS` 中。使用 @userinfobot 仔细检查。 |
| 机器人忽略群组消息 | 隐私模式可能开启。禁用它（步骤 3）或使机器人成为群组管理员。**记住在更改隐私后移除并重新添加机器人**。 |
| 语音消息未转录 | 验证 STT 可用：安装 `faster-whisper` 用于本地转录，或在 `~/.hermes/.env` 中设置 `GROQ_API_KEY` / `VOICE_TOOLS_OPENAI_KEY`。 |
| 语音回复是文件，不是气泡 | 安装 `ffmpeg`（Edge TTS Opus 转换所需）。 |
| 机器人令牌被撤销/无效 | 通过 BotFather 中的 `/revoke` 然后 `/newbot` 或 `/token` 生成新令牌。更新您的 `.env` 文件。 |
| Webhook 未接收更新 | 验证 `TELEGRAM_WEBHOOK_URL` 可公开访问（使用 `curl` 测试）。确保您的平台/反向代理将来自 URL 端口的入站 HTTPS 流量路由到 `TELEGRAM_WEBHOOK_PORT` 配置的本地监听端口（它们不需要是相同的数字）。确保 SSL/TLS 处于活动状态 — Telegram 仅发送到 HTTPS URL。检查防火墙规则。 |

## 执行批准

当代理尝试运行潜在危险的命令时，它会在聊天中请求您的批准：

> ⚠️ 此命令潜在危险（递归删除）。回复 "yes" 以批准。

回复 "yes"/"y" 批准或 "no"/"n" 拒绝。

## 安全

:::warning
始终设置 `TELEGRAM_ALLOWED_USERS` 来限制谁可以与您的机器人交互。没有它，网关默认拒绝所有用户作为安全措施。
:::

永远不要公开分享您的机器人令牌。如果被泄露，请立即通过 BotFather 的 `/revoke` 命令撤销它。

有关更多详细信息，请参阅 [安全文档](/user-guide/security)。您也可以使用 [DM 配对](/user-guide/messaging#dm-pairing-alternative-to-allowlists) 作为用户授权的更动态方法。