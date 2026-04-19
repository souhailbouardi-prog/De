---
sidebar_position: 5
title: "WhatsApp"
description: "通过内置的 Baileys 桥将 Hermes Agent 设置为 WhatsApp 机器人"
---

# WhatsApp 设置

Hermes 通过基于 **Baileys** 的内置桥连接到 WhatsApp。这通过模拟 WhatsApp Web 会话工作 — **不是**通过官方的 WhatsApp Business API。不需要 Meta 开发者账户或商业验证。

:::warning 非官方 API — 封禁风险
WhatsApp **不**正式支持 Business API 之外的第三方机器人。使用第三方桥存在账户限制的小风险。为最小化风险：
- **为机器人使用专用电话号码**（不是您的个人号码）
- **不要发送批量/垃圾消息** — 保持对话式使用
- **不要自动向未先联系的人发送出站消息**
:::

:::warning WhatsApp Web 协议更新
WhatsApp 定期更新其 Web 协议，这可能会暂时破坏与第三方桥的兼容性。当这种情况发生时，Hermes 将更新桥依赖项。如果机器人在 WhatsApp 更新后停止工作，请拉取最新的 Hermes 版本并重新配对。
:::

## 两种模式

| 模式 | 工作原理 | 最适合 |
|------|-------------|----------|
| **单独的机器人号码**（推荐） | 为机器人专用一个电话号码。人们直接向该号码发送消息。 | 干净的用户体验，多用户，较低的封禁风险 |
| **个人自聊** | 使用您自己的 WhatsApp。您向自己发送消息来与代理交谈。 | 快速设置，单用户，测试 |

---

## 先决条件

- **Node.js v18+** 和 **npm** — WhatsApp 桥作为 Node.js 进程运行
- **安装了 WhatsApp 的手机**（用于扫描二维码）

与旧的浏览器驱动桥不同，当前基于 Baileys 的桥**不需要**本地 Chromium 或 Puppeteer 依赖堆栈。

---

## 步骤 1：运行设置向导

```bash
hermes whatsapp
```

向导将：

1. 询问您想要哪种模式（**bot** 或 **self-chat**）
2. 如有需要安装桥依赖项
3. 在终端中显示**二维码**
4. 等待您扫描它

**扫描二维码：**

1. 在您的手机上打开 WhatsApp
2. 前往 **设置 → 链接的设备**
3. 点击 **链接设备**
4. 将相机对准终端二维码

配对后，向导确认连接并退出。您的会话会自动保存。

:::tip
如果二维码看起来混乱，请确保您的终端至少 60 列宽并支持 Unicode。您也可以尝试不同的终端模拟器。
:::

---

## 步骤 2：获取第二个电话号码（机器人模式）

对于机器人模式，您需要一个尚未在 WhatsApp 注册的电话号码。三个选项：

| 选项 | 成本 | 说明 |
|--------|------|-------|
| **Google Voice** | 免费 | 仅限美国。在 [voice.google.com](https://voice.google.com) 获取号码。通过 Google Voice 应用通过 SMS 验证 WhatsApp。 |
| **预付费 SIM** | 一次性 $5–15 | 任何运营商。激活，验证 WhatsApp，然后 SIM 可以放在抽屉里。号码必须保持活跃（每 90 天打一次电话）。 |
| **VoIP 服务** | 免费–$5/月 | TextNow、TextFree 或类似服务。一些 VoIP 号码被 WhatsApp 阻止 — 如果第一个不行，尝试几个。 |

获取号码后：

1. 在手机上安装 WhatsApp（或使用双 SIM 的 WhatsApp Business 应用）
2. 用新号码注册 WhatsApp
3. 运行 `hermes whatsapp` 并从该 WhatsApp 账户扫描二维码

---

## 步骤 3：配置 Hermes

将以下内容添加到您的 `~/.hermes/.env` 文件：

```bash
# 必需
WHATSAPP_ENABLED=true
WHATSAPP_MODE=bot                          # "bot" 或 "self-chat"

# 访问控制 — 选择以下选项之一：
WHATSAPP_ALLOWED_USERS=15551234567         # 逗号分隔的电话号码（带国家代码，无 +）
# WHATSAPP_ALLOWED_USERS=*                 # 或使用 * 允许所有人
# WHATSAPP_ALLOW_ALL_USERS=true            # 或设置此标志（与 * 效果相同）
```

:::tip 允许所有人的简写
设置 `WHATSAPP_ALLOWED_USERS=*` 允许**所有**发送者（相当于 `WHATSAPP_ALLOW_ALL_USERS=true`）。这与 [Signal 群组允许列表](/docs/reference/environment-variables) 一致。要改用配对流程，请移除这两个变量并依赖 [DM 配对系统](/docs/user-guide/security#dm-pairing-system)。
:::

`~/.hermes/config.yaml` 中的可选行为设置：

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `unauthorized_dm_behavior: pair` 是全局默认值。未知的 DM 发送者会获得配对代码。
- `whatsapp.unauthorized_dm_behavior: ignore` 使 WhatsApp 对未授权的 DM 保持沉默，这通常是私人号码的更好选择。

然后启动网关：

```bash
hermes gateway              # 前台
hermes gateway install      # 作为用户服务安装
sudo hermes gateway install --system   # 仅限 Linux：启动时系统服务
```

网关使用保存的会话自动启动 WhatsApp 桥。

---

## 会话持久性

Baileys 桥在 `~/.hermes/platforms/whatsapp/session` 下保存其会话。这意味着：

- **会话在重启后保持** — 您不需要每次都重新扫描二维码
- 会话数据包括加密密钥和设备凭证
- **不要共享或提交此会话目录** — 它授予对 WhatsApp 账户的完全访问权限

---

## 重新配对

如果会话中断（手机重置、WhatsApp 更新、手动取消链接），您会在网关日志中看到连接错误。要修复它：

```bash
hermes whatsapp
```

这会生成新的二维码。再次扫描它，会话将重新建立。网关会自动处理**临时**断开连接（网络波动、手机短暂离线）的重新连接逻辑。

---

## 语音消息

Hermes 支持 WhatsApp 上的语音：

- **传入：** 语音消息（`.ogg` opus）使用配置的 STT 提供商自动转录：本地 `faster-whisper`、Groq Whisper (`GROQ_API_KEY`) 或 OpenAI Whisper (`VOICE_TOOLS_OPENAI_KEY`)
- **传出：** TTS 响应作为 MP3 音频文件附件发送
- 代理响应默认前缀为 "⚕ **Hermes Agent**"。您可以在 `config.yaml` 中自定义或禁用：

```yaml
# ~/.hermes/config.yaml
whatsapp:
  reply_prefix: ""                          # 空字符串禁用标题
  # reply_prefix: "🤖 *My Bot*\n──────\n"  # 自定义前缀（支持 \n 换行）
```

---

## 消息格式化和传递

WhatsApp 支持**流式（渐进式）响应** — 机器人在 AI 生成文本时实时编辑其消息，就像 Discord 和 Telegram 一样。在内部，WhatsApp 被归类为具有中等传递能力的 TIER_MEDIUM 平台。

### 分块

长响应会在**4,096 个字符**（WhatsApp 的实际显示限制）处自动分割成多条消息。您不需要配置任何东西 — 网关处理分割并按顺序发送块。

### 兼容 WhatsApp 的 Markdown

AI 响应中的标准 Markdown 会自动转换为 WhatsApp 的原生格式：

| Markdown | WhatsApp | 渲染为 |
|----------|----------|------------|
| `**bold**` | `*bold*` | **粗体** |
| `~~strikethrough~~` | `~strikethrough~` | ~~删除线~~ |
| `# Heading` | `*Heading*` | 粗体文本（无原生标题） |
| `[link text](url)` | `link text (url)` | 内联 URL |

代码块和内联代码保持原样，因为 WhatsApp 原生支持三反引号格式化。

### 工具进度

当代理调用工具（网络搜索、文件操作等）时，WhatsApp 会显示实时进度指示器，显示正在运行的工具。这默认启用 — 无需配置。

---

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| **二维码无法扫描** | 确保终端足够宽（60+ 列）。尝试不同的终端。确保您从正确的 WhatsApp 账户（机器人号码，不是个人）扫描。 |
| **二维码过期** | 二维码每 ~20 秒刷新一次。如果超时，重新启动 `hermes whatsapp`。 |
| **会话不持久** | 检查 `~/.hermes/platforms/whatsapp/session` 是否存在且可写。如果容器化，将其挂载为持久卷。 |
| **意外登出** | WhatsApp 在长时间不活动后取消链接设备。保持手机开机并连接到网络，必要时使用 `hermes whatsapp` 重新配对。 |
| **桥崩溃或重连循环** | 重启网关，更新 Hermes，如果会话因 WhatsApp 协议更改而失效，则重新配对。 |
| **WhatsApp 更新后机器人停止工作** | 更新 Hermes 以获取最新的桥版本，然后重新配对。 |
| **macOS: "Node.js not installed" 但 node 在终端中工作** | launchd 服务不继承您的 shell PATH。运行 `hermes gateway install` 以将您当前的 PATH 重新快照到 plist 中，然后 `hermes gateway start`。有关详细信息，请参阅 [网关服务文档](./index.md#macos-launchd)。 |
| **消息未被接收** | 验证 `WHATSAPP_ALLOWED_USERS` 包含发送者的号码（带国家代码，无 `+` 或空格），或将其设置为 `*` 以允许所有人。在 `.env` 中设置 `WHATSAPP_DEBUG=true` 并重启网关，以在 `bridge.log` 中查看原始消息事件。 |
| **机器人用配对代码回复陌生人** | 如果您希望未授权的 DM 被静默忽略，请在 `~/.hermes/config.yaml` 中设置 `whatsapp.unauthorized_dm_behavior: ignore`。 |

---

## 安全性

:::warning
**在上线前配置访问控制**。设置 `WHATSAPP_ALLOWED_USERS` 包含特定电话号码（包括国家代码，不带 `+`），使用 `*` 允许所有人，或设置 `WHATSAPP_ALLOW_ALL_USERS=true`。没有这些设置，网关会**默认拒绝所有入站消息**作为安全措施。
:::

默认情况下，未授权的 DM 仍会收到配对代码回复。如果您希望私人 WhatsApp 号码对陌生人完全保持沉默，请设置：

```yaml
whatsapp:
  unauthorized_dm_behavior: ignore
```

- `~/.hermes/platforms/whatsapp/session` 目录包含完整的会话凭证 — 像保护密码一样保护它
- 设置文件权限：`chmod 700 ~/.hermes/platforms/whatsapp/session`
- **为机器人使用专用电话号码**，以将风险与您的个人账户隔离
- 如果您怀疑被入侵，请从 WhatsApp → 设置 → 链接的设备中取消链接设备
- 日志中的电话号码会部分脱敏，但请查看您的日志保留策略