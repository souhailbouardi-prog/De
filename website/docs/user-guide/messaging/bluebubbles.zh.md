# BlueBubbles (iMessage)

通过[BlueBubbles](https://bluebubbles.app/)将Hermes连接到Apple iMessage — 一个免费、开源的macOS服务器，将iMessage桥接到任何设备。

## 前提条件

- 一台**Mac**（始终开启）运行[BlueBubbles Server](https://bluebubbles.app/)
- 在该Mac上登录Messages.app的Apple ID
- BlueBubbles Server v1.0.0+（webhooks需要此版本）
- Hermes与BlueBubbles服务器之间的网络连接

## 设置

### 1. 安装BlueBubbles Server

从[bluebubbles.app](https://bluebubbles.app/)下载并安装。完成设置向导 — 使用您的Apple ID登录并配置连接方法（本地网络、Ngrok、Cloudflare或动态DNS）。

### 2. 获取您的服务器URL和密码

在BlueBubbles Server → **设置 → API** 中，记录：
- **服务器URL**（例如 `http://192.168.1.10:1234`）
- **服务器密码**

### 3. 配置Hermes

运行设置向导：

```bash
hermes gateway setup
```

选择 **BlueBubbles (iMessage)** 并输入您的服务器URL和密码。

或直接在 `~/.hermes/.env` 中设置环境变量：

```bash
BLUEBUBBLES_SERVER_URL=http://192.168.1.10:1234
BLUEBUBBLES_PASSWORD=your-server-password
```

### 4. 授权用户

选择一种方法：

**私聊配对（推荐）：**
当有人向您的iMessage发送消息时，Hermes会自动向他们发送配对码。使用以下命令批准：
```bash
hermes pairing approve bluebubbles <CODE>
```
使用 `hermes pairing list` 查看待处理的代码和已批准的用户。

**预授权特定用户**（在 `~/.hermes/.env` 中）：
```bash
BLUEBUBBLES_ALLOWED_USERS=user@icloud.com,+15551234567
```

**开放访问**（在 `~/.hermes/.env` 中）：
```bash
BLUEBUBBLES_ALLOW_ALL_USERS=true
```

### 5. 启动网关

```bash
hermes gateway run
```

Hermes将连接到您的BlueBubbles服务器，注册webhook，并开始监听iMessage消息。

## 工作原理

```
iMessage → Messages.app → BlueBubbles Server → Webhook → Hermes
Hermes → BlueBubbles REST API → Messages.app → iMessage
```

- **入站：** 当新消息到达时，BlueBubbles向本地监听器发送webhook事件。无轮询 — 即时交付。
- **出站：** Hermes通过BlueBubbles REST API发送消息。
- **媒体：** 双向支持图像、语音消息、视频和文档。入站附件被下载并在本地缓存以供代理处理。

## 环境变量

| 变量 | 必填 | 默认值 | 描述 |
|----------|----------|---------|-------------|
| `BLUEBUBBLES_SERVER_URL` | 是 | — | BlueBubbles服务器URL |
| `BLUEBUBBLES_PASSWORD` | 是 | — | 服务器密码 |
| `BLUEBUBBLES_WEBHOOK_HOST` | 否 | `127.0.0.1` | Webhook监听器绑定地址 |
| `BLUEBUBBLES_WEBHOOK_PORT` | 否 | `8645` | Webhook监听器端口 |
| `BLUEBUBBLES_WEBHOOK_PATH` | 否 | `/bluebubbles-webhook` | Webhook URL路径 |
| `BLUEBUBBLES_HOME_CHANNEL` | 否 | — | 用于定时任务交付的电话/电子邮件 |
| `BLUEBUBBLES_ALLOWED_USERS` | 否 | — | 逗号分隔的授权用户 |
| `BLUEBUBBLES_ALLOW_ALL_USERS` | 否 | `false` | 允许所有用户 |
| `BLUEBUBBLES_SEND_READ_RECEIPTS` | 否 | `true` | 自动标记消息为已读 |

## 功能

### 文本消息

发送和接收iMessage。Markdown会自动剥离，以确保干净的纯文本交付。

### 富媒体

- **图像：** 照片在iMessage对话中以原生方式显示
- **语音消息：** 音频文件作为iMessage语音消息发送
- **视频：** 视频附件
- **文档：** 文件作为iMessage附件发送

### 轻触反应

喜欢、点赞、不喜欢、大笑、强调和疑问反应。需要BlueBubbles [Private API助手](https://docs.bluebubbles.app/helper-bundle/installation)。

### 输入指示器

在代理处理时，在iMessage对话中显示"正在输入..."。需要Private API。

### 已读回执

处理后自动将消息标记为已读。需要Private API。

### 聊天寻址

您可以通过电子邮件或电话号码寻址聊天 — Hermes会自动将它们解析为BlueBubbles聊天GUID。无需使用原始GUID格式。

## Private API

某些功能需要BlueBubbles [Private API助手](https://docs.bluebubbles.app/helper-bundle/installation)：
- 轻触反应
- 输入指示器
- 已读回执
- 按地址创建新聊天

没有Private API，基本的文本消息和媒体仍然可以工作。

## 故障排除

### "无法到达服务器"

- 验证服务器URL正确且Mac已开启
- 检查BlueBubbles Server是否正在运行
- 确保网络连接（防火墙、端口转发）

### 消息未到达

- 检查webhook是否在BlueBubbles Server → 设置 → API → Webhooks中注册
- 验证webhook URL可从Mac访问
- 检查 `hermes logs gateway` 获取webhook错误（或 `hermes logs -f` 实时跟踪）

### "Private API助手未连接"

- 安装Private API助手：[docs.bluebubbles.app](https://docs.bluebubbles.app/helper-bundle/installation)
- 基本消息传递无需它 — 只有反应、输入和已读回执需要它