---
sidebar_position: 9
title: "Matrix"
description: "将 Hermes Agent 设置为 Matrix 机器人"
---

# Matrix 设置

Hermes Agent 与 Matrix（开放的联邦消息协议）集成。Matrix 允许您运行自己的 homeserver 或使用公共服务器如 matrix.org — 无论哪种方式，您都能保持对通信的控制。机器人通过 `mautrix` Python SDK 连接，通过 Hermes Agent 管道处理消息（包括工具使用、内存和推理），并实时响应。它支持文本、文件附件、图像、音频、视频和可选的端到端加密（E2EE）。

Hermes 适用于任何 Matrix homeserver — Synapse、Conduit、Dendrite 或 matrix.org。

在设置之前，这里是大多数人想知道的：Hermes 连接后如何行为。

## Hermes 的行为

| 上下文 | 行为 |
|---------|----------|
| **私聊** | Hermes 响应每条消息。不需要 `@提及`。每个私聊都有自己的会话。设置 `MATRIX_DM_MENTION_THREADS=true` 以在机器人在私聊中被 `@提及` 时启动线程。 |
| **房间** | 默认情况下，Hermes 需要 `@提及` 才会响应。设置 `MATRIX_REQUIRE_MENTION=false` 或向 `MATRIX_FREE_RESPONSE_ROOMS` 添加房间 ID 以获得自由响应房间。房间邀请会被自动接受。 |
| **线程** | Hermes 支持 Matrix 线程（MSC3440）。如果您在线程中回复，Hermes 会将线程上下文与主房间时间线隔离。机器人已经参与的线程不需要提及。 |
| **自动线程** | 默认情况下，Hermes 会为它在房间中响应的每条消息自动创建线程。这保持了对话的隔离。设置 `MATRIX_AUTO_THREAD=false` 以禁用。 |
| **有多个用户的共享房间** | 默认情况下，Hermes 在房间内为每个用户隔离会话历史。除非您明确禁用，否则在同一个房间中交谈的两个人不会共享一个对话记录。 |

:::tip
机器人在被邀请时会自动加入房间。只需将机器人的 Matrix 用户邀请到任何房间，它就会加入并开始响应。
:::

### Matrix 中的会话模型

默认情况下：

- 每个私聊获得自己的会话
- 每个线程获得自己的会话命名空间
- 共享房间中的每个用户在该房间内获得自己的会话

这由 `config.yaml` 控制：

```yaml
group_sessions_per_user: true
```

只有当您明确希望整个房间共享一个对话时，才将其设置为 `false`：

```yaml
group_sessions_per_user: false
```

共享会话对于协作房间很有用，但它们也意味着：

- 用户共享上下文增长和令牌成本
- 一个人的长工具任务可能会膨胀其他人的上下文
- 一个人的进行中运行可能会中断同一房间中另一个人的后续操作

### 提及和线程配置

您可以通过环境变量或 `config.yaml` 配置提及和自动线程行为：

```yaml
matrix:
  require_mention: true           # 在房间中需要 @提及（默认：true）
  free_response_rooms:            # 免除提及要求的房间
    - "!abc123:matrix.org"
  auto_thread: true               # 自动为响应创建线程（默认：true）
  dm_mention_threads: false       # 在私聊中被 @提及时创建线程（默认：false）
```

或通过环境变量：

```bash
MATRIX_REQUIRE_MENTION=true
MATRIX_FREE_RESPONSE_ROOMS=!abc123:matrix.org,!def456:matrix.org
MATRIX_AUTO_THREAD=true
MATRIX_DM_MENTION_THREADS=false
```

:::note
如果您从没有 `MATRIX_REQUIRE_MENTION` 的版本升级，机器人以前会响应房间中的所有消息。要保留该行为，请设置 `MATRIX_REQUIRE_MENTION=false`。
:::

本指南将引导您完成完整的设置过程 — 从创建机器人账户到发送第一条消息。

## 步骤 1：创建机器人账户

您需要为机器人创建一个 Matrix 用户账户。有几种方法可以做到这一点：

### 选项 A：在您的 Homeserver 上注册（推荐）

如果您运行自己的 homeserver（Synapse、Conduit、Dendrite）：

1. 使用管理 API 或注册工具创建新用户：

```bash
# Synapse 示例
register_new_matrix_user -c /etc/synapse/homeserver.yaml http://localhost:8008
```

2. 选择一个用户名，如 `hermes` — 完整的用户 ID 将是 `@hermes:your-server.org`。

### 选项 B：使用 matrix.org 或其他公共 Homeserver

1. 前往 [Element Web](https://app.element.io) 并创建一个新账户。
2. 为您的机器人选择一个用户名（例如 `hermes-bot`）。

### 选项 C：使用您自己的账户

您也可以以自己的用户身份运行 Hermes。这意味着机器人以您的身份发帖 — 对个人助手很有用。

## 步骤 2：获取访问令牌

Hermes 需要访问令牌才能向 homeserver 进行身份验证。您有两个选项：

### 选项 A：访问令牌（推荐）

获取令牌的最可靠方法：

**通过 Element：**
1. 使用机器人账户登录 [Element](https://app.element.io)。
2. 前往 **设置** → **帮助与关于**。
3. 向下滚动并展开 **高级** — 访问令牌显示在那里。
4. **立即复制它**。

**通过 API：**

```bash
curl -X POST https://your-server/_matrix/client/v3/login \
  -H "Content-Type: application/json" \
  -d '{
    "type": "m.login.password",
    "user": "@hermes:your-server.org",
    "password": "your-password"
  }'
```

响应包含一个 `access_token` 字段 — 复制它。

:::warning[保持您的访问令牌安全]
访问令牌授予对机器人 Matrix 账户的完全访问权限。永远不要公开分享它或将其提交到 Git。如果被泄露，通过为该用户注销所有会话来撤销它。
:::

### 选项 B：密码登录

您可以向 Hermes 提供机器人的用户 ID 和密码，而不是提供访问令牌。Hermes 将在启动时自动登录。这更简单，但意味着密码存储在您的 `.env` 文件中。

```bash
MATRIX_USER_ID=@hermes:your-server.org
MATRIX_PASSWORD=your-password
```

## 步骤 3：找到您的 Matrix 用户 ID

Hermes Agent 使用您的 Matrix 用户 ID 来控制谁可以与机器人交互。Matrix 用户 ID 遵循 `@username:server` 格式。

找到您的用户 ID：

1. 打开 [Element](https://app.element.io)（或您首选的 Matrix 客户端）。
2. 点击您的头像 → **设置**。
3. 您的用户 ID 显示在个人资料顶部（例如 `@alice:matrix.org`）。

:::tip
Matrix 用户 ID 始终以 `@` 开头，并包含一个 `:` 后跟服务器名称。例如：`@alice:matrix.org`、`@bob:your-server.com`。
:::

## 步骤 4：配置 Hermes Agent

### 选项 A：交互式设置（推荐）

运行引导设置命令：

```bash
hermes gateway setup
```

当提示时选择 **Matrix**，然后提供您的 homeserver URL、访问令牌（或用户 ID + 密码），以及在被询问时提供允许的用户 ID。

### 选项 B：手动配置

将以下内容添加到您的 `~/.hermes/.env` 文件：

**使用访问令牌：**

```bash
# 必需
MATRIX_HOMESERVER=https://matrix.example.org
MATRIX_ACCESS_TOKEN=***

# 可选：用户 ID（如果省略，会从令牌自动检测）
# MATRIX_USER_ID=@hermes:matrix.example.org

# 安全：限制谁可以与机器人交互
MATRIX_ALLOWED_USERS=@alice:matrix.example.org

# 多个允许的用户（逗号分隔）
# MATRIX_ALLOWED_USERS=@alice:matrix.example.org,@bob:matrix.example.org
```

**使用密码登录：**

```bash
# 必需
MATRIX_HOMESERVER=https://matrix.example.org
MATRIX_USER_ID=@hermes:matrix.example.org
MATRIX_PASSWORD=***

# 安全
MATRIX_ALLOWED_USERS=@alice:matrix.example.org
```

`~/.hermes/config.yaml` 中的可选行为设置：

```yaml
group_sessions_per_user: true
```

- `group_sessions_per_user: true` 保持每个参与者的上下文在共享房间内隔离

### 启动网关

配置完成后，启动 Matrix 网关：

```bash
hermes gateway
```

机器人应该在几秒钟内连接到您的 homeserver 并开始同步。向它发送一条消息 — 无论是私聊还是在它已加入的房间中 — 进行测试。

:::tip
您可以在后台运行 `hermes gateway` 或作为 systemd 服务以实现持久操作。有关详细信息，请参阅部署文档。
:::

## 端到端加密（E2EE）

Hermes 支持 Matrix 端到端加密，因此您可以在加密房间中与您的机器人聊天。

### 要求

E2EE 需要带有加密附加功能的 `mautrix` 库和 `libolm` C 库：

```bash
# 安装带有 E2EE 支持的 mautrix
pip install 'mautrix[encryption]'

# 或安装带有 hermes 附加功能
pip install 'hermes-agent[matrix]'
```

您还需要在系统上安装 `libolm`：

```bash
# Debian/Ubuntu
sudo apt install libolm-dev

# macOS
brew install libolm

# Fedora
sudo dnf install libolm-devel
```

### 启用 E2EE

添加到您的 `~/.hermes/.env`：

```bash
MATRIX_ENCRYPTION=true
```

启用 E2EE 后，Hermes：

- 将加密密钥存储在 `~/.hermes/platforms/matrix/store/` 中（旧版安装：`~/.hermes/matrix/store/`）
- 在首次连接时上传设备密钥
- 自动解密传入消息并加密传出消息
- 被邀请时自动加入加密房间

### 交叉签名验证（推荐）

如果您的 Matrix 账户启用了交叉签名（Element 中的默认设置），请设置恢复密钥，以便机器人可以在启动时自签名其设备。没有这个，其他 Matrix 客户端可能会在设备密钥轮换后拒绝与机器人共享加密会话。

```bash
MATRIX_RECOVERY_KEY=EsT... your recovery key here
```

**在哪里找到它：** 在 Element 中，前往 **设置** → **安全与隐私** → **加密** → 您的恢复密钥（也称为 "安全密钥"）。这是您首次设置交叉签名时被要求保存的密钥。

每次启动时，如果设置了 `MATRIX_RECOVERY_KEY`，Hermes 会从 homeserver 的安全秘密存储中导入交叉签名密钥并签名当前设备。这是幂等的，可以安全地永久启用。

:::warning[删除加密存储]
如果您删除 `~/.hermes/platforms/matrix/store/crypto.db`，机器人会失去其加密身份。使用相同的设备 ID 简单重启 **不会** 完全恢复 — homeserver 仍然持有用旧身份密钥签名的一次性密钥，并且对等方无法建立新的 Olm 会话。

Hermes 在启动时检测到这种情况并拒绝启用 E2EE，记录：`device XXXX has stale one-time keys on the server signed with a previous identity key`。

**最简单的恢复：生成新的访问令牌**（这会获得一个没有过时密钥历史的新设备 ID）。请参阅下面的 "从以前版本的 E2EE 升级" 部分。这是最可靠的路径，避免触及 homeserver 数据库。

**手动恢复**（高级 — 保持相同的设备 ID）：

1. 停止 Synapse 并从其数据库中删除旧设备：
   ```bash
   sudo systemctl stop matrix-synapse
   sudo sqlite3 /var/lib/matrix-synapse/homeserver.db "
     DELETE FROM e2e_device_keys_json WHERE device_id = 'DEVICE_ID' AND user_id = '@hermes:your-server';
     DELETE FROM e2e_one_time_keys_json WHERE device_id = 'DEVICE_ID' AND user_id = '@hermes:your-server';
     DELETE FROM e2e_fallback_keys_json WHERE device_id = 'DEVICE_ID' AND user_id = '@hermes:your-server';
     DELETE FROM devices WHERE device_id = 'DEVICE_ID' AND user_id = '@hermes:your-server';
   "
   sudo systemctl start matrix-synapse
   ```
   或通过 Synapse 管理 API（注意 URL 编码的用户 ID）：
   ```bash
   curl -X DELETE -H "Authorization: Bearer ADMIN_TOKEN" \
     'https://your-server/_synapse/admin/v2/users/%40hermes%3Ayour-server/devices/DEVICE_ID'
   ```
   注意：通过管理 API 删除设备也可能使关联的访问令牌失效。您可能需要在之后生成新的令牌。

2. 删除本地加密存储并重启 Hermes：
   ```bash
   rm -f ~/.hermes/platforms/matrix/store/crypto.db*
   # restart hermes
   ```

其他 Matrix 客户端（Element、matrix-commander）可能会缓存旧设备密钥。恢复后，在 Element 中输入 `/discardsession` 以强制与机器人建立新的加密会话。
:::

:::info
如果未安装 `mautrix[encryption]` 或缺少 `libolm`，机器人会自动回退到普通（未加密）客户端。您会在日志中看到警告。
:::

## 主房间

您可以指定一个 "主房间"，机器人会在其中发送主动消息（例如 cron 作业输出、提醒和通知）。有两种设置方法：

### 使用斜杠命令

在机器人所在的任何 Matrix 房间中输入 `/sethome`。该房间成为主房间。

### 手动配置

添加到您的 `~/.hermes/.env`：

```bash
MATRIX_HOME_ROOM=!abc123def456:matrix.example.org
```

:::tip
要找到房间 ID：在 Element 中，前往房间 → **设置** → **高级** → **内部房间 ID** 显示在那里（以 `!` 开头）。
:::

## 故障排除

### 机器人不响应消息

**原因**：机器人尚未加入房间，或 `MATRIX_ALLOWED_USERS` 不包含您的用户 ID。

**修复**：邀请机器人加入房间 — 它会在邀请时自动加入。验证您的用户 ID 是否在 `MATRIX_ALLOWED_USERS` 中（使用完整的 `@user:server` 格式）。重启网关。

### 启动时 "Failed to authenticate" / "whoami failed"

**原因**：访问令牌或 homeserver URL 不正确。

**修复**：验证 `MATRIX_HOMESERVER` 指向您的 homeserver（包括 `https://`，无尾随斜杠）。检查 `MATRIX_ACCESS_TOKEN` 是否有效 — 尝试用 curl 测试：

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-server/_matrix/client/v3/account/whoami
```

如果这返回您的用户信息，则令牌有效。如果返回错误，请生成新令牌。

### "mautrix not installed" 错误

**原因**：未安装 `mautrix` Python 包。

**修复**：安装它：

```bash
pip install 'mautrix[encryption]'
```

或使用 Hermes 附加功能：

```bash
pip install 'hermes-agent[matrix]'
```

### 加密错误 / "could not decrypt event"

**原因**：缺少加密密钥、未安装 `libolm` 或机器人的设备不受信任。

**修复**：
1. 验证您的系统上安装了 `libolm`（请参阅上面的 E2EE 部分）。
2. 确保 `MATRIX_ENCRYPTION=true` 在您的 `.env` 中设置。
3. 在您的 Matrix 客户端（Element）中，前往机器人的个人资料 -> 会话 -> 验证/信任机器人的设备。
4. 如果机器人刚刚加入加密房间，它只能解密它加入后发送的消息。旧消息无法访问。

### 从以前版本的 E2EE 升级

:::tip
如果您还手动删除了 `crypto.db`，请参阅 E2EE 部分中的 "删除加密存储" 警告 — 有额外的步骤来清除 homeserver 中的过时一次性密钥。
:::

如果您之前使用带有 `MATRIX_ENCRYPTION=true` 的 Hermes 并升级到使用新的基于 SQLite 的加密存储的版本，机器人的加密身份已更改。您的 Matrix 客户端（Element）可能会缓存旧设备密钥并拒绝与机器人共享加密会话。

**症状**：机器人连接并在日志中显示 "E2EE enabled"，但所有消息都显示 "could not decrypt event"，机器人从不响应。

**发生了什么**：旧的加密状态（来自之前的 `matrix-nio` 或基于序列化的 `mautrix` 后端）与新的 SQLite 加密存储不兼容。机器人创建了一个新的加密身份，但您的 Matrix 客户端仍然缓存旧密钥，不会与密钥已更改的设备共享房间的加密会话。这是 Matrix 安全功能 — 客户端将同一设备的身份密钥更改视为可疑。

**修复**（一次性迁移）：

1. **生成新的访问令牌** 以获得新的设备 ID。最简单的方法：

   ```bash
   curl -X POST https://your-server/_matrix/client/v3/login \
     -H "Content-Type: application/json" \
     -d '{
       "type": "m.login.password",
       "identifier": {"type": "m.id.user", "user": "@hermes:your-server.org"},
       "password": "***",
       "initial_device_display_name": "Hermes Agent"
     }'
   ```

   复制新的 `access_token` 并更新 `~/.hermes/.env` 中的 `MATRIX_ACCESS_TOKEN`。

2. **删除旧的加密状态**：

   ```bash
   rm -f ~/.hermes/platforms/matrix/store/crypto.db
   rm -f ~/.hermes/platforms/matrix/store/crypto_store.*
   ```

3. **设置您的恢复密钥**（如果您使用交叉签名 — 大多数 Element 用户都使用）。添加到 `~/.hermes/.env`：

   ```bash
   MATRIX_RECOVERY_KEY=EsT... your recovery key here
   ```

   这让机器人在启动时使用交叉签名密钥自签名，因此 Element 立即信任新设备。没有这个，Element 可能会将新设备视为未验证并拒绝共享加密会话。在 Element 的 **设置** → **安全与隐私** → **加密** 下找到您的恢复密钥。

4. **强制您的 Matrix 客户端轮换加密会话**。在 Element 中，打开与机器人的私聊房间并输入 `/discardsession`。这强制 Element 创建新的加密会话并与机器人的新设备共享。

5. **重启网关**：

   ```bash
   hermes gateway run
   ```

   如果设置了 `MATRIX_RECOVERY_KEY`，您应该在日志中看到 `Matrix: cross-signing verified via recovery key`。

6. **发送新消息**。机器人应该正常解密并响应。

:::note
迁移后，*升级前* 发送的消息无法解密 — 旧的加密密钥已消失。这只影响过渡；新消息正常工作。
:::

:::tip
**新安装不受影响**。此迁移仅在您之前使用 Hermes 并启用了 E2EE 且正在升级时才需要。

**为什么需要新的访问令牌？** 每个 Matrix 访问令牌都绑定到特定的设备 ID。使用新的加密密钥重用相同的设备 ID 会导致其他 Matrix 客户端不信任该设备（他们将身份密钥更改视为潜在的安全漏洞）。新的访问令牌获得一个没有过时密钥历史的新设备 ID，因此其他客户端立即信任它。
:::

## 代理模式（macOS 上的 E2EE）

Matrix E2EE 需要 `libolm`，它在 macOS ARM64（Apple Silicon）上无法编译。`hermes-agent[matrix]` 附加功能仅在 Linux 上可用。如果您在 macOS 上，代理模式允许您在 Linux VM 的 Docker 容器中运行 E2EE，而实际的代理在 macOS 上本地运行，可以完全访问您的本地文件、内存和技能。

### 工作原理

```
macOS（主机）：
  └─ hermes gateway
       ├─ api_server 适配器 ← 监听 0.0.0.0:8642
       ├─ AIAgent ← 单一事实来源
       ├─ 会话、内存、技能
       └─ 本地文件访问（Obsidian、项目等）

Linux VM（Docker）：
  └─ hermes gateway（代理模式）
       ├─ Matrix 适配器 ← E2EE 解密/加密
       └─ HTTP 转发 → macOS:8642/v1/chat/completions
          （无 LLM API 密钥，无代理，无推理）
```

Docker 容器仅处理 Matrix 协议 + E2EE。当消息到达时，它解密并通过标准 HTTP 请求将文本转发到主机。主机运行代理，调用工具，生成响应，并将其流回。容器加密并将响应发送到 Matrix。所有会话都是统一的 — CLI、Matrix、Telegram 和任何其他平台共享相同的内存和对话历史。

### 步骤 1：配置主机（macOS）

启用 API 服务器，以便主机接受来自 Docker 容器的传入请求。

添加到 `~/.hermes/.env`：

```bash
API_SERVER_ENABLED=true
API_SERVER_KEY=your-secret-key-here
API_SERVER_HOST=0.0.0.0
```

- `API_SERVER_HOST=0.0.0.0` 绑定到所有接口，以便 Docker 容器可以访问它。
- `API_SERVER_KEY` 对于非环回绑定是必需的。选择一个强随机字符串。
- API 服务器默认在端口 8642 上运行（如果需要，可使用 `API_SERVER_PORT` 更改）。

启动网关：

```bash
hermes gateway
```

您应该看到 API 服务器与您配置的任何其他平台一起启动。验证它是否可从 VM 访问：

```bash
# 从 Linux VM
curl http://<mac-ip>:8642/health
```

### 步骤 2：配置 Docker 容器（Linux VM）

容器需要 Matrix 凭据和代理 URL。它不需要 LLM API 密钥。

**`docker-compose.yml`：**

```yaml
services:
  hermes-matrix:
    build: .
    environment:
      # Matrix 凭据
      MATRIX_HOMESERVER: "https://matrix.example.org"
      MATRIX_ACCESS_TOKEN: "syt_..."
      MATRIX_ALLOWED_USERS: "@you:matrix.example.org"
      MATRIX_ENCRYPTION: "true"
      MATRIX_DEVICE_ID: "HERMES_BOT"

      # 代理模式 — 转发到主机代理
      GATEWAY_PROXY_URL: "http://192.168.1.100:8642"
      GATEWAY_PROXY_KEY: "your-secret-key-here"
    volumes:
      - ./matrix-store:/root/.hermes/platforms/matrix/store
```

**`Dockerfile`：**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y libolm-dev && rm -rf /var/lib/apt/lists/*
RUN pip install 'hermes-agent[matrix]'

CMD ["hermes", "gateway"]
```

这就是整个容器。不需要 OpenRouter、Anthropic 或任何推理提供商的 API 密钥。

### 步骤 3：启动两者

1. 首先启动主机网关：
   ```bash
   hermes gateway
   ```

2. 启动 Docker 容器：
   ```bash
   docker compose up -d
   ```

3. 在加密的 Matrix 房间中发送消息。容器解密它，将其转发到主机，并将响应流回。

### 配置参考

代理模式在**容器端**（瘦网关）上配置：

| 设置 | 描述 |
|---------|-------------|
| `GATEWAY_PROXY_URL` | 远程 Hermes API 服务器的 URL（例如 `http://192.168.1.100:8642`） |
| `GATEWAY_PROXY_KEY` | 用于身份验证的 Bearer 令牌（必须与主机上的 `API_SERVER_KEY` 匹配） |
| `gateway.proxy_url` | 与 `GATEWAY_PROXY_URL` 相同，但在 `config.yaml` 中 |

主机端需要：

| 设置 | 描述 |
|---------|-------------|
| `API_SERVER_ENABLED` | 设置为 `true` |
| `API_SERVER_KEY` | Bearer 令牌（与容器共享） |
| `API_SERVER_HOST` | 设置为 `0.0.0.0` 以进行网络访问 |
| `API_SERVER_PORT` | 端口号（默认：`8642`） |

### 适用于任何平台

代理模式不限于 Matrix。任何平台适配器都可以使用它 — 在任何网关实例上设置 `GATEWAY_PROXY_URL`，它将转发到远程代理，而不是在本地运行一个。这对于平台适配器需要在与代理不同的环境中运行的任何部署都很有用（网络隔离、E2EE 要求、资源约束）。

:::tip
会话连续性通过 `X-Hermes-Session-Id` 标头维护。主机的 API 服务器通过此 ID 跟踪会话，因此对话在消息之间持续存在，就像使用本地代理一样。
:::

:::note
**限制（v1）：** 来自远程代理的工具进度消息不会被中继回 — 用户只能看到流式最终响应，而不是单个工具调用。危险命令批准提示在主机端处理，而不是中继给 Matrix 用户。这些可以在未来的更新中解决。
:::

### 同步问题 / 机器人落后

**原因**：长时间运行的工具执行可能会延迟同步循环，或者 homeserver 速度慢。

**修复**：同步循环在错误时每 5 秒自动重试。检查 Hermes 日志中的同步相关警告。如果机器人持续落后，确保您的 homeserver 有足够的资源。

### 机器人离线

**原因**：Hermes 网关未运行，或连接失败。

**修复**：检查 `hermes gateway` 是否正在运行。查看终端输出中的错误消息。常见问题：错误的 homeserver URL、过期的访问令牌、homeserver 无法访问。

### "User not allowed" / 机器人忽略您

**原因**：您的用户 ID 不在 `MATRIX_ALLOWED_USERS` 中。

**修复**：将您的用户 ID 添加到 `~/.hermes/.env` 中的 `MATRIX_ALLOWED_USERS` 并重启网关。使用完整的 `@user:server` 格式。

## 安全性

:::warning
始终设置 `MATRIX_ALLOWED_USERS` 以限制谁可以与机器人交互。没有它，网关默认拒绝所有用户作为安全措施。只添加您信任的用户 ID — 授权用户可以完全访问代理的功能，包括工具使用和系统访问。
:::

有关保护 Hermes Agent 部署的更多信息，请参阅 [安全指南](../security.md)。

## 注意事项

- **任何 homeserver**：适用于 Synapse、Conduit、Dendrite、matrix.org 或任何符合规范的 Matrix homeserver。不需要特定的 homeserver 软件。
- **联邦**：如果您在联邦 homeserver 上，机器人可以与来自其他服务器的用户通信 — 只需将他们的完整 `@user:server` ID 添加到 `MATRIX_ALLOWED_USERS`。
- **自动加入**：机器人自动接受房间邀请并加入。加入后立即开始响应。
- **媒体支持**：Hermes 可以发送和接收图像、音频、视频和文件附件。媒体通过 Matrix 内容存储库 API 上传到您的 homeserver。
- **原生语音消息 (MSC3245)**：Matrix 适配器自动为传出的语音消息添加 `org.matrix.msc3245.voice` 标志。这意味着 TTS 响应和语音音频在 Element 和其他支持 MSC3245 的客户端中呈现为**原生语音气泡**，而不是通用音频文件附件。带有 MSC3245 标志的传入语音消息也会被正确识别并路由到语音转文本转录。不需要配置 — 这会自动工作。