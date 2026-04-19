---
sidebar_position: 11
title: "飞书 / Lark"
description: "将 Hermes Agent 设置为飞书或 Lark 机器人"
---

# 飞书 / Lark 设置

Hermes Agent 作为功能齐全的机器人集成到飞书和 Lark。连接后，您可以在直接消息或群聊中与代理聊天，在主聊天中接收 cron 作业结果，并通过正常的网关流程发送文本、图像、音频和文件附件。

该集成支持两种连接模式：

- `websocket` — 推荐；Hermes 打开出站连接，您不需要公共 webhook 端点
- `webhook` — 当您希望飞书/Lark 通过 HTTP 将事件推送到您的网关时很有用

## Hermes 的行为

| 上下文 | 行为 |
|-------|------|
| 直接消息 | Hermes 响应每条消息。 |
| 群聊 | Hermes 仅在机器人在聊天中被 @ 提及时响应。 |
| 共享群聊 | 默认情况下，会话历史在共享聊天中按用户隔离。 |

这种共享聊天行为由 `config.yaml` 控制：

```yaml
group_sessions_per_user: true
```

只有当您明确希望每个聊天有一个共享对话时，才将其设置为 `false`。

## 步骤 1：创建飞书 / Lark 应用

### 推荐：扫码创建（一个命令）

```bash
hermes gateway setup
```

选择 **飞书 / Lark** 并用您的飞书或 Lark 移动应用扫描二维码。Hermes 将自动创建具有正确权限的机器人应用并保存凭证。

### 替代方法：手动设置

如果扫码创建不可用，向导会回退到手动输入：

1. 打开飞书或 Lark 开发者控制台：
   - 飞书：[https://open.feishu.cn/](https://open.feishu.cn/)
   - Lark：[https://open.larksuite.com/](https://open.larksuite.com/)
2. 创建一个新应用。
3. 在 **凭证与基础信息** 中，复制 **App ID** 和 **App Secret**。
4. 为应用启用 **机器人** 能力。
5. 运行 `hermes gateway setup`，选择 **飞书 / Lark**，并在提示时输入凭证。

:::warning
请保持 App Secret 私密。任何拥有它的人都可以冒充您的应用。
:::

## 步骤 2：选择连接模式

### 推荐：WebSocket 模式

当 Hermes 在您的笔记本电脑、工作站或私人服务器上运行时使用 WebSocket 模式。不需要公共 URL。官方 Lark SDK 打开并维护持久的出站 WebSocket 连接，具有自动重连功能。

```bash
FEISHU_CONNECTION_MODE=websocket
```

**要求：** 必须安装 `websockets` Python 包。SDK 内部处理连接生命周期、心跳和自动重连。

**工作原理：** 适配器在后台执行线程中运行 Lark SDK 的 WebSocket 客户端。入站事件（消息、反应、卡片操作）被调度到主 asyncio 循环。断开连接时，SDK 将尝试自动重连。

### 可选：Webhook 模式

仅当您已经在可访问的 HTTP 端点后面运行 Hermes 时使用 webhook 模式。

```bash
FEISHU_CONNECTION_MODE=webhook
```

在 webhook 模式下，Hermes 启动 HTTP 服务器（通过 `aiohttp`）并在以下位置提供飞书端点：

```text
/feishu/webhook
```

**要求：** 必须安装 `aiohttp` Python 包。

您可以自定义 webhook 服务器绑定地址和路径：

```bash
FEISHU_WEBHOOK_HOST=127.0.0.1   # 默认：127.0.0.1
FEISHU_WEBHOOK_PORT=8765         # 默认：8765
FEISHU_WEBHOOK_PATH=/feishu/webhook  # 默认：/feishu/webhook
```

当飞书发送 URL 验证挑战 (`type: url_verification`) 时，webhook 会自动响应，以便您可以在飞书开发者控制台中完成订阅设置。

## 步骤 3：配置 Hermes

### 选项 A：交互式设置

```bash
hermes gateway setup
```

选择 **飞书 / Lark** 并填写提示。

### 选项 B：手动配置

将以下内容添加到 `~/.hermes/.env`：

```bash
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=secret_xxx
FEISHU_DOMAIN=feishu
FEISHU_CONNECTION_MODE=websocket

# 可选但强烈推荐
FEISHU_ALLOWED_USERS=ou_xxx,ou_yyy
FEISHU_HOME_CHANNEL=oc_xxx
```

`FEISHU_DOMAIN` 接受：

- `feishu` 用于飞书中国
- `lark` 用于 Lark 国际

## 步骤 4：启动网关

```bash
hermes gateway
```

然后从飞书/Lark 向机器人发送消息，确认连接已激活。

## 主聊天

在飞书/Lark 聊天中使用 `/set-home` 将其标记为 cron 作业结果和跨平台通知的主频道。

您也可以预配置它：

```bash
FEISHU_HOME_CHANNEL=oc_xxx
```

## 安全

### 用户允许列表

对于生产使用，设置飞书开放 ID 的允许列表：

```bash
FEISHU_ALLOWED_USERS=ou_xxx,ou_yyy
```

如果您将允许列表留空，任何能够接触到机器人的人都可能使用它。在群聊中，在处理消息之前，会根据发送者的 open_id 检查允许列表。

### Webhook 加密密钥

在 webhook 模式下运行时，设置加密密钥以启用入站 webhook 负载的签名验证：

```bash
FEISHU_ENCRYPT_KEY=your-encrypt-key
```

此密钥在飞书应用配置的 **事件订阅** 部分找到。设置后，适配器使用签名算法验证每个 webhook 请求：

```
SHA256(timestamp + nonce + encrypt_key + body)
```

计算的哈希值使用定时安全比较与 `x-lark-signature` 头进行比较。具有无效或缺失签名的请求被拒绝，返回 HTTP 401。

:::tip
在 WebSocket 模式下，签名验证由 SDK 本身处理，因此 `FEISHU_ENCRYPT_KEY` 是可选的。在 webhook 模式下，它对于生产环境强烈推荐。
:::

### 验证令牌

检查 webhook 负载中 `token` 字段的额外认证层：

```bash
FEISHU_VERIFICATION_TOKEN=your-verification-token
```

此令牌也在飞书应用的 **事件订阅** 部分找到。设置后，每个入站 webhook 负载必须在其 `header` 对象中包含匹配的 `token`。不匹配的令牌被拒绝，返回 HTTP 401。

`FEISHU_ENCRYPT_KEY` 和 `FEISHU_VERIFICATION_TOKEN` 可以一起使用，以实现深度防御。

## 群消息策略

`FEISHU_GROUP_POLICY` 环境变量控制 Hermes 在群聊中的响应方式：

```bash
FEISHU_GROUP_POLICY=allowlist   # 默认
```

| 值 | 行为 |
|-----|------|
| `open` | Hermes 响应任何群中任何用户的 @ 提及。 |
| `allowlist` | Hermes 仅响应 `FEISHU_ALLOWED_USERS` 中列出的用户的 @ 提及。 |
| `disabled` | Hermes 完全忽略所有群消息。 |

在所有模式下，必须在处理消息之前在群中明确 @ 提及（或 @all）机器人。直接消息绕过此门控。

### 用于 @ 提及门控的机器人身份

为了在群中精确检测 @ 提及，适配器需要知道机器人的身份。可以明确提供：

```bash
FEISHU_BOT_OPEN_ID=ou_xxx
FEISHU_BOT_USER_ID=xxx
FEISHU_BOT_NAME=MyBot
```

如果这些都未设置，适配器将尝试在启动时通过应用信息 API 自动发现机器人名称。为此，需要授予 `admin:app.info:readonly` 或 `application:application:self_manage` 权限范围。

## 交互式卡片操作

当用户点击按钮或与机器人发送的交互式卡片交互时，适配器将这些路由为合成的 `/card` 命令事件：

- 按钮点击变为：`/card button {"key": "value", ...}`
- 卡片定义中的操作 `value` 负载作为 JSON 包含。
- 卡片操作通过 15 分钟窗口去重，以防止重复处理。

卡片操作事件以 `MessageType.COMMAND` 调度，因此它们通过正常的命令处理管道流动。

这也是 **命令批准** 的工作方式 — 当代理需要运行危险命令时，它会发送带有允许一次 / 会话 / 总是 / 拒绝按钮的交互式卡片。用户点击按钮，卡片操作回调将批准决定返回给代理。

### 必需的飞书应用配置

交互式卡片需要在飞书开发者控制台中进行**三个**配置步骤。缺少任何一个都会导致用户点击卡片按钮时出现错误 **200340**。

1. **订阅卡片操作事件：**
   在 **事件订阅** 中，将 `card.action.trigger` 添加到您的订阅事件中。

2. **启用交互式卡片能力：**
   在 **应用功能 > 机器人** 中，确保 **交互式卡片** 开关已启用。这告诉飞书您的应用可以接收卡片操作回调。

3. **配置卡片请求 URL（仅 webhook 模式）：**
   在 **应用功能 > 机器人 > 消息卡片请求 URL** 中，将 URL 设置为与事件 webhook 相同的端点（例如 `https://your-server:8765/feishu/webhook`）。在 WebSocket 模式下，这由 SDK 自动处理。

:::warning
没有所有三个步骤，飞书将成功*发送*交互式卡片（发送只需要 `im:message:send` 权限），但点击任何按钮将返回错误 200340。卡片看起来可以工作 — 错误只在用户与其交互时出现。
:::

## 文档评论智能回复

除了聊天，适配器还可以回答在**飞书/Lark 文档**上留下的 `@` 提及。当用户对文档发表评论（本地文本选择或整个文档评论）并 @ 提及机器人时，Hermes 会阅读文档加上周围的评论线程，并在线程上发布 LLM 回复。

由 `drive.notice.comment_add_v1` 事件提供支持，处理程序：

- 并行获取文档内容和评论时间线（整个文档线程 20 条消息，本地选择线程 12 条）。
- 使用 `feishu_doc` + `feishu_drive` 工具集运行代理，范围限定为单个评论会话。
- 以 4000 字符为单位分块回复，并将其作为线程回复发布。
- 为每个文档会话缓存 1 小时，上限为 50 条消息，以便同一文档上的后续评论保持上下文。

### 三级访问控制

文档评论回复是**仅显式授权** — 没有隐式允许所有模式。权限按以下顺序解析（第一个匹配获胜，每个字段）：

1. **精确文档** — 范围限定为特定文档令牌的规则。
2. **通配符** — 匹配文档模式的规则。
3. **顶级** — 工作区的默认规则。

每个规则有两种可用策略：

- **`allowlist`** — 用户/租户的静态列表。
- **`pairing`** — 静态列表 ∪ 运行时批准的存储。对于版主可以实时授予访问权限的部署很有用。

规则存储在 `~/.hermes/feishu_comment_rules.json`（配对授权在 `~/.hermes/feishu_comment_pairing.json`）中，具有 mtime 缓存热重载 — 编辑在下次评论事件时生效，无需重启网关。

命令行：

```bash
# 检查当前规则和配对状态
python -m gateway.platforms.feishu_comment_rules status

# 模拟特定文档 + 用户的访问检查
python -m gateway.platforms.feishu_comment_rules check <fileType:fileToken> <user_open_id>

# 在运行时管理配对授权
python -m gateway.platforms.feishu_comment_rules pairing list
python -m gateway.platforms.feishu_comment_rules pairing add <user_open_id>
python -m gateway.platforms.feishu_comment_rules pairing remove <user_open_id>
```

### 必需的飞书应用配置

除了已经授予的聊天/卡片权限外，添加云端硬盘评论事件：

- 在 **事件订阅** 中订阅 `drive.notice.comment_add_v1`。
- 授予 `docs:doc:readonly` 和 `drive:drive:readonly` 范围，以便处理程序可以读取文档内容。

## 媒体支持

### 入站（接收）

适配器接收并缓存来自用户的以下媒体类型：

| 类型 | 扩展名 | 处理方式 |
|------|--------|----------|
| **图像** | .jpg, .jpeg, .png, .gif, .webp, .bmp | 通过飞书 API 下载并本地缓存 |
| **音频** | .ogg, .mp3, .wav, .m4a, .aac, .flac, .opus, .webm | 下载并缓存；小文本文件自动提取 |
| **视频** | .mp4, .mov, .avi, .mkv, .webm, .m4v, .3gp | 下载并作为文档缓存 |
| **文件** | .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx 等 | 下载并作为文档缓存 |

来自富文本（post）消息的媒体，包括内联图像和文件附件，也会被提取和缓存。

对于小型基于文本的文档（.txt, .md），文件内容会自动注入到消息文本中，这样代理可以直接读取它，而不需要工具。

### 出站（发送）

| 方法 | 发送内容 |
|------|----------|
| `send` | 文本或富文本消息（基于 markdown 内容自动检测） |
| `send_image` / `send_image_file` | 上传图像到飞书，然后作为原生图像气泡发送（可选标题） |
| `send_document` | 上传文件到飞书 API，然后作为文件附件发送 |
| `send_voice` | 上传音频文件作为飞书文件附件 |
| `send_video` | 上传视频并作为原生媒体消息发送 |
| `send_animation` | GIF 降级为文件附件（飞书没有原生 GIF 气泡） |

文件上传路由基于扩展名自动：

- `.ogg`, `.opus` → 上传为 `opus` 音频
- `.mp4`, `.mov`, `.avi`, `.m4v` → 上传为 `mp4` 媒体
- `.pdf`, `.doc(x)`, `.xls(x)`, `.ppt(x)` → 上传为对应文档类型
- 其他所有 → 上传为通用流文件

## Markdown 渲染和 Post 回退

当出站文本包含 markdown 格式（标题、粗体、列表、代码块、链接等）时，适配器会自动将其作为带有嵌入 `md` 标签的飞书 **post** 消息发送，而不是纯文本。这在飞书客户端中启用丰富渲染。

如果飞书 API 拒绝 post 负载（例如，由于不支持的 markdown 构造），适配器会自动回退到发送为纯文本，去除 markdown。这种两阶段回退确保消息始终传递。

纯文本消息（未检测到 markdown）作为简单的 `text` 消息类型发送。

## ACK 表情反应

当适配器接收到入站消息时，它会立即添加一个 ✅（OK）表情反应，以表示消息已收到并正在处理。这在代理完成响应之前提供视觉反馈。

反应是持久的 — 它在响应发送后仍然保留在消息上，作为收据标记。

用户对机器人消息的反应也会被跟踪。如果用户在机器人发送的消息上添加或删除表情反应，它会被路由为合成文本事件（`reaction:added:EMOJI_TYPE` 或 `reaction:removed:EMOJI_TYPE`），以便代理可以响应反馈。

## 突发保护和批处理

适配器包含对快速消息突发的去抖动，以避免使代理不堪重负：

### 文本批处理

当用户快速连续发送多条文本消息时，它们在被调度之前会被合并为单个事件：

| 设置 | 环境变量 | 默认值 |
|------|----------|--------|
| 安静期 | `HERMES_FEISHU_TEXT_BATCH_DELAY_SECONDS` | 0.6s |
| 每批最大消息数 | `HERMES_FEISHU_TEXT_BATCH_MAX_MESSAGES` | 8 |
| 每批最大字符数 | `HERMES_FEISHU_TEXT_BATCH_MAX_CHARS` | 4000 |

### 媒体批处理

快速连续发送的多个媒体附件（例如，拖动多个图像）被合并为单个事件：

| 设置 | 环境变量 | 默认值 |
|------|----------|--------|
| 安静期 | `HERMES_FEISHU_MEDIA_BATCH_DELAY_SECONDS` | 0.8s |

### 每聊天序列化

同一聊天内的消息串行处理（一次一个），以保持对话连贯性。每个聊天都有自己的锁，因此不同聊天中的消息会并发处理。

## 速率限制（Webhook 模式）

在 webhook 模式下，适配器强制执行每 IP 速率限制以防止滥用：

- **窗口：** 60 秒滑动窗口
- **限制：** 每窗口每（app_id, path, IP）三元组 120 请求
- **跟踪上限：** 最多跟踪 4096 个唯一键（防止无界内存增长）

超过限制的请求收到 HTTP 429（请求过多）。

### Webhook 异常跟踪

适配器跟踪每个 IP 地址的连续错误响应。在 6 小时窗口内来自同一 IP 的 25 次连续错误后，会记录警告。这有助于检测配置错误的客户端或探测尝试。

额外的 webhook 保护：
- **正文大小限制：** 最大 1 MB
- **正文读取超时：** 30 秒
- **内容类型强制：** 仅接受 `application/json`

## WebSocket 调优

使用 `websocket` 模式时，您可以自定义重连和 ping 行为：

```yaml
platforms:
  feishu:
    extra:
      ws_reconnect_interval: 120   # 重连尝试之间的秒数（默认：120）
      ws_ping_interval: 30         # WebSocket ping 之间的秒数（可选；未设置则使用 SDK 默认值）
```

| 设置 | 配置键 | 默认值 | 描述 |
|------|--------|--------|------|
| 重连间隔 | `ws_reconnect_interval` | 120s | 重连尝试之间的等待时间 |
| Ping 间隔 | `ws_ping_interval` | _(SDK 默认)_ | WebSocket 保持活动 ping 的频率 |

## 每群组访问控制

除了全局 `FEISHU_GROUP_POLICY`，您可以使用 config.yaml 中的 `group_rules` 为每个群聊设置细粒度规则：

```yaml
platforms:
  feishu:
    extra:
      default_group_policy: "open"     # 不在 group_rules 中的群组的默认值
      admins:                          # 可以管理机器人设置的用户
        - "ou_admin_open_id"
      group_rules:
        "oc_group_chat_id_1":
          policy: "allowlist"          # open | allowlist | blacklist | admin_only | disabled
          allowlist:
            - "ou_user_open_id_1"
            - "ou_user_open_id_2"
        "oc_group_chat_id_2":
          policy: "admin_only"
        "oc_group_chat_id_3":
          policy: "blacklist"
          blacklist:
            - "ou_blocked_user"
```

| 策略 | 描述 |
|------|------|
| `open` | 群中的任何人都可以使用机器人 |
| `allowlist` | 只有群组 `allowlist` 中的用户可以使用机器人 |
| `blacklist` | 除群组 `blacklist` 中的用户外，所有人都可以使用机器人 |
| `admin_only` | 只有全局 `admins` 列表中的用户可以在该群组中使用机器人 |
| `disabled` | 机器人忽略该群组中的所有消息 |

未在 `group_rules` 中列出的群组回退到 `default_group_policy`（默认为 `FEISHU_GROUP_POLICY` 的值）。

## 去重

入站消息使用消息 ID 去重，TTL 为 24 小时。去重状态在重启之间持久化到 `~/.hermes/feishu_seen_message_ids.json`。

| 设置 | 环境变量 | 默认值 |
|------|----------|--------|
| 缓存大小 | `HERMES_FEISHU_DEDUP_CACHE_SIZE` | 2048 条目 |

## 所有环境变量

| 变量 | 必填 | 默认值 | 描述 |
|------|------|--------|------|
| `FEISHU_APP_ID` | ✅ | — | 飞书/Lark App ID |
| `FEISHU_APP_SECRET` | ✅ | — | 飞书/Lark App Secret |
| `FEISHU_DOMAIN` | — | `feishu` | `feishu`（中国）或 `lark`（国际） |
| `FEISHU_CONNECTION_MODE` | — | `websocket` | `websocket` 或 `webhook` |
| `FEISHU_ALLOWED_USERS` | — | _(空)_ | 用户允许列表的逗号分隔 open_id 列表 |
| `FEISHU_HOME_CHANNEL` | — | — | cron/通知输出的聊天 ID |
| `FEISHU_ENCRYPT_KEY` | — | _(空)_ | webhook 签名验证的加密密钥 |
| `FEISHU_VERIFICATION_TOKEN` | — | _(空)_ | webhook 负载认证的验证令牌 |
| `FEISHU_GROUP_POLICY` | — | `allowlist` | 群消息策略：`open`, `allowlist`, `disabled` |
| `FEISHU_BOT_OPEN_ID` | — | _(空)_ | 机器人的 open_id（用于 @ 提及检测） |
| `FEISHU_BOT_USER_ID` | — | _(空)_ | 机器人的 user_id（用于 @ 提及检测） |
| `FEISHU_BOT_NAME` | — | _(空)_ | 机器人的显示名称（用于 @ 提及检测） |
| `FEISHU_WEBHOOK_HOST` | — | `127.0.0.1` | Webhook 服务器绑定地址 |
| `FEISHU_WEBHOOK_PORT` | — | `8765` | Webhook 服务器端口 |
| `FEISHU_WEBHOOK_PATH` | — | `/feishu/webhook` | Webhook 端点路径 |
| `HERMES_FEISHU_DEDUP_CACHE_SIZE` | — | `2048` | 要跟踪的最大去重消息 ID 数 |
| `HERMES_FEISHU_TEXT_BATCH_DELAY_SECONDS` | — | `0.6` | 文本突发去抖动安静期 |
| `HERMES_FEISHU_TEXT_BATCH_MAX_MESSAGES` | — | `8` | 每个文本批次合并的最大消息数 |
| `HERMES_FEISHU_TEXT_BATCH_MAX_CHARS` | — | `4000` | 每个文本批次合并的最大字符数 |
| `HERMES_FEISHU_MEDIA_BATCH_DELAY_SECONDS` | — | `0.8` | 媒体突发去抖动安静期 |

WebSocket 和每群组 ACL 设置通过 `config.yaml` 中的 `platforms.feishu.extra` 配置（见上面的 [WebSocket 调优](#websocket-tuning) 和 [每群组访问控制](#per-group-access-control)）。

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| `lark-oapi not installed` | 安装 SDK：`pip install lark-oapi` |
| `websockets not installed; websocket mode unavailable` | 安装 websockets：`pip install websockets` |
| `aiohttp not installed; webhook mode unavailable` | 安装 aiohttp：`pip install aiohttp` |
| `FEISHU_APP_ID or FEISHU_APP_SECRET not set` | 设置两个环境变量或通过 `hermes gateway setup` 配置 |
| `Another local Hermes gateway is already using this Feishu app_id` | 同一时间只有一个 Hermes 实例可以使用相同的 app_id。先停止其他网关。 |
| 机器人在群中不响应 | 确保机器人被 @ 提及，检查 `FEISHU_GROUP_POLICY`，并验证发送者是否在 `FEISHU_ALLOWED_USERS` 中（如果策略是 `allowlist`） |
| `Webhook rejected: invalid verification token` | 确保 `FEISHU_VERIFICATION_TOKEN` 与飞书应用事件订阅配置中的令牌匹配 |
| `Webhook rejected: invalid signature` | 确保 `FEISHU_ENCRYPT_KEY` 与飞书应用配置中的加密密钥匹配 |
| Post 消息显示为纯文本 | 飞书 API 拒绝了 post 负载；这是正常的回退行为。查看日志了解详情。 |
| 机器人未收到图像/文件 | 向飞书应用授予 `im:message` 和 `im:resource` 权限范围 |
| 机器人身份未自动检测 | 授予 `admin:app.info:readonly` 范围，或手动设置 `FEISHU_BOT_OPEN_ID` / `FEISHU_BOT_NAME` |
| 点击批准按钮时错误 200340 | 在飞书开发者控制台中启用 **交互式卡片** 能力并配置 **卡片请求 URL**。见上面的 [必需的飞书应用配置](#required-feishu-app-configuration)。 |
| `Webhook rate limit exceeded` | 来自同一 IP 的请求超过 120 次/分钟。这通常是配置错误或循环。 |

## 工具集

飞书 / Lark 使用 `hermes-feishu` 平台预设，其中包含与 Telegram 和其他基于网关的消息平台相同的核心工具。