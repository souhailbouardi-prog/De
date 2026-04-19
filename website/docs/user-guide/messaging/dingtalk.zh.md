---
sidebar_position: 10
title: "钉钉"
description: "将Hermes Agent设置为钉钉聊天机器人"
---

# 钉钉设置

Hermes Agent 可以作为钉钉聊天机器人集成，让您通过直接消息或群聊与AI助手聊天。机器人通过钉钉的流式模式（Stream Mode）连接——这是一种不需要公共URL或webhook服务器的长连接WebSocket连接——并通过钉钉的会话webhook API使用markdown格式的消息回复。

在设置之前，这里是大多数人想知道的部分：一旦Hermes进入您的钉钉工作区，它的行为如何。

## Hermes 的行为

| 场景 | 行为 |
|---------|----------|
| **私聊（1:1聊天）** | Hermes 响应每条消息。不需要 `@提及`。每个私聊都有自己的会话。 |
| **群聊** | 当您 `@提及` 它时，Hermes 会响应。没有提及时，Hermes 会忽略消息。 |
| **多个用户的共享群** | 默认情况下，Hermes 在群内为每个用户隔离会话历史。同一群中的两个人不会共享一个对话记录，除非您明确禁用该功能。 |

### 钉钉中的会话模型

默认情况下：

- 每个私聊都有自己的会话
- 共享群聊中的每个用户在该群内都有自己的会话

这由 `config.yaml` 控制：

```yaml
group_sessions_per_user: true
```

只有当您明确希望整个群组共享一个对话时，才将其设置为 `false`：

```yaml
group_sessions_per_user: false
```

本指南将引导您完成完整的设置过程——从创建钉钉机器人到发送第一条消息。

## 前提条件

安装所需的Python包：

```bash
pip install "hermes-agent[dingtalk]"
```

或单独安装：

```bash
pip install dingtalk-stream httpx alibabacloud-dingtalk
```

- `dingtalk-stream` — 钉钉官方的流式模式SDK（基于WebSocket的实时消息）
- `httpx` — 用于通过会话webhook发送回复的异步HTTP客户端
- `alibabacloud-dingtalk` — 用于AI卡片、表情反应和媒体下载的钉钉开放API SDK

## 步骤1：创建钉钉应用

1. 访问 [钉钉开发者控制台](https://open-dev.dingtalk.com/)。
2. 使用您的钉钉管理员账户登录。
3. 点击 **应用开发** → **自定义应用** → **通过H5微应用创建应用**（或根据您的控制台版本选择 **机器人**）。
4. 填写：
   - **应用名称**：例如 `Hermes Agent`
   - **描述**：可选
5. 创建后，导航到 **凭证与基础信息** 找到您的 **Client ID**（AppKey）和 **Client Secret**（AppSecret）。复制两者。

:::warning[凭证仅显示一次]
Client Secret 仅在创建应用时显示一次。如果您丢失了它，需要重新生成。永远不要公开分享这些凭证或提交到Git。
:::

## 步骤2：启用机器人能力

1. 在应用的设置页面，转到 **添加能力** → **机器人**。
2. 启用机器人能力。
3. 在 **消息接收模式** 下，选择 **流式模式**（推荐 — 不需要公共URL）。

:::tip
流式模式是推荐的设置。它使用从您的机器发起的长连接WebSocket，因此您不需要公共IP、域名或webhook端点。这在NAT、防火墙和本地机器后都能工作。
:::

## 步骤3：查找您的钉钉用户ID

Hermes Agent 使用您的钉钉用户ID来控制谁可以与机器人交互。钉钉用户ID是由您组织的管理员设置的字母数字字符串。

要找到您的用户ID：

1. 询问您的钉钉组织管理员 — 用户ID在钉钉管理控制台的 **通讯录** → **成员** 下配置。
2. 或者，机器人会记录每条传入消息的 `sender_id`。启动网关，向机器人发送消息，然后在日志中查找您的ID。

## 步骤4：配置Hermes Agent

### 选项A：交互式设置（推荐）

运行引导设置命令：

```bash
hermes gateway setup
```

当提示时选择 **钉钉**。设置向导可以通过以下两种路径之一进行授权：

- **二维码设备流程（推荐）**。使用钉钉移动应用扫描终端中打印的二维码 — 您的Client ID和Client Secret会自动返回并写入 `~/.hermes/.env`。无需访问开发者控制台。
- **手动粘贴**。如果您已经有凭证（或二维码扫描不方便），在提示时粘贴您的Client ID、Client Secret和允许的用户ID。

:::note 关于openClaw品牌披露
由于钉钉的 `verification_uri_complete` 在API层硬编码为openClaw标识，QR目前在 `openClaw` 源字符串下授权，直到阿里巴巴/钉钉-Real-AI在服务器端注册Hermes特定模板。这纯粹是钉钉如何呈现同意屏幕的方式 — 您创建的机器人完全属于您，并且对您的租户是私有的。
:::

### 选项B：手动配置

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

- `group_sessions_per_user: true` 保持每个参与者的上下文在共享群聊中隔离

### 启动网关

配置完成后，启动钉钉网关：

```bash
hermes gateway
```

机器人应该在几秒钟内连接到钉钉的流式模式。向它发送消息 — 无论是私聊还是在已添加它的群组中 — 进行测试。

:::tip
您可以在后台运行 `hermes gateway` 或将其作为systemd服务运行以实现持久操作。有关详细信息，请参阅部署文档。
:::

## 功能

### AI卡片

Hermes可以使用钉钉AI卡片而不是普通的markdown消息进行回复。卡片提供更丰富、更结构化的显示，并支持在代理生成响应时进行流式更新。

要启用AI卡片，在 `config.yaml` 中配置卡片模板ID：

```yaml
platforms:
  dingtalk:
    enabled: true
    extra:
      card_template_id: "your-card-template-id"
```

您可以在钉钉开发者控制台的应用AI卡片设置下找到您的卡片模板ID。启用AI卡片后，所有回复都将作为带有流式文本更新的卡片发送。

### 表情反应

Hermes会自动向您的消息添加表情反应，以显示处理状态：

- 🤔思考中 — 当机器人开始处理您的消息时添加
- 🥳完成 — 当响应完成时添加（替换思考中的反应）

这些反应在私聊和群聊中都有效。

### 显示设置

您可以独立于其他平台自定义钉钉的显示行为：

```yaml
display:
  platforms:
    dingtalk:
      show_reasoning: false   # 在回复中显示模型推理/思考
      streaming: true         # 启用流式响应（与AI卡片配合使用）
      tool_progress: all      # 显示工具执行进度（all/new/off）
      interim_assistant_messages: true  # 显示中间评论消息
```

要禁用工具进度和中间消息以获得更干净的体验：

```yaml
display:
  platforms:
    dingtalk:
      tool_progress: off
      interim_assistant_messages: false
```

## 故障排除

### 机器人不响应消息

**原因**：机器人能力未启用，或者 `DINGTALK_ALLOWED_USERS` 不包含您的用户ID。

**解决方法**：验证机器人能力在应用设置中已启用，并且已选择流式模式。检查您的用户ID是否在 `DINGTALK_ALLOWED_USERS` 中。重启网关。

### "dingtalk-stream not installed" 错误

**原因**：未安装 `dingtalk-stream` Python包。

**解决方法**：安装它：

```bash
pip install dingtalk-stream httpx
```

### "DINGTALK_CLIENT_ID and DINGTALK_CLIENT_SECRET required"

**原因**：凭证未在您的环境或 `.env` 文件中设置。

**解决方法**：验证 `DINGTALK_CLIENT_ID` 和 `DINGTALK_CLIENT_SECRET` 在 `~/.hermes/.env` 中设置正确。Client ID是您的AppKey，Client Secret是您从钉钉开发者控制台获得的AppSecret。

### 流断开/重连循环

**原因**：网络不稳定、钉钉平台维护或凭证问题。

**解决方法**：适配器会自动以指数退避方式重连（2秒 → 5秒 → 10秒 → 30秒 → 60秒）。检查您的凭证是否有效，以及您的应用是否未被停用。验证您的网络允许出站WebSocket连接。

### 机器人离线

**原因**：Hermes网关未运行，或连接失败。

**解决方法**：检查 `hermes gateway` 是否正在运行。查看终端输出中的错误消息。常见问题：凭证错误、应用被停用、未安装 `dingtalk-stream` 或 `httpx`。

### "No session_webhook available"

**原因**：机器人尝试回复但没有会话webhook URL。这通常发生在webhook过期或机器人在接收消息和发送回复之间重启时。

**解决方法**：向机器人发送新消息 — 每条传入消息都为回复提供新的会话webhook。这是钉钉的正常限制；机器人只能回复它最近收到的消息。

## 安全

:::warning
始终设置 `DINGTALK_ALLOWED_USERS` 以限制谁可以与机器人交互。如果没有设置，网关默认拒绝所有用户作为安全措施。只添加您信任的人的用户ID — 授权用户可以完全访问代理的功能，包括工具使用和系统访问。
:::

有关保护Hermes Agent部署的更多信息，请参阅 [安全指南](../security.md)。

## 注意事项

- **流式模式**：不需要公共URL、域名或webhook服务器。连接通过WebSocket从您的机器发起，因此它在NAT和防火墙后都能工作。
- **AI卡片**：可选择使用丰富的AI卡片而不是普通的markdown进行回复。通过 `card_template_id` 配置。
- **表情反应**：自动 🤔思考中/🥳完成 反应，用于显示处理状态。
- **Markdown回复**：回复以钉钉的markdown格式格式化，用于富文本显示。
- **媒体支持**：传入消息中的图像和文件会自动解析，并可以通过视觉工具处理。
- **消息去重**：适配器使用5分钟窗口对消息进行去重，以防止处理同一条消息两次。
- **自动重连**：如果流连接断开，适配器会自动以指数退避方式重连。
- **消息长度限制**：每条消息的回复限制为20,000个字符。较长的回复会被截断。