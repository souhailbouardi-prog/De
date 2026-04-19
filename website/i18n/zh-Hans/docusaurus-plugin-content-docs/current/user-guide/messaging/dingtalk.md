---
sidebar_position: 10
title: "DingTalk"
description: "将 Hermes Agent 设置为钉钉聊天机器人"
---

# 钉钉设置

Hermes Agent 作为聊天机器人集成到钉钉中，让您通过直接消息或群聊与您的 AI 助手聊天。机器人通过钉钉的 Stream Mode 连接 — 一个长寿命的 WebSocket 连接，不需要公共 URL 或 webhook 服务器 — 并通过钉钉的会话 webhook API 使用 markdown 格式的消息回复。

在设置之前，这里是大多数人想知道的：Hermes 在您的钉钉工作区中的行为。

## Hermes 的行为

| 上下文 | 行为 |
|---------|----------|
| **私聊（1:1 聊天）** | Hermes 响应每条消息。不需要 `@提及`。每个私聊都有自己的会话。 |
| **群聊** | 当您 `@提及` 它时，Hermes 会响应。没有提及，Hermes 会忽略消息。 |
| **与多个用户共享群聊** | 默认情况下，Hermes 在群内为每个用户隔离会话历史记录。两个人在同一个群聊中交谈不会共享一个转录本，除非您明确禁用它。 |

### 钉钉中的会话模型

默认情况下：

- 每个私聊获得自己的会话
- 共享群聊中的每个用户在该群内获得自己的会话

这由 `config.yaml` 控制：

```yaml
group_sessions_per_user: true
```

只有当您明确希望整个群聊有一个共享对话时，才将其设置为 `false`：

```yaml
group_sessions_per_user: false
```

本指南引导您完成完整的设置过程 — 从创建钉钉机器人到发送第一条消息。

## 先决条件

安装所需的 Python 包：

```bash
pip install dingtalk-stream httpx
```

- `dingtalk-stream` — 钉钉官方的 Stream Mode SDK（基于 WebSocket 的实时消息传递）
- `httpx` — 用于通过会话 webhook 发送回复的异步 HTTP 客户端

## 步骤 1：创建钉钉应用

1. 前往 [钉钉开发者控制台](https://open-dev.dingtalk.com/)。
2. 使用您的钉钉管理员账户登录。
3. 点击 **应用开发** → **自定义应用** → **通过 H5 微应用创建应用**（或根据您的控制台版本选择 **机器人**）。
4. 填写：
   - **应用名称**：例如，`Hermes Agent`
   - **描述**：可选
5. 创建后，导航到 **凭证与基础信息** 以找到您的 **Client ID**（AppKey）和 **Client Secret**（AppSecret）。复制两者。

:::warning[凭证只显示一次]
Client Secret 仅在创建应用时显示一次。如果您丢失了它，需要重新生成。永远不要公开分享这些凭证或将其提交到 Git。
:::

## 步骤 2：启用机器人能力

1. 在您的应用设置页面中，前往 **添加能力** → **机器人**。
2. 启用机器人能力。
3. 在 **消息接收模式** 下，选择 **Stream Mode**（推荐 — 不需要公共 URL）。

:::tip
Stream Mode 是推荐的设置。它使用从您的机器发起的长寿命 WebSocket 连接，因此您不需要公共 IP、域名或 webhook 端点。这在 NAT、防火墙后面和本地机器上都能工作。
:::

## 步骤 3：查找您的钉钉用户 ID

Hermes Agent 使用您的钉钉用户 ID 来控制谁可以与机器人交互。钉钉用户 ID 是由您组织的管理员设置的字母数字字符串。

要找到您的：

1. 询问您的钉钉组织管理员 — 用户 ID 在钉钉管理控制台的 **通讯录** → **成员** 下配置。
2. 或者，机器人会记录每条传入消息的 `sender_id`。启动网关，向机器人发送消息，然后在日志中检查您的 ID。

## 步骤 4：配置 Hermes Agent

### 选项 A：交互式设置（推荐）

运行引导设置命令：

```bash
hermes gateway setup
```

当提示时选择 **DingTalk**，然后在询问时粘贴您的 Client ID、Client Secret 和允许的用户 ID。

### 选项 B：手动配置

将以下内容添加到您的 `~/.hermes/.env` 文件：

```bash
# 必需
DINGTALK_CLIENT_ID=your-app-key
DINGTALK_CLIENT_SECRET=your-app-secret

# 安全：限制谁可以与机器人交互
DINGTALK_ALLOWED_USERS=user-id-1

# 多个允许的用户（逗号分隔）
# DINGTALK_ALLOWED_USERS=user-id-1,user-id-2
```

`~/.hermes/config.yaml` 中的可选行为设置：

```yaml
group_sessions_per_user: true
```

- `group_sessions_per_user: true` 在共享群聊中保持每个参与者的上下文隔离

### 启动网关

配置完成后，启动钉钉网关：

```bash
hermes gateway
```

机器人应该在几秒钟内连接到钉钉的 Stream Mode。向它发送消息 — 无论是私聊还是在已添加它的群聊中 — 进行测试。

:::tip
您可以在后台或作为 systemd 服务运行 `hermes gateway` 以实现持久操作。有关详细信息，请参阅部署文档。
:::

## 故障排除

### 机器人不响应消息

**原因**：机器人能力未启用，或者 `DINGTALK_ALLOWED_USERS` 不包含您的用户 ID。

**解决方法**：验证您的应用设置中是否启用了机器人能力，并选择了 Stream Mode。检查您的用户 ID 是否在 `DINGTALK_ALLOWED_USERS` 中。重启网关。

### "dingtalk-stream not installed" 错误

**原因**：未安装 `dingtalk-stream` Python 包。

**解决方法**：安装它：

```bash
pip install dingtalk-stream httpx
```

### "DINGTALK_CLIENT_ID and DINGTALK_CLIENT_SECRET required"

**原因**：凭证未在您的环境或 `.env` 文件中设置。

**解决方法**：验证 `DINGTALK_CLIENT_ID` 和 `DINGTALK_CLIENT_SECRET` 在 `~/.hermes/.env` 中设置正确。Client ID 是您的 AppKey，Client Secret 是您从钉钉开发者控制台获得的 AppSecret。

### 流断开连接 / 重连循环

**原因**：网络不稳定、钉钉平台维护或凭证问题。

**解决方法**：适配器使用指数退避自动重连（2s → 5s → 10s → 30s → 60s）。检查您的凭证是否有效，您的应用是否未被停用。验证您的网络允许出站 WebSocket 连接。

### 机器人离线

**原因**：Hermes 网关未运行，或连接失败。

**解决方法**：检查 `hermes gateway` 是否在运行。查看终端输出以获取错误消息。常见问题：错误的凭证、应用被停用、未安装 `dingtalk-stream` 或 `httpx`。

### "No session_webhook available"

**原因**：机器人尝试回复但没有会话 webhook URL。这通常发生在 webhook 过期或机器人在接收消息和发送回复之间重启的情况下。

**解决方法**：向机器人发送新消息 — 每条传入消息都会提供一个用于回复的新会话 webhook。这是钉钉的正常限制；机器人只能回复它最近收到的消息。

## 安全性

:::warning
始终设置 `DINGTALK_ALLOWED_USERS` 以限制谁可以与机器人交互。没有它，网关默认拒绝所有用户作为安全措施。只添加您信任的人的用户 ID — 授权用户可以完全访问智能体的功能，包括工具使用和系统访问。
:::

有关保护您的 Hermes Agent 部署的更多信息，请参阅 [安全指南](../security.md)。

## 注意事项

- **Stream Mode**：不需要公共 URL、域名或 webhook 服务器。连接通过 WebSocket 从您的机器发起，因此在 NAT 和防火墙后面也能工作。
- **Markdown 响应**：回复使用钉钉的 markdown 格式进行富文本显示。
- **消息去重**：适配器使用 5 分钟窗口对消息进行去重，以防止重复处理相同的消息。
- **自动重连**：如果流连接断开，适配器会使用指数退避自动重连。
- **消息长度限制**：每条消息的响应上限为 20,000 字符。较长的响应会被截断。