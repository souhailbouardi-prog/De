---
sidebar_position: 13
title: "Webhooks"
description: "接收来自GitHub、GitLab和其他服务的事件以触发Hermes代理运行"
---

# Webhooks

接收来自外部服务（GitHub、GitLab、JIRA、Stripe等）的事件并自动触发Hermes代理运行。Webhook适配器运行一个HTTP服务器，接受POST请求，验证HMAC签名，将有效负载转换为代理提示，并将响应路由回源或其他配置的平台。

代理处理事件并可以通过在PR上发表评论、向Telegram/Discord发送消息或记录结果来响应。

---

## 快速开始

1. 通过 `hermes gateway setup` 或环境变量启用
2. 在 `config.yaml` 中定义路由 **或** 使用 `hermes webhook subscribe` 动态创建
3. 将您的服务指向 `http://your-server:8644/webhooks/<route-name>`

---

## 设置

有两种方法启用webhook适配器。

### 通过设置向导

```bash
hermes gateway setup
```

按照提示启用webhooks，设置端口，并设置全局HMAC密钥。

### 通过环境变量

添加到 `~/.hermes/.env`：

```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644        # 默认
WEBHOOK_SECRET=your-global-secret
```

### 验证服务器

网关运行后：

```bash
curl http://localhost:8644/health
```

预期响应：

```json
{"status": "ok", "platform": "webhook"}
```

---

## 配置路由 {#configuring-routes}

路由定义如何处理不同的webhook源。每个路由是 `config.yaml` 中 `platforms.webhook.extra.routes` 下的命名条目。

### 路由属性

| 属性 | 必需 | 描述 |
|----------|----------|-------------|
| `events` | 否 | 要接受的事件类型列表（例如 `["pull_request"]`）。如果为空，接受所有事件。事件类型从 `X-GitHub-Event`、`X-GitLab-Event` 或有效负载中的 `event_type` 读取。 |
| `secret` | **是** | 用于签名验证的HMAC密钥。如果未在路由上设置，则回退到全局 `secret`。仅用于测试时设置为 `"INSECURE_NO_AUTH"`（跳过验证）。 |
| `prompt` | 否 | 带有点表示法有效负载访问的模板字符串（例如 `{pull_request.title}`）。如果省略，完整的JSON有效负载会被转储到提示中。 |
| `skills` | 否 | 为代理运行加载的技能名称列表。 |
| `deliver` | 否 | 发送响应的位置：`github_comment`、`telegram`、`discord`、`slack`、`signal`、`sms`、`whatsapp`、`matrix`、`mattermost`、`homeassistant`、`email`、`dingtalk`、`feishu`、`wecom`、`weixin`、`bluebubbles`、`qqbot` 或 `log`（默认）。 |
| `deliver_extra` | 否 | 额外的交付配置 — 键取决于 `deliver` 类型（例如 `repo`、`pr_number`、`chat_id`）。值支持与 `prompt` 相同的 `{dot.notation}` 模板。 |

### 完整示例

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "global-fallback-secret"
      routes:
        github-pr:
          events: ["pull_request"]
          secret: "github-webhook-secret"
          prompt: |
            审查此拉取请求：
            仓库：{repository.full_name}
            PR #{number}：{pull_request.title}
            作者：{pull_request.user.login}
            URL：{pull_request.html_url}
            差异URL：{pull_request.diff_url}
            操作：{action}
          skills: ["github-code-review"]
          deliver: "github_comment"
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{number}"
        deploy-notify:
          events: ["push"]
          secret: "deploy-secret"
          prompt: "新的推送至 {repository.full_name} 分支 {ref}：{head_commit.message}"
          deliver: "telegram"
```

### 提示模板

提示使用点表示法访问webhook有效负载中的嵌套字段：

- `{pull_request.title}` 解析为 `payload["pull_request"]["title"]`
- `{repository.full_name}` 解析为 `payload["repository"]["full_name"]`
- `{__raw__}` — 特殊令牌，将**整个有效负载**作为缩进的JSON转储（截断为4000字符）。对于监控警报或通用webhook，代理需要完整上下文时非常有用。
- 缺失的键保留为字面 `{key}` 字符串（无错误）
- 嵌套的字典和列表被JSON序列化并截断为2000字符

您可以将 `{__raw__}` 与常规模板变量混合使用：

```yaml
prompt: "PR #{pull_request.number} by {pull_request.user.login}：{__raw__}"
```

如果未为路由配置 `prompt` 模板，整个有效负载会被转储为缩进的JSON（截断为4000字符）。

相同的点表示法模板在 `deliver_extra` 值中也有效。

### 论坛主题交付

将webhook响应交付到Telegram时，您可以通过在 `deliver_extra` 中包含 `message_thread_id`（或 `thread_id`）来定位特定的论坛主题：

```yaml
webhooks:
  routes:
    alerts:
      events: ["alert"]
      prompt: "警报：{__raw__}"
      deliver: "telegram"
      deliver_extra:
        chat_id: "-1001234567890"
        message_thread_id: "42"
```

如果 `deliver_extra` 中未提供 `chat_id`，交付会回退到为目标平台配置的主频道。

---

## GitHub PR 审查（分步）{#github-pr-review}

本教程设置在每个拉取请求上的自动代码审查。

### 1. 在GitHub中创建webhook

1. 转到您的仓库 → **设置** → **Webhooks** → **添加webhook**
2. 将 **Payload URL** 设置为 `http://your-server:8644/webhooks/github-pr`
3. 将 **Content type** 设置为 `application/json`
4. 将 **Secret** 设置为与您的路由配置匹配（例如 `github-webhook-secret`）
5. 在 **Which events?** 下，选择 **Let me select individual events** 并检查 **Pull requests**
6. 点击 **Add webhook**

### 2. 添加路由配置

将 `github-pr` 路由添加到您的 `~/.hermes/config.yaml`，如上面的示例所示。

### 3. 确保 `gh` CLI 已认证

`github_comment` 交付类型使用GitHub CLI发表评论：

```bash
gh auth login
```

### 4. 测试

在仓库上打开一个拉取请求。Webhook触发，Hermes处理事件，并在PR上发表审查评论。

---

## GitLab Webhook设置 {#gitlab-webhook-setup}

GitLab webhooks的工作方式类似，但使用不同的认证机制。GitLab将密钥作为普通的 `X-Gitlab-Token` 头部发送（精确字符串匹配，不是HMAC）。

### 1. 在GitLab中创建webhook

1. 转到您的项目 → **设置** → **Webhooks**
2. 将 **URL** 设置为 `http://your-server:8644/webhooks/gitlab-mr`
3. 输入您的 **Secret token**
4. 选择 **Merge request events**（以及您想要的任何其他事件）
5. 点击 **Add webhook**

### 2. 添加路由配置

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      routes:
        gitlab-mr:
          events: ["merge_request"]
          secret: "your-gitlab-secret-token"
          prompt: |
            审查此合并请求：
            项目：{project.path_with_namespace}
            MR !{object_attributes.iid}：{object_attributes.title}
            作者：{object_attributes.last_commit.author.name}
            URL：{object_attributes.url}
            操作：{object_attributes.action}
          deliver: "log"
```

---

## 交付选项 {#delivery-options}

`deliver` 字段控制代理的响应在处理webhook事件后去向何处。

| 交付类型 | 描述 |
|-------------|-------------|
| `log` | 将响应记录到网关日志输出。这是默认值，对测试有用。 |
| `github_comment` | 通过 `gh` CLI将响应作为PR/issue评论发布。需要 `deliver_extra.repo` 和 `deliver_extra.pr_number`。`gh` CLI必须在网关主机上安装并认证（`gh auth login`）。 |
| `telegram` | 将响应路由到Telegram。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `discord` | 将响应路由到Discord。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `slack` | 将响应路由到Slack。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `signal` | 将响应路由到Signal。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `sms` | 通过Twilio将响应路由到SMS。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `whatsapp` | 将响应路由到WhatsApp。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `matrix` | 将响应路由到Matrix。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `mattermost` | 将响应路由到Mattermost。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `homeassistant` | 将响应路由到Home Assistant。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `email` | 将响应路由到Email。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `dingtalk` | 将响应路由到钉钉。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `feishu` | 将响应路由到飞书/Lark。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `wecom` | 将响应路由到企业微信。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `weixin` | 将响应路由到微信。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `bluebubbles` | 将响应路由到BlueBubbles (iMessage)。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |

对于跨平台交付，目标平台也必须在网关中启用和连接。如果 `deliver_extra` 中未提供 `chat_id`，响应会发送到该平台配置的主频道。

---

## 动态订阅（CLI）{#dynamic-subscriptions}

除了 `config.yaml` 中的静态路由外，您还可以使用 `hermes webhook` CLI命令动态创建webhook订阅。这在代理本身需要设置事件驱动触发器时特别有用。

### 创建订阅

```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New issue #{issue.number}: {issue.title}\nBy: {issue.user.login}\n\n{issue.body}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789" \
  --description "Triage new GitHub issues"
```

这会返回webhook URL和自动生成的HMAC密钥。配置您的服务POST到该URL。

### 列出订阅

```bash
hermes webhook list
```

### 删除订阅

```bash
hermes webhook remove github-issues
```

### 测试订阅

```bash
hermes webhook test github-issues
hermes webhook test github-issues --payload '{"issue": {"number": 42, "title": "Test"}}'
```

### 动态订阅如何工作

- 订阅存储在 `~/.hermes/webhook_subscriptions.json`
- Webhook适配器在每个传入请求上热重载此文件（mtime门控，开销可忽略）
- 来自 `config.yaml` 的静态路由始终优先于具有相同名称的动态路由
- 动态订阅使用与静态路由相同的路由格式和功能（事件、提示模板、技能、交付）
- 无需重启网关 — 订阅后立即生效

### 代理驱动的订阅

当由 `webhook-subscriptions` 技能引导时，代理可以通过终端工具创建订阅。要求代理"为GitHub issues设置webhook"，它会运行适当的 `hermes webhook subscribe` 命令。

---

## 安全性 {#security}

Webhook适配器包含多层安全措施：

### HMAC签名验证

适配器使用每个源的适当方法验证传入的webhook签名：

- **GitHub**：`X-Hub-Signature-256` 头部 — HMAC-SHA256十六进制摘要，前缀为 `sha256=`
- **GitLab**：`X-Gitlab-Token` 头部 — 普通密钥字符串匹配
- **通用**：`X-Webhook-Signature` 头部 — 原始HMAC-SHA256十六进制摘要

如果配置了密钥但不存在公认的签名头部，请求会被拒绝。

### 密钥是必需的

每个路由必须有一个密钥 — 要么直接在路由上设置，要么从全局 `secret` 继承。没有密钥的路由会导致适配器在启动时失败并报错。仅用于开发/测试时，您可以将密钥设置为 `"INSECURE_NO_AUTH"` 以完全跳过验证。

### 速率限制

每个路由默认限制为**每分钟30个请求**（固定窗口）。全局配置：

```yaml
platforms:
  webhook:
    extra:
      rate_limit: 60  # 每分钟请求数
```

超过限制的请求会收到 `429 Too Many Requests` 响应。

### 幂等性

交付ID（来自 `X-GitHub-Delivery`、`X-Request-ID` 或时间戳回退）缓存**1小时**。重复交付（例如webhook重试）会被静默跳过，返回 `200` 响应，防止重复代理运行。

### 体大小限制

超过**1 MB**的有效负载在读取体之前被拒绝。配置：

```yaml
platforms:
  webhook:
    extra:
      max_body_bytes: 2097152  # 2 MB
```

### 提示注入风险

:::warning
Webhook有效负载包含攻击者控制的数据 — PR标题、提交消息、issue描述等都可能包含恶意指令。当暴露在互联网上时，在沙盒环境（Docker、VM）中运行网关。考虑使用Docker或SSH终端后端进行隔离。
:::

---

## 故障排除 {#troubleshooting}

### Webhook未到达

- 验证端口是否暴露且可从webhook源访问
- 检查防火墙规则 — 端口 `8644`（或您配置的端口）必须开放
- 验证URL路径匹配：`http://your-server:8644/webhooks/<route-name>`
- 使用 `/health` 端点确认服务器正在运行

### 签名验证失败

- 确保路由配置中的密钥与webhook源中配置的密钥完全匹配
- 对于GitHub，密钥是基于HMAC的 — 检查 `X-Hub-Signature-256`
- 对于GitLab，密钥是普通令牌匹配 — 检查 `X-Gitlab-Token`
- 检查网关日志中的 `Invalid signature` 警告

### 事件被忽略

- 检查事件类型是否在路由的 `events` 列表中
- GitHub事件使用如 `pull_request`、`push`、`issues` 等值（`X-GitHub-Event` 头部值）
- GitLab事件使用如 `merge_request`、`push` 等值（`X-GitLab-Event` 头部值）
- 如果 `events` 为空或未设置，接受所有事件

### 代理无响应

- 在前台运行网关查看日志：`hermes gateway run`
- 检查提示模板是否正确渲染
- 验证交付目标已配置并连接

### 重复响应

- 幂等性缓存应防止这种情况 — 检查webhook源是否发送交付ID头部（`X-GitHub-Delivery` 或 `X-Request-ID`）
- 交付ID缓存1小时

### `gh` CLI错误（GitHub评论交付）

- 在网关主机上运行 `gh auth login`
- 确保认证的GitHub用户对仓库有写入权限
- 检查 `gh` 是否已安装并在PATH中

---

## 环境变量 {#environment-variables}

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `WEBHOOK_ENABLED` | 启用webhook平台适配器 | `false` |
| `WEBHOOK_PORT` | 用于接收webhooks的HTTP服务器端口 | `8644` |
| `WEBHOOK_SECRET` | 全局HMAC密钥（当路由未指定自己的密钥时用作回退） | _(无)_ |