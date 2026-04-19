---
sidebar_position: 15
title: "Weixin (WeChat)"
description: "通过iLink Bot API将Hermes Agent连接到个人微信账户"
---

# Weixin (微信)

将Hermes连接到[WeChat](https://weixin.qq.com/)（微信），腾讯的个人消息平台。适配器使用腾讯的**iLink Bot API**用于个人微信账户 — 这与WeCom（企业微信）不同。消息通过长轮询传递，因此不需要公共端点或webhook。

:::info
此适配器适用于**个人微信账户**（微信）。如果您需要企业/公司微信，请参阅[WeCom适配器](./wecom.md)。
:::

## 先决条件

- 个人微信账户
- Python包：`aiohttp`和`cryptography`
- `qrcode`包是可选的（用于设置期间的终端QR渲染）

安装所需的依赖项：

```bash
pip install aiohttp cryptography
# 可选：用于终端QR码显示
pip install qrcode
```

## 设置

### 1. 运行设置向导

连接微信账户的最简单方法是通过交互式设置：

```bash
hermes gateway setup
```

提示时选择**Weixin**。向导将：

1. 从iLink Bot API请求QR码
2. 在终端中显示QR码（或提供URL）
3. 等待您用微信移动应用扫描QR码
4. 提示您在手机上确认登录
5. 自动将账户凭据保存到`~/.hermes/weixin/accounts/`

确认后，您会看到类似以下消息：

```
微信连接成功，account_id=your-account-id
```

向导存储`account_id`、`token`和`base_url`，因此您不需要手动配置它们。

### 2. 配置环境变量

初始QR登录后，至少在`~/.hermes/.env`中设置账户ID：

```bash
WEIXIN_ACCOUNT_ID=your-account-id

# 可选：覆盖令牌（通常从QR登录自动保存）
# WEIXIN_TOKEN=your-bot-token

# 可选：限制访问
WEIXIN_DM_POLICY=open
WEIXIN_ALLOWED_USERS=user_id_1,user_id_2

# 可选：恢复传统多行分割行为
# WEIXIN_SPLIT_MULTILINE_MESSAGES=true

# 可选：定时任务/通知的主频道
WEIXIN_HOME_CHANNEL=chat_id
WEIXIN_HOME_CHANNEL_NAME=Home
```

### 3. 启动网关

```bash
hermes gateway
```

适配器将恢复保存的凭据，连接到iLink API，并开始长轮询消息。

## 功能

- **长轮询传输** — 不需要公共端点、webhook或WebSocket
- **QR码登录** — 通过`hermes gateway setup`扫描连接设置
- **DM和群聊消息** — 可配置的访问策略
- **媒体支持** — 图像、视频、文件和语音消息
- **AES-128-ECB加密CDN** — 所有媒体传输的自动加密/解密
- **上下文令牌持久性** — 跨重启的磁盘支持回复连续性
- **Markdown格式** — 标题、表格和代码块为微信可读性重新格式化
- **智能消息分块** — 消息在限制下保持为单个气泡；只有超大有效载荷在逻辑边界处分割
- **输入指示器** — 在代理处理时在微信客户端中显示"正在输入..."状态
- **SSRF保护** — 下载前验证出站媒体URL
- **消息去重** — 5分钟滑动窗口防止重复处理
- **带退避的自动重试** — 从瞬时API错误中恢复

## 配置选项

在`config.yaml`中的`platforms.weixin.extra`下设置：

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `account_id` | — | iLink Bot账户ID（必需） |
| `token` | — | iLink Bot令牌（必需，从QR登录自动保存） |
| `base_url` | `https://ilinkai.weixin.qq.com` | iLink API基础URL |
| `cdn_base_url` | `https://novac2c.cdn.weixin.qq.com/c2c` | 用于媒体传输的CDN基础URL |
| `dm_policy` | `open` | DM访问：`open`、`allowlist`、`disabled`、`pairing` |
| `group_policy` | `disabled` | 群组访问：`open`、`allowlist`、`disabled` |
| `allow_from` | `[]` | 允许DM的用户ID（当dm_policy=allowlist时） |
| `group_allow_from` | `[]` | 允许的群组ID（当group_policy=allowlist时） |
| `split_multiline_messages` | `false` | 当为`true`时，将多行回复分割为多条聊天消息（传统行为）。当为`false`时，保持多行回复为一条消息，除非它们超过长度限制。 |

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
WEIXIN_DM_POLICY=allowlist
WEIXIN_ALLOWED_USERS=user_id_1,user_id_2
```

### 群组策略

控制机器人在哪些群组中响应：

| 值 | 行为 |
|-------|----------|
| `open` | 机器人在所有群组中响应 |
| `allowlist` | 机器人仅在`group_allow_from`中列出的群组ID中响应 |
| `disabled` | 所有群消息都被忽略（默认） |

```bash
WEIXIN_GROUP_POLICY=allowlist
WEIXIN_GROUP_ALLOWED_USERS=group_id_1,group_id_2
```

:::note
微信的默认群组策略是`disabled`（与WeCom默认设置为`open`不同）。这是有意的，因为个人微信账户可能在许多群组中。
:::

## 媒体支持

### 入站（接收）

适配器接收用户的媒体附件，从微信CDN下载它们，解密它们，并将它们本地缓存以供代理处理：

| 类型 | 处理方式 |
|------|-----------------| 
| **图像** | 下载、AES解密并缓存为JPEG。 |
| **视频** | 下载、AES解密并缓存为MP4。 |
| **文件** | 下载、AES解密并缓存。保留原始文件名。 |
| **语音** | 如果有文本转录，则将其提取为文本。否则，下载并缓存音频（SILK格式）。 |

**引用消息：** 来自引用（回复）消息的媒体也会被提取，因此代理了解用户正在回复的内容的上下文。

### AES-128-ECB加密CDN

微信媒体文件通过加密的CDN传输。适配器透明处理这一点：

- **入站：** 加密媒体使用`encrypted_query_param` URL从CDN下载，然后使用消息有效载荷中提供的每文件密钥通过AES-128-ECB解密。
- **出站：** 文件在本地使用随机AES-128-ECB密钥加密，上传到CDN，并在出站消息中包含加密引用。
- AES密钥为16字节（128位）。密钥可能以原始base64或十六进制编码形式到达 — 适配器处理两种格式。
- 这需要`cryptography` Python包。

无需配置 — 加密和解密自动进行。

### 出站（发送）

| 方法 | 发送内容 |
|--------|--------------|
| `send` | 带有Markdown格式的文本消息 | 
| `send_image` / `send_image_file` | 原生图像消息（通过CDN上传） |
| `send_document` | 文件附件（通过CDN上传） |
| `send_video` | 视频消息（通过CDN上传） |

所有出站媒体都通过加密的CDN上传流程：

1. 生成随机AES-128密钥
2. 使用AES-128-ECB + PKCS#7填充加密文件
3. 从iLink API请求上传URL (`getuploadurl`)
4. 将密文上传到CDN
5. 发送带有加密媒体引用的消息

## 上下文令牌持久性

iLink Bot API要求为给定对等方的每条出站消息回显`context_token`。适配器维护磁盘支持的上下文令牌存储：

- 令牌按账户+对等方保存到`~/.hermes/weixin/accounts/<account_id>.context-tokens.json`
- 启动时，恢复以前保存的令牌
- 每条入站消息更新该发送者的存储令牌
- 出站消息自动包含最新的上下文令牌

这确保即使在网关重启后也能保持回复连续性。

## Markdown格式

微信的个人聊天不原生呈现完整的Markdown。适配器重新格式化内容以提高可读性：

- **标题** (`# Title`) → 转换为`【Title】`（级别1）或`**Title**`（级别2+）
- **表格** → 重新格式化为带标签的键值列表（例如，`- Column: Value`）
- **代码块** → 保持原样（微信足够好地呈现这些）
- **过多的空行** → 折叠为双换行符

## 消息分块

只要消息符合平台限制，它们就会作为单条聊天消息传递。只有超大有效载荷会被分割传递：

- 最大消息长度：**4000字符**
- 限制下的消息即使包含多个段落或换行符也保持完整
- 超大消息在逻辑边界（段落、空行、代码块）处分割
- 代码块在可能的情况下保持完整（除非围栏本身超过限制，否则永远不会在块中间分割）
- 超大单个块回退到基础适配器的截断逻辑
- 0.3秒的块间延迟防止发送多个块时的微信速率限制下降

## 输入指示器

适配器在微信客户端中显示输入状态：

1. 当消息到达时，适配器通过`getconfig` API获取`typing_ticket`
2. 输入票证按用户缓存10分钟
3. `send_typing`发送输入开始信号；`stop_typing`发送输入停止信号
4. 网关在代理处理消息时自动触发输入指示器

## 长轮询连接

适配器使用HTTP长轮询（而非WebSocket）接收消息：

### 工作原理

1. **连接：** 验证凭据并启动轮询循环
2. **轮询：** 调用`getupdates`，超时35秒；服务器保持请求直到消息到达或超时过期
3. **调度：** 入站消息通过`asyncio.create_task`并发调度
4. **同步缓冲区：** 持久同步游标（`get_updates_buf`）保存到磁盘，以便适配器在重启后从正确的位置恢复

### 重试行为

对于API错误，适配器使用简单的重试策略：

| 条件 | 行为 |
|-----------|----------|
| 瞬时错误（第1-2次） | 2秒后重试 |
| 重复错误（3+次） | 退避30秒，然后重置计数器 |
| 会话过期 (`errcode=-14`) | 暂停10分钟（可能需要重新登录） |
| 超时 | 立即重新轮询（正常长轮询行为） |

### 去重

入站消息使用消息ID进行去重，窗口为5分钟。这防止在网络故障或重叠轮询响应期间重复处理。

### 令牌锁

一次只能有一个Weixin网关实例使用给定的令牌。适配器在启动时获取作用域锁，并在关闭时释放它。如果另一个网关已经在使用相同的令牌，启动将失败并显示信息性错误消息。

## 所有环境变量

| 变量 | 必需 | 默认值 | 描述 |
|----------|----------|---------|-------------|
| `WEIXIN_ACCOUNT_ID` | ✅ | — | iLink Bot账户ID（来自QR登录） |
| `WEIXIN_TOKEN` | ✅ | — | iLink Bot令牌（从QR登录自动保存） |
| `WEIXIN_BASE_URL` | — | `https://ilinkai.weixin.qq.com` | iLink API基础URL |
| `WEIXIN_CDN_BASE_URL` | — | `https://novac2c.cdn.weixin.qq.com/c2c` | 用于媒体传输的CDN基础URL |
| `WEIXIN_DM_POLICY` | — | `open` | DM访问策略：`open`、`allowlist`、`disabled`、`pairing` |
| `WEIXIN_GROUP_POLICY` | — | `disabled` | 群组访问策略：`open`、`allowlist`、`disabled` |
| `WEIXIN_ALLOWED_USERS` | — | _(empty)_ | DM允许列表的逗号分隔用户ID |
| `WEIXIN_GROUP_ALLOWED_USERS` | — | _(empty)_ | 群组允许列表的逗号分隔群组ID |
| `WEIXIN_HOME_CHANNEL` | — | — | 用于定时任务/通知输出的聊天ID |
| `WEIXIN_HOME_CHANNEL_NAME` | — | `Home` | 主频道的显示名称 |
| `WEIXIN_ALLOW_ALL_USERS` | — | — | 网关级标志，允许所有用户（由设置向导使用） |

## 故障排除

| 问题 | 解决方案 |
|---------|-----|
| `Weixin startup failed: aiohttp and cryptography are required` | 安装两者：`pip install aiohttp cryptography` |
| `Weixin startup failed: WEIXIN_TOKEN is required` | 运行`hermes gateway setup`完成QR登录，或手动设置`WEIXIN_TOKEN` |
| `Weixin startup failed: WEIXIN_ACCOUNT_ID is required` | 在`.env`中设置`WEIXIN_ACCOUNT_ID`或运行`hermes gateway setup` |
| `Another local Hermes gateway is already using this Weixin token` | 首先停止其他网关实例 — 每个令牌只允许一个轮询器 |
| 会话过期 (`errcode=-14`) | 您的登录会话已过期。重新运行`hermes gateway setup`扫描新的QR码 |
| 设置期间QR码过期 | QR码自动刷新最多3次。如果持续过期，请检查您的网络连接 |
| 机器人不响应DM | 检查`WEIXIN_DM_POLICY` — 如果设置为`allowlist`，发件人必须在`WEIXIN_ALLOWED_USERS`中 |
| 机器人忽略群消息 | 群组策略默认为`disabled`。设置`WEIXIN_GROUP_POLICY=open`或`allowlist` |
| 媒体下载/上传失败 | 确保安装了`cryptography`。检查对`novac2c.cdn.weixin.qq.com`的网络访问 |
| `Blocked unsafe URL (SSRF protection)` | 出站媒体URL指向私有/内部地址。只允许公共URL |
| 语音消息显示为文本 | 如果微信提供转录，适配器使用文本。这是预期行为 |
| 消息出现重复 | 适配器按消息ID去重。如果看到重复，请检查是否运行了多个网关实例 |
| `iLink POST ... HTTP 4xx/5xx` | 来自iLink服务的API错误。检查您的令牌有效性和网络连接 |
| 终端QR码不渲染 | 安装`qrcode`：`pip install qrcode`。或者，打开QR码上方打印的URL |