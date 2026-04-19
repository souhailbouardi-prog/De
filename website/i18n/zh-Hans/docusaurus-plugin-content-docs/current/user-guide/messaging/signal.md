---
sidebar_position: 6
title: "Signal"
description: "通过signal-cli守护进程设置Hermes Agent作为Signal消息传递机器人"
---

# Signal设置

Hermes通过运行在HTTP模式下的[signal-cli](https://github.com/AsamK/signal-cli)守护进程连接到Signal。适配器通过SSE（服务器发送事件）实时流式传输消息，并通过JSON-RPC发送响应。

Signal是最注重隐私的主流 messenger — 默认端到端加密，开源协议，最小化元数据收集。这使其成为安全敏感的代理工作流程的理想选择。

:::info 无新Python依赖
Signal适配器使用`httpx`（已经是Hermes的核心依赖）进行所有通信。不需要额外的Python包。您只需要在外部安装signal-cli。
:::

---

## 先决条件

- **signal-cli** — 基于Java的Signal客户端 ([GitHub](https://github.com/AsamK/signal-cli))
- **Java 17+** 运行时 — signal-cli所需
- **一个安装了Signal的电话号码**（用于作为辅助设备链接）

### 安装signal-cli

```bash
# macOS
brew install signal-cli

# Linux（下载最新版本）
VERSION=$(curl -Ls -o /dev/null -w %{url_effective} \
  https://github.com/AsamK/signal-cli/releases/latest | sed 's/^.*\/v//')
curl -L -O "https://github.com/AsamK/signal-cli/releases/download/v${VERSION}/signal-cli-${VERSION}.tar.gz"
sudo tar xf "signal-cli-${VERSION}.tar.gz" -C /opt
sudo ln -sf "/opt/signal-cli-${VERSION}/bin/signal-cli" /usr/local/bin/
```

:::caution
signal-cli **不在** apt或snap存储库中。上面的Linux安装直接从[GitHub releases](https://github.com/AsamK/signal-cli/releases)下载。
:::

---

## 步骤1：链接您的Signal账户

Signal-cli作为**链接设备**工作 — 类似于WhatsApp Web，但适用于Signal。您的手机保持为主设备。

```bash
# 生成链接URI（显示QR码或链接）
signal-cli link -n "HermesAgent"
```

1. 在您的手机上打开**Signal**
2. 转到**设置 → 链接设备**
3. 点击**链接新设备**
4. 扫描QR码或输入URI

---

## 步骤2：启动signal-cli守护进程

```bash
# 用您的Signal电话号码替换+1234567890（E.164格式）
signal-cli --account +1234567890 daemon --http 127.0.0.1:8080
```

:::tip
让这个在后台运行。您可以使用`systemd`、`tmux`、`screen`或作为服务运行。
:::

验证它正在运行：

```bash
curl http://127.0.0.1:8080/api/v1/check
# 应返回：{"versions":{"signal-cli":...}}
```

---

## 步骤3：配置Hermes

最简单的方法：

```bash
hermes gateway setup
```

从平台菜单中选择**Signal**。向导将：

1. 检查是否安装了signal-cli
2. 提示输入HTTP URL（默认：`http://127.0.0.1:8080`）
3. 测试与守护进程的连接
4. 询问您的账户电话号码
5. 配置允许的用户和访问策略

### 手动配置

添加到 `~/.hermes/.env`：

```bash
# 必需
SIGNAL_HTTP_URL=http://127.0.0.1:8080
SIGNAL_ACCOUNT=+1234567890

# 安全（推荐）
SIGNAL_ALLOWED_USERS=+1234567890,+0987654321    # 逗号分隔的E.164号码或UUID

# 可选
SIGNAL_GROUP_ALLOWED_USERS=groupId1,groupId2     # 启用群组（省略以禁用，*表示全部）
SIGNAL_HOME_CHANNEL=+1234567890                  # 定时任务的默认传递目标
```

然后启动网关：

```bash
hermes gateway              # 前台运行
hermes gateway install      # 安装为用户服务
sudo hermes gateway install --system   # 仅Linux：启动时系统服务
```

---

## 访问控制

### DM访问

DM访问遵循与所有其他Hermes平台相同的模式：

1. **设置`SIGNAL_ALLOWED_USERS`** → 只有那些用户可以发消息
2. **未设置允许列表** → 未知用户获得DM配对代码（通过`hermes pairing approve signal CODE`批准）
3. **`SIGNAL_ALLOW_ALL_USERS=true`** → 任何人都可以发消息（谨慎使用）

### 群组访问

群组访问由`SIGNAL_GROUP_ALLOWED_USERS`环境变量控制：

| 配置 | 行为 |
|---------------|----------|
| 未设置（默认） | 忽略所有群组消息。机器人只响应DM。 |
| 设置群组ID | 仅监控列出的群组（例如，`groupId1,groupId2`）。 |
| 设置为`*` | 机器人在它是成员的任何群组中响应。 |

---

## 功能

### 附件

适配器支持双向发送和接收媒体。

**传入**（用户 → 代理）：

- **图像** — PNG、JPEG、GIF、WebP（通过魔术字节自动检测）
- **音频** — MP3、OGG、WAV、M4A（如果配置了Whisper，语音消息会被转录）
- **文档** — PDF、ZIP和其他文件类型

**传出**（代理 → 用户）：

代理可以通过响应中的`MEDIA:`标签发送媒体文件。支持以下传递方法：

- **图像** — `send_image_file`发送PNG、JPEG、GIF、WebP作为原生Signal附件
- **语音** — `send_voice`发送音频文件（OGG、MP3、WAV、M4A、AAC）作为附件
- **视频** — `send_video`发送MP4视频文件
- **文档** — `send_document`发送任何文件类型（PDF、ZIP等）

所有传出媒体都通过Signal的标准附件API。与某些平台不同，Signal在协议级别不区分语音消息和文件附件。

附件大小限制：**100 MB**（双向）。

### 输入指示器

机器人在处理消息时发送输入指示器，每8秒刷新一次。

### 电话号码编辑

所有电话号码在日志中自动编辑：
- `+15551234567` → `+155****4567`
- 这适用于Hermes网关日志和全局编辑系统

### 给自己的笔记（单号码设置）

如果您在自己的电话号码上运行signal-cli作为**链接的辅助设备**（而不是单独的机器人号码），您可以通过Signal的"给自己的笔记"功能与Hermes交互。

只需从您的手机向自己发送消息 — signal-cli接收它，Hermes在同一对话中响应。

**工作原理：**
- "给自己的笔记"消息以`syncMessage.sentMessage`信封到达
- 适配器检测这些消息何时发送到机器人自己的账户，并将其作为常规入站消息处理
- 回显保护（发送时间戳跟踪）防止无限循环 — 机器人自己的回复被自动过滤掉

**无需额外配置。** 只要`SIGNAL_ACCOUNT`与您的电话号码匹配，这就会自动工作。

### 健康监控

适配器监控SSE连接并在以下情况下自动重新连接：
- 连接断开（指数退避：2s → 60s）
- 120秒内未检测到活动（ping signal-cli以验证）

---

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| **设置期间"无法到达signal-cli"** | 确保signal-cli守护进程正在运行：`signal-cli --account +YOUR_NUMBER daemon --http 127.0.0.1:8080` |
| **未收到消息** | 检查`SIGNAL_ALLOWED_USERS`是否包含E.164格式的发件人号码（带`+`前缀） |
| **"signal-cli not found on PATH"** | 安装signal-cli并确保它在您的PATH中，或使用Docker |
| **连接不断断开** | 检查signal-cli日志中的错误。确保安装了Java 17+。 |
| **群组消息被忽略** | 配置`SIGNAL_GROUP_ALLOWED_USERS`，使用特定的群组ID，或`*`允许所有群组。 |
| **机器人对任何人都不响应** | 配置`SIGNAL_ALLOWED_USERS`，使用DM配对，或如果您想要更广泛的访问，通过网关策略明确允许所有用户。 |
| **重复消息** | 确保只有一个signal-cli实例在监听您的电话号码 |

---

## 安全

:::warning
**始终配置访问控制。** 机器人默认具有终端访问权限。没有`SIGNAL_ALLOWED_USERS`或DM配对，网关会拒绝所有入站消息作为安全措施。
:::

- 所有日志输出中的电话号码都被编辑
- 使用DM配对或明确的允许列表进行新用户的安全入职
- 除非您特别需要群组支持，否则保持群组禁用，或者只允许您信任的群组
- Signal的端到端加密保护传输中的消息内容
- `~/.local/share/signal-cli/`中的signal-cli会话数据包含账户凭据 — 像保护密码一样保护它

---

## 环境变量参考

| 变量 | 必需 | 默认值 | 描述 |
|----------|----------|---------|-------------|
| `SIGNAL_HTTP_URL` | 是 | — | signal-cli HTTP端点 |
| `SIGNAL_ACCOUNT` | 是 | — | 机器人电话号码（E.164） |
| `SIGNAL_ALLOWED_USERS` | 否 | — | 逗号分隔的电话号码/UUID |
| `SIGNAL_GROUP_ALLOWED_USERS` | 否 | — | 要监控的群组ID，或`*`表示全部（省略以禁用群组） |
| `SIGNAL_ALLOW_ALL_USERS` | 否 | `false` | 允许任何用户交互（跳过允许列表） |
| `SIGNAL_HOME_CHANNEL` | 否 | — | 定时任务的默认传递目标 |