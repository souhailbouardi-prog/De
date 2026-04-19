---
sidebar_position: 8
title: "Mattermost"
description: "将 Hermes Agent 设置为 Mattermost 机器人"
---

# Mattermost 设置

Hermes Agent 作为机器人与 Mattermost 集成，让您通过直接消息或团队频道与 AI 助手聊天。Mattermost 是一个自托管的开源 Slack 替代品 — 您在自己的基础设施上运行它，完全控制您的数据。机器人通过 Mattermost 的 REST API (v4) 和 WebSocket 连接以获取实时事件，通过 Hermes Agent 管道处理消息（包括工具使用、内存和推理），并实时响应。它支持文本、文件附件、图像和斜杠命令。

不需要外部 Mattermost 库 — 适配器使用 `aiohttp`，这已经是 Hermes 的依赖项。

在设置之前，这里是大多数人想知道的：Hermes 在您的 Mattermost 实例中如何行为。

## Hermes 的行为

| 上下文 | 行为 |
|---------|----------|
| **私聊** | Hermes 响应每条消息。不需要 `@提及`。每个私聊都有自己的会话。 |
| **公共/私有频道** | 当您 `@提及` 它时，Hermes 会响应。没有提及，Hermes 会忽略消息。 |
| **线程** | 如果 `MATTERMOST_REPLY_MODE=thread`，Hermes 会在您的消息下方的线程中回复。线程上下文与父频道隔离。 |
| **有多个用户的共享频道** | 默认情况下，Hermes 在频道内为每个用户隔离会话历史。除非您明确禁用，否则在同一个频道中交谈的两个人不会共享一个对话记录。 |

:::tip
如果您希望 Hermes 以线程对话方式回复（嵌套在您的原始消息下），请设置 `MATTERMOST_REPLY_MODE=thread`。默认值是 `off`，它在频道中发送扁平消息。
:::

### Mattermost 中的会话模型

默认情况下：

- 每个私聊获得自己的会话
- 每个线程获得自己的会话命名空间
- 共享频道中的每个用户在该频道内获得自己的会话

这由 `config.yaml` 控制：

```yaml
group_sessions_per_user: true
```

只有当您明确希望整个频道共享一个对话时，才将其设置为 `false`：

```yaml
group_sessions_per_user: false
```

共享会话对于协作频道很有用，但它们也意味着：

- 用户共享上下文增长和令牌成本
- 一个人的长工具任务可能会膨胀其他人的上下文
- 一个人的进行中运行可能会中断同一频道中另一个人的后续操作

本指南将引导您完成完整的设置过程 — 从在 Mattermost 上创建机器人到发送第一条消息。

## 步骤 1：启用机器人账户

在创建机器人之前，必须在 Mattermost 服务器上启用机器人账户。

1. 以**系统管理员**身份登录 Mattermost。
2. 前往 **系统控制台** → **集成** → **机器人账户**。
3. 将 **启用机器人账户创建** 设置为 **true**。
4. 点击 **保存**。

:::info
如果您没有系统管理员访问权限，请让您的 Mattermost 管理员启用机器人账户并为您创建一个。
:::

## 步骤 2：创建机器人账户

1. 在 Mattermost 中，点击 **☰** 菜单（左上角）→ **集成** → **机器人账户**。
2. 点击 **添加机器人账户**。
3. 填写详细信息：
   - **用户名**：例如 `hermes`
   - **显示名称**：例如 `Hermes Agent`
   - **描述**：可选
   - **角色**：`Member` 足够
4. 点击 **创建机器人账户**。
5. Mattermost 将显示**机器人令牌**。**立即复制它**。

:::warning[令牌只显示一次]
机器人令牌只在创建机器人账户时显示一次。如果您丢失了它，需要从机器人账户设置中重新生成。永远不要公开分享您的令牌或将其提交到 Git — 任何拥有此令牌的人都可以完全控制机器人。
:::

将令牌存储在安全的地方（例如密码管理器）。您将在步骤 5 中需要它。

:::tip
您也可以使用**个人访问令牌**而不是机器人账户。前往 **个人资料** → **安全** → **个人访问令牌** → **创建令牌**。如果您希望 Hermes 以您自己的用户身份而不是单独的机器人用户身份发帖，这很有用。
:::

## 步骤 3：将机器人添加到频道

机器人需要是您希望它响应的任何频道的成员：

1. 打开您希望机器人加入的频道。
2. 点击频道名称 → **添加成员**。
3. 搜索您的机器人用户名（例如 `hermes`）并添加它。

对于私聊，只需打开与机器人的直接消息 — 它将能够立即响应。

## 步骤 4：找到您的 Mattermost 用户 ID

Hermes Agent 使用您的 Mattermost 用户 ID 来控制谁可以与机器人交互。要找到它：

1. 点击您的**头像**（左上角）→ **个人资料**。
2. 您的用户 ID 显示在个人资料对话框中 — 点击它进行复制。

您的用户 ID 是一个 26 字符的字母数字字符串，如 `3uo8dkh1p7g1mfk49ear5fzs5c`。

:::warning
您的用户 ID**不是**您的用户名。用户名是 `@` 后面的内容（例如 `@alice`）。用户 ID 是 Mattermost 在内部使用的长字母数字标识符。
:::

**替代方法**：您也可以通过 API 获取用户 ID：

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-mattermost-server/api/v4/users/me | jq .id
```

:::tip
要获取**频道 ID**：点击频道名称 → **查看信息**。频道 ID 显示在信息面板中。如果您想手动设置主频道，您将需要这个。
:::

## 步骤 5：配置 Hermes Agent

### 选项 A：交互式设置（推荐）

运行引导设置命令：

```bash
hermes gateway setup
```

当提示时选择 **Mattermost**，然后在被询问时粘贴您的服务器 URL、机器人令牌和用户 ID。

### 选项 B：手动配置

将以下内容添加到您的 `~/.hermes/.env` 文件：

```bash
# 必需
MATTERMOST_URL=https://mm.example.com
MATTERMOST_TOKEN=***
MATTERMOST_ALLOWED_USERS=3uo8dkh1p7g1mfk49ear5fzs5c

# 多个允许的用户（逗号分隔）
# MATTERMOST_ALLOWED_USERS=3uo8dkh1p7g1mfk49ear5fzs5c,8fk2jd9s0a7bncm1xqw4tp6r3e

# 可选：回复模式（thread 或 off，默认：off）
# MATTERMOST_REPLY_MODE=thread

# 可选：无需 @提及即可响应（默认：true = 需要提及）
# MATTERMOST_REQUIRE_MENTION=false

# 可选：机器人无需 @提及即可响应的频道（逗号分隔的频道 ID）
# MATTERMOST_FREE_RESPONSE_CHANNELS=channel_id_1,channel_id_2
```

`~/.hermes/config.yaml` 中的可选行为设置：

```yaml
group_sessions_per_user: true
```

- `group_sessions_per_user: true` 保持每个参与者的上下文在共享频道和线程内隔离

### 启动网关

配置完成后，启动 Mattermost 网关：

```bash
hermes gateway
```

机器人应该在几秒钟内连接到您的 Mattermost 服务器。向它发送一条消息 — 无论是私聊还是在已添加它的频道中 — 进行测试。

:::tip
您可以在后台运行 `hermes gateway` 或作为 systemd 服务以实现持久操作。有关详细信息，请参阅部署文档。
:::

## 主频道

您可以指定一个 "主频道"，机器人会在其中发送主动消息（例如 cron 作业输出、提醒和通知）。有两种设置方法：

### 使用斜杠命令

在机器人所在的任何 Mattermost 频道中输入 `/sethome`。该频道成为主频道。

### 手动配置

添加到您的 `~/.hermes/.env`：

```bash
MATTERMOST_HOME_CHANNEL=abc123def456ghi789jkl012mn
```

将 ID 替换为实际的频道 ID（点击频道名称 → 查看信息 → 复制 ID）。

## 回复模式

`MATTERMOST_REPLY_MODE` 设置控制 Hermes 如何发布响应：

| 模式 | 行为 |
|------|----------|
| `off`（默认） | Hermes 在频道中发布扁平消息，就像普通用户一样。 |
| `thread` | Hermes 在您原始消息下方的线程中回复。当有大量来回对话时，保持频道整洁。 |

在您的 `~/.hermes/.env` 中设置：

```bash
MATTERMOST_REPLY_MODE=thread
```

## 提及行为

默认情况下，机器人只在 `@提及` 时在频道中响应。您可以更改此设置：

| 变量 | 默认值 | 描述 |
|----------|---------|-------------|
| `MATTERMOST_REQUIRE_MENTION` | `true` | 设置为 `false` 以响应频道中的所有消息（私聊始终有效）。 |
| `MATTERMOST_FREE_RESPONSE_CHANNELS` | _(无)_ | 逗号分隔的频道 ID，即使 require_mention 为 true，机器人也会在没有 `@提及` 的情况下响应。 |

要在 Mattermost 中找到频道 ID：打开频道，点击频道名称标题，然后在 URL 或频道详细信息中查找 ID。

当机器人被 `@提及` 时，提及会在处理前自动从消息中剥离。

## 故障排除

### 机器人不响应消息

**原因**：机器人不是频道的成员，或 `MATTERMOST_ALLOWED_USERS` 不包含您的用户 ID。

**修复**：将机器人添加到频道（频道名称 → 添加成员 → 搜索机器人）。验证您的用户 ID 是否在 `MATTERMOST_ALLOWED_USERS` 中。重启网关。

### 403 Forbidden 错误

**原因**：机器人令牌无效，或机器人没有在频道中发帖的权限。

**修复**：检查您的 `.env` 文件中的 `MATTERMOST_TOKEN` 是否正确。确保机器人账户未被停用。验证机器人已被添加到频道。如果使用个人访问令牌，确保您的账户具有所需的权限。

### WebSocket 断开连接 / 重连循环

**原因**：网络不稳定、Mattermost 服务器重启或 WebSocket 连接的防火墙/代理问题。

**修复**：适配器使用指数退避（2s → 60s）自动重连。检查您服务器的 WebSocket 配置 — 反向代理（nginx、Apache）需要配置 WebSocket 升级头。验证没有防火墙阻止您的 Mattermost 服务器上的 WebSocket 连接。

对于 nginx，确保您的配置包含：

```nginx
location /api/v4/websocket {
    proxy_pass http://mattermost-backend;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 600s;
}
```

### 启动时 "Failed to authenticate"

**原因**：令牌或服务器 URL 不正确。

**修复**：验证 `MATTERMOST_URL` 指向您的 Mattermost 服务器（包括 `https://`，无尾随斜杠）。检查 `MATTERMOST_TOKEN` 是否有效 — 尝试用 curl 测试：

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-server/api/v4/users/me
```

如果这返回您的机器人的用户信息，则令牌有效。如果返回错误，请重新生成令牌。

### 机器人离线

**原因**：Hermes 网关未运行，或连接失败。

**修复**：检查 `hermes gateway` 是否正在运行。查看终端输出中的错误消息。常见问题：错误的 URL、过期的令牌、Mattermost 服务器无法访问。

### "User not allowed" / 机器人忽略您

**原因**：您的用户 ID 不在 `MATTERMOST_ALLOWED_USERS` 中。

**修复**：将您的用户 ID 添加到 `~/.hermes/.env` 中的 `MATTERMOST_ALLOWED_USERS` 并重启网关。请记住：用户 ID 是一个 26 字符的字母数字字符串，而不是您的 `@username`。

## 按频道提示

为特定的 Mattermost 频道分配临时系统提示。提示在运行时每次轮次注入 — 从不持久化到对话历史 — 因此更改会立即生效。

```yaml
mattermost:
  channel_prompts:
    "channel_id_abc123": |
      你是一个研究助手。专注于学术来源、
      引用和简洁的综合。
    "channel_id_def456": |
      代码审查模式。精确关注边缘情况和
      性能影响。
```

键是 Mattermost 频道 ID（在频道 URL 或通过 API 找到）。匹配频道中的所有消息都会将提示作为临时系统指令注入。

## 安全性

:::warning
始终设置 `MATTERMOST_ALLOWED_USERS` 以限制谁可以与机器人交互。没有它，网关默认拒绝所有用户作为安全措施。只添加您信任的用户 ID — 授权用户可以完全访问代理的功能，包括工具使用和系统访问。
:::

有关保护 Hermes Agent 部署的更多信息，请参阅 [安全指南](../security.md)。

## 注意事项

- **自托管友好**：适用于任何自托管的 Mattermost 实例。不需要 Mattermost Cloud 账户或订阅。
- **无额外依赖**：适配器使用 `aiohttp` 进行 HTTP 和 WebSocket，这已经包含在 Hermes Agent 中。
- **Team Edition 兼容**：适用于 Mattermost Team Edition（免费）和 Enterprise Edition。