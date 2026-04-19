---
sidebar_position: 5
title: "WhatsApp"
description: "通过内置的 Baileys 桥接器将 Hermes Agent 设置为 WhatsApp 机器人"
---

# WhatsApp 设置

Hermes 通过基于 **Baileys** 的内置桥接器连接到 WhatsApp。这通过模拟 WhatsApp Web 会话工作 — **不是**通过官方的 WhatsApp Business API。不需要 Meta 开发者账户或企业验证。

:::warning 非官方 API — 封号风险
WhatsApp **不**正式支持 Business API 之外的第三方机器人。使用第三方桥接器有较小的账户限制风险。为了最小化风险：
- **为机器人使用专用电话号码**（不是您的个人号码）
- **不要发送批量/垃圾消息** — 保持对话式使用
- **不要自动向未先发消息的人发送外发消息**
:::

:::warning WhatsApp Web 协议更新
WhatsApp 会定期更新其 Web 协议，这可能会暂时破坏与第三方桥接器的兼容性。当这种情况发生时，Hermes 会更新桥接器依赖项。如果机器人在 WhatsApp 更新后停止工作，请拉取最新的 Hermes 版本并重新配对。
:::

## 两种模式

| 模式 | 工作方式 | 最适合 |
|------|-------------|----------|
| **独立的机器人号码**（推荐） | 为机器人专用一个电话号码。人们直接向该号码发送消息。 | 清晰的用户体验，多用户，较低的封号风险 |
| **个人自聊** | 使用您自己的 WhatsApp。您向自己发送消息以与智能体交谈。 | 快速设置，单用户，测试 |

---

## 前提条件

- **Node.js v18+** 和 **npm** — WhatsApp 桥接器作为 Node.js 进程运行
- **安装了 WhatsApp 的手机**（用于扫描二维码）

与较旧的浏览器驱动桥接器不同，当前基于 Baileys 的桥接器**不**需要本地 Chromium 或 Puppeteer 依赖项栈。

---

## 步骤 1：运行设置向导

```bash
hermes whatsapp
```

向导将：

1. 询问您想要哪种模式（**机器人**或**自聊**）
2. Install bridge dependencies if needed
3. Display a **QR code** in your terminal
4. Wait for you to scan it

**To scan the QR code:**

1. Open WhatsApp on your phone
2. Go to **Settings → Linked Devices**
3. Tap **Link a Device**
4. Point your camera at the terminal QR code

Once paired, the wizard confirms the connection and exits. Your session is saved automatically.

:::tip
If the QR code looks garbled, make sure your terminal is at least 60 columns wide and supports
Unicode. You can also try a different terminal emulator.
:::

---

## 步骤 2：获取第二个手机号码（机器人模式）

对于机器人模式，您需要一个尚未在 WhatsApp 上注册的手机号码。三个选项：

| 选项 | 费用 | 备注 |
|--------|------|-------|
| **Google Voice** | 免费 | 仅限美国。在 [voice.google.com](https://voice.google.com) 获取号码。通过 Google Voice 应用验证 WhatsApp。 |
| **预付费 SIM** | 5–15 美元一次性 | 任何运营商。激活、验证 WhatsApp，然后 SIM 可以放在抽屉里。号码必须保持活跃（每 90 天打一个电话）。 |
| **VoIP 服务** | 免费–5 美元/月 | TextNow、TextFree 或类似服务。部分 VoIP 号码会被 WhatsApp 屏蔽 — 如果第一个不行，多试几个。 |

获取号码后：

1. 在手机上安装 WhatsApp（或使用双卡 WhatsApp Business 应用）
2. 用 WhatsApp 注册新号码
3. 运行 `hermes whatsapp` 并扫描该 WhatsApp 账户的二维码

---

## 步骤 3：配置 Hermes

将以下内容添加到您的 `~/.hermes/.env` 文件：

```bash
# 必需
WHATSAPP_ENABLED=true
WHATSAPP_MODE=bot                          # "bot" 或 "self-chat"

# 访问控制 — 选择其中一个选项：
WHATSAPP_ALLOWED_USERS=15551234567         # 用逗号分隔的手机号码（带国家代码，不带 +）
# WHATSAPP_ALLOWED_USERS=*                 # 或使用 * 允许所有人
# WHATSAPP_ALLOW_ALL_USERS=true            # 或设置此标志（与 * 相同）
```

:::tip 允许所有人简写
设置 `WHATSAPP_ALLOWED_USERS=*` 允许**所有**发送者（相当于 `WHATSAPP_ALLOW_ALL_USERS=true`）。
这与 [Signal 群组允许列表](/docs/reference/environment-variables) 一致。
要改用配对流程，请移除这两个变量，依赖 [DM 配对系统](/docs/user-guide/security#dm-pairing-system)。
:::

`~/.hermes/config.yaml` 中的可选行为设置：

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `unauthorized_dm_behavior: pair` is the global default. Unknown DM senders get a pairing code.
- `whatsapp.unauthorized_dm_behavior: ignore` makes WhatsApp stay silent for unauthorized DMs, which is usually the better choice for a private number.

Then start the gateway:

```bash
hermes gateway              # Foreground
hermes gateway install      # Install as a user service
sudo hermes gateway install --system   # Linux only: boot-time system service
```

The gateway starts the WhatsApp bridge automatically using the saved session.

---

## 会话持久化

Baileys 桥接将会话保存在 `~/.hermes/platforms/whatsapp/session` 中。这意味着：

- **会话在重启后保留** — 您不需要每次都重新扫描二维码
- 会话数据包括加密密钥和设备凭据
- **不要共享或提交此会话目录** — 它授予对 WhatsApp 账户的完全访问权限

---

## 重新配对

如果会话断开（手机重置、WhatsApp 更新、手动取消链接），您会在网关日志中看到连接错误。修复方法：

```bash
hermes whatsapp
```

这会生成一个新的二维码。再次扫描后会话就重新建立了。网关会自动处理**临时**断开（网络闪烁、手机短暂离线），带有重连逻辑。

---

## 语音消息

Hermes 支持 WhatsApp 语音：

- **传入：** 语音消息（`.ogg` opus）使用配置的 STT 提供商自动转录：本地 `faster-whisper`、Groq Whisper（`GROQ_API_KEY`）或 OpenAI Whisper（`VOICE_TOOLS_OPENAI_KEY`）
- **传出：** TTS 响应作为 MP3 音频文件附件发送
- 智能体响应默认以 "⚕ **Hermes Agent**" 为前缀。您可以在 `config.yaml` 中自定义或禁用：

```yaml
# ~/.hermes/config.yaml
whatsapp:
  reply_prefix: ""                          # 空字符串禁用标题
  # reply_prefix: "🤖 *My Bot*\n──────\n"  # 自定义前缀（支持 \n 换行）
```

---

## 消息格式与发送

WhatsApp 支持**流式（渐进式）响应** — 机器人在 AI 生成文本时实时编辑其消息，就像 Discord 和 Telegram 一样。内部来说，WhatsApp 被归类为 TIER_MEDIUM 平台以发送能力。

### 分块

Long responses are automatically split into multiple messages at **4,096 characters** per chunk (WhatsApp's practical display limit). You don't need to configure anything — the gateway handles splitting and sends chunks sequentially.

### WhatsApp-Compatible Markdown

Standard Markdown in AI responses is automatically converted to WhatsApp's native formatting:

| Markdown | WhatsApp | Renders as |
|----------|----------|------------|
| `**bold**` | `*bold*` | **bold** |
| `~~strikethrough~~` | `~strikethrough~` | ~~strikethrough~~ |
| `# Heading` | `*Heading*` | Bold text (no native headings) |
| `[link text](url)` | `link text (url)` | Inline URL |

Code blocks and inline code are preserved as-is since WhatsApp supports triple-backtick formatting natively.

### Tool Progress

When the agent calls tools (web search, file operations, etc.), WhatsApp displays real-time progress indicators showing which tool is running. This is enabled by default — no configuration needed.

---

## Troubleshooting

| 问题 | 解决方案 |
|---------|----------|
| **二维码无法扫描** | 确保终端足够宽（60+ 列）。尝试不同的终端。确保从正确的 WhatsApp 账户扫描（机器人号码，不是个人）。 |
| **二维码过期** | 二维码每约 20 秒刷新一次。如果超时，重启 `hermes whatsapp`。 |
| **会话未保存** | 检查 `~/.hermes/platforms/whatsapp/session` 是否存在且可写。如果是容器化的，将其挂载为持久卷。 |
| **意外退出登录** | WhatsApp 长时间不活动后会取消链接设备。保持手机开机并连接到网络，然后如需要用 `hermes whatsapp` 重新配对。 |
| **桥接崩溃或重连循环** | 重启网关，更新 Hermes，如果会话被 WhatsApp 协议更改失效则重新配对。 |
| **WhatsApp 更新后机器人停止工作** | 更新 Hermes 以获取最新的桥接版本，然后重新配对。 |
| **macOS："Node.js 未安装"但终端中 node 可用** | launchd 服务不继承您的 shell PATH。运行 `hermes gateway install` 重新快照您当前的 PATH 到 plist，然后 `hermes gateway start`。详细信息请参阅[网关服务文档](./index.md#macos-launchd)。 |
| **未收到消息** | 验证 `WHATSAPP_ALLOWED_USERS` 包含发送者的号码（带国家代码，不带 `+` 或空格），或设置为 `*` 允许所有人。在 `.env` 中设置 `WHATSAPP_DEBUG=true` 并重启网关以在 `bridge.log` 中查看原始消息事件。 |
| **机器人用配对码回复陌生人** | 如果您想静默忽略未经授权的 DM，请在 `~/.hermes/config.yaml` 中设置 `whatsapp.unauthorized_dm_behavior: ignore`。 |

---

## 安全

:::warning
在上线之前**配置访问控制**。使用特定手机号码设置 `WHATSAPP_ALLOWED_USERS`（包括国家代码，不带 `+`），使用 `*` 允许所有人，或设置 `WHATSAPP_ALLOW_ALL_USERS=true`。没有任何这些设置时，网关**拒绝所有传入消息**作为安全措施。
:::

默认情况下，未经授权的 DM 仍会收到配对码回复。如果您希望私人 WhatsApp 号码对陌生人完全静默，请设置：

```yaml
whatsapp:
  unauthorized_dm_behavior: ignore
```

- `~/.hermes/platforms/whatsapp/session` 目录包含完整会话凭据 — 像密码一样保护它
- 设置文件权限：`chmod 700 ~/.hermes/platforms/whatsapp/session`
- 使用**专用手机号码**进行机器人操作以隔离个人账户的风险
- 如果怀疑被泄露，从 WhatsApp 取消链接设备 → 设置 → 已链接的设备
- 日志中的手机号码被部分隐藏，但请检查您的日志保留策略