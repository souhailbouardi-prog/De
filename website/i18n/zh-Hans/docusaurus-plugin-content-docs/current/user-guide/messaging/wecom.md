---
sidebar_position: 14
title: "WeCom (Enterprise WeChat)"
description: "通过AI Bot WebSocket网关将Hermes Agent连接到WeCom"
---

# WeCom (企业微信)

将Hermes连接到[WeCom](https://work.weixin.qq.com/)（企业微信），腾讯的企业消息平台。适配器使用WeCom的AI Bot WebSocket网关进行实时双向通信 — 不需要公共端点或webhook。

## 先决条件

- 企业微信组织账户
- 在企业微信管理后台创建的AI机器人
- 机器人凭证页面中的机器人ID和Secret
- Python包：`aiohttp`和`httpx`

## 设置

### 1. 创建AI机器人

1. 登录[企业微信管理后台](https://work.weixin.qq.com/wework_admin/frame)
2. 导航到**应用管理** → **创建应用** → **AI机器人**
3. 配置机器人名称和描述
4. 从凭证页面复制**机器人ID**和**Secret**

### 2. 配置Hermes

运行交互式设置：

```bash
hermes gateway setup
```

选择**WeCom**并输入您的机器人ID和Secret。

或在`~/.hermes/.env`中设置环境变量：

```bash
WECOM_BOT_ID=your-bot-id
WECOM_SECRET=your-secret

# 可选：限制访问
WECOM_ALLOWED_USERS=user_id_1,user_id_2

# 可选：定时任务/通知的主频道
WECOM_HOME_CHANNEL=chat_id
```

### 3. 启动网关

```bash
hermes gateway
```

## 功能

- **WebSocket传输** — 持久连接，不需要公共端点
- **DM和群聊消息** — 可配置的访问策略
- **按群组发件人允许列表** — 对每个群组中谁可以交互进行精细控制
- **媒体支持** — 图像、文件、语音、视频上传和下载
- **AES加密媒体** — 对入站附件自动解密
- **引用上下文** — 保留回复线程
- **Markdown渲染** — 富文本响应
- **回复模式流式传输** — 将响应与入站消息上下文相关联
- **自动重连** — 连接断开时指数退避

## 配置选项

在`config.yaml`中的`platforms.wecom.extra`下设置：

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `bot_id` | — | WeCom AI机器人ID（必需） |
| `secret` | — | WeCom AI机器人Secret（必需） |
| `websocket_url` | `wss://openws.work.weixin.qq.com` | WebSocket网关URL |
| `dm_policy` | `open` | DM访问：`open`、`allowlist`、`disabled`、`pairing` |
| `group_policy` | `open` | 群组访问：`open`、`allowlist`、`disabled` |
| `allow_from` | `[]` | 允许DM的用户ID（当dm_policy=allowlist时） |
| `group_allow_from` | `[]` | 允许的群组ID（当group_policy=allowlist时） |
| `groups` | `{}` | 按群组配置（见下文） |

## 访问策略

### DM策略

控制谁可以向机器人发送直接消息：

| 值 | 行为 |
|-------|----------|
| `open` | 任何人都可以DM机器人（默认） |
| `allowlist` | 只有`allow_from`中的用户ID可以DM |
| `disabled` | 所有DM都被忽略 |
| `pairing` | 配对模式（用于初始设置） |

```bash
WECOM_DM_POLICY=allowlist
```

### 群组策略

控制机器人在哪些群组中响应：

| 值 | 行为 |
|-------|----------|
| `open` | 机器人在所有群组中响应（默认） |
| `allowlist` | 机器人仅在`group_allow_from`中列出的群组ID中响应 |
| `disabled` | 所有群消息都被忽略 |

```bash
WECOM_GROUP_POLICY=allowlist
```

### 按群组发件人允许列表

对于精细控制，您可以限制特定群组中哪些用户可以与机器人交互。这在`config.yaml`中配置：

```yaml
platforms:
  wecom:
    enabled: true
    extra:
      bot_id: "your-bot-id"
      secret: "your-secret"
      group_policy: "allowlist"
      group_allow_from:
        - "group_id_1"
        - "group_id_2"
      groups:
        group_id_1:
          allow_from:
            - "user_alice"
            - "user_bob"
        group_id_2:
          allow_from:
            - "user_charlie"
        "*":
          allow_from:
            - "user_admin"
```

**工作原理：**

1. `group_policy`和`group_allow_from`控制决定一个群组是否被允许。
2. 如果群组通过顶层检查，`groups.<group_id>.allow_from`列表（如果存在）进一步限制该群组中哪些发件人可以与机器人交互。
3. 通配符`"*"`群组条目作为未明确列出的群组的默认值。
4. 允许列表条目支持`*`通配符以允许所有用户，且条目不区分大小写。
5. 条目可以选择使用`wecom:user:`或`wecom:group:`前缀格式 — 前缀会自动剥离。

如果没有为群组配置`allow_from`，则该群组中的所有用户都被允许（假设群组本身通过顶层策略检查）。

## 媒体支持

### 入站（接收）

适配器接收用户的媒体附件并将其本地缓存以供代理处理：

| 类型 | 处理方式 |
|------|-----------------|
| **图像** | 下载并本地缓存。支持基于URL和base64编码的图像。 |
| **文件** | 下载并缓存。文件名从原始消息中保留。 |
| **语音** | 如果可用，提取语音消息文本转录。 |
| **混合消息** | 解析企业微信混合类型消息（文本+图像）并提取所有组件。 |

**引用消息：** 来自引用（回复）消息的媒体也会被提取，因此代理了解用户正在回复的内容的上下文。

### AES加密媒体解密

企业微信使用AES-256-CBC加密一些入站媒体附件。适配器自动处理这一点：

- 当入站媒体项包含`aeskey`字段时，适配器下载加密字节并使用带有PKCS#7填充的AES-256-CBC解密它们。
- AES密钥是`aeskey`字段的base64解码值（必须正好32字节）。
- IV从密钥的前16字节派生。
- 这需要`cryptography` Python包（`pip install cryptography`）。

无需配置 — 当接收到加密媒体时，解密会透明进行。

### 出站（发送）

| 方法 | 发送内容 | 大小限制 |
|--------|--------------|------------|
| `send` | Markdown文本消息 | 4000字符 |
| `send_image` / `send_image_file` | 原生图像消息 | 10 MB |
| `send_document` | 文件附件 | 20 MB |
| `send_voice` | 语音消息（仅AMR格式用于原生语音） | 2 MB |
| `send_video` | 视频消息 | 10 MB |

**分块上传：** 文件通过三步协议（init → chunks → finish）以512 KB块上传。适配器自动处理这一点。

**自动降级：** 当媒体超过原生类型的大小限制但低于绝对20 MB文件限制时，它会自动作为通用文件附件发送：

- 图像 > 10 MB → 作为文件发送
- 视频 > 10 MB → 作为文件发送
- 语音 > 2 MB → 作为文件发送
- 非AMR音频 → 作为文件发送（企业微信仅支持AMR用于原生语音）

超过绝对20 MB限制的文件会被拒绝，并向聊天发送信息性消息。

## 回复模式流式响应

当机器人通过企业微信回调接收消息时，适配器会记住入站请求ID。如果在请求上下文仍然活跃时发送响应，适配器使用企业微信的回复模式（`aibot_respond_msg`）和流式传输将响应直接与入站消息相关联。这在企业微信客户端中提供更自然的对话体验。

如果入站请求上下文已过期或不可用，适配器会回退到通过`aibot_send_msg`发送主动消息。

回复模式也适用于媒体：上传的媒体可以作为对原始消息的回复发送。

## 连接和重连

适配器维护与企业微信网关`wss://openws.work.weixin.qq.com`的持久WebSocket连接。

### 连接生命周期

1. **连接：** 打开WebSocket连接并发送带有bot_id和secret的`aibot_subscribe`认证帧。
2. **心跳：** 每30秒发送应用级ping帧以保持连接活跃。
3. **监听：** 持续读取入站帧并调度消息回调。

### 重连行为

连接丢失时，适配器使用指数退避进行重连：

| 尝试 | 延迟 |
|---------|-------|
| 第1次重试 | 2秒 |
| 第2次重试 | 5秒 |
| 第3次重试 | 10秒 |
| 第4次重试 | 30秒 |
| 第5次+重试 | 60秒 |

每次成功重连后，退避计数器重置为零。所有待处理的请求future在断开连接时都会失败，因此调用者不会无限期挂起。

### 去重

入站消息使用消息ID进行去重，窗口为5分钟，最大缓存为1000个条目。这防止在重连或网络故障期间重复处理消息。

## 所有环境变量

| 变量 | 必需 | 默认值 | 描述 |
|----------|----------|---------|-------------|
| `WECOM_BOT_ID` | ✅ | — | WeCom AI机器人ID |
| `WECOM_SECRET` | ✅ | — | WeCom AI机器人Secret |
| `WECOM_ALLOWED_USERS` | — | _(empty)_ | 网关级允许列表的逗号分隔用户ID |
| `WECOM_HOME_CHANNEL` | — | — | 用于定时任务/通知输出的聊天ID |
| `WECOM_WEBSOCKET_URL` | — | `wss://openws.work.weixin.qq.com` | WebSocket网关URL |
| `WECOM_DM_POLICY` | — | `open` | DM访问策略 |
| `WECOM_GROUP_POLICY` | — | `open` | 群组访问策略 |

## 故障排除

| 问题 | 解决方案 |
|---------|-----|
| `WECOM_BOT_ID and WECOM_SECRET are required` | 设置两个环境变量或在设置向导中配置 |
| `WeCom startup failed: aiohttp not installed` | 安装aiohttp：`pip install aiohttp` |
| `WeCom startup failed: httpx not installed` | 安装httpx：`pip install httpx` |
| `invalid secret (errcode=40013)` | 验证secret与您的机器人凭证匹配 |
| `Timed out waiting for subscribe acknowledgement` | 检查到`openws.work.weixin.qq.com`的网络连接 |
| 机器人在群组中不响应 | 检查`group_policy`设置并确保群组ID在`group_allow_from`中 |
| 机器人忽略群组中的某些用户 | 检查`groups`配置部分中的按群组`allow_from`列表 |
| 媒体解密失败 | 安装`cryptography`：`pip install cryptography` |
| `cryptography is required for WeCom media decryption` | 入站媒体是AES加密的。安装：`pip install cryptography` |
| 语音消息作为文件发送 | 企业微信仅支持AMR格式用于原生语音。其他格式会自动降级为文件。 |
| `File too large`错误 | 企业微信对所有文件上传有20 MB的绝对限制。压缩或分割文件。 |
| 图像作为文件发送 | 图像> 10 MB超过原生图像限制，会自动降级为文件附件。 |
| `Timeout sending message to WeCom` | WebSocket可能已断开。检查日志中的重连消息。 |
| `WeCom websocket closed during authentication` | 网络问题或凭据不正确。验证bot_id和secret。 |