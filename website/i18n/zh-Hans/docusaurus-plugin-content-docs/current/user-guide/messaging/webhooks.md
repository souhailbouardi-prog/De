---
sidebar_position: 13
title: "Webhooks"
description: "接收来自 GitHub、GitLab 和其他服务的事件以触发 Hermes 智能体运行"
---

# Webhooks

接收来自外部服务（GitHub、GitLab、JIRA、Stripe 等）的事件并自动触发 Hermes 智能体运行。Webhook 适配器运行一个 HTTP 服务器，接受 POST 请求，验证 HMAC 签名，将有效载荷转换为智能体提示，并将响应路由回源或其他配置的平台。

智能体处理事件，可以通过在 PR 上发表评论、向 Telegram/Discord 发送消息或记录结果来响应。

---

## 快速开始

1. 通过 `hermes gateway setup` 或环境变量启用
2. 在 `config.yaml` 中定义路由 **或** 使用 `hermes webhook subscribe` 动态创建它们
3. 将您的服务指向 `http://your-server:8644/webhooks/<route-name>`

---

## 设置

有两种方法可以启用 webhook 适配器。

### 通过设置向导

```bash
hermes gateway setup
```

按照提示启用 webhook，设置端口，并设置全局 HMAC 密钥。

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

路由定义了如何处理不同的 webhook 源。每个路由都是 `config.yaml` 中 `platforms.webhook.extra.routes` 下的命名条目。

### 路由属性

| 属性 | 必需 | 描述 |
|----------|----------|-------------|
| `events` | 否 | 要接受的事件类型列表（例如 `["pull_request"]`）。如果为空，接受所有事件。事件类型从 `X-GitHub-Event`、`X-GitLab-Event` 或有效载荷中的 `event_type` 读取。 |
| `secret` | **是** | 用于签名验证的 HMAC 密钥。如果未在路由上设置，则回退到全局 `secret`。仅用于测试时设置为 `"INSECURE_NO_AUTH"`（跳过验证）。 |
| `prompt` | 否 | 带有点表示法有效载荷访问的模板字符串（例如 `{pull_request.title}`）。如果省略，完整的 JSON 有效载荷将被转储到提示中。 |
| `skills` | 否 | 为智能体运行加载的技能名称列表。 |
| `deliver` | 否 | 发送响应的位置：`github_comment`、`telegram`、`discord`、`slack`、`signal`、`sms`、`whatsapp`、`matrix`、`mattermost`、`homeassistant`、`email`、`dingtalk`、`feishu`、`wecom`、`weixin`、`bluebubbles`、`qqbot` 或 `log`（默认）。 |
| `deliver_extra` | 否 | 额外的传递配置 — 键取决于 `deliver` 类型（例如 `repo`、`pr_number`、`chat_id`）。值支持与 `prompt` 相同的 `{dot.notation}` 模板。 |

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
            审查这个拉取请求：
            仓库：{repository.full_name}
            PR #{number}：{pull_request.title}
            作者：{pull_request.user.login}
            URL：{pull_request.html_url}
            Diff URL：{pull_request.diff_url}
            动作：{action}
          skills: ["github-code-review"]
          deliver: "github_comment"
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{number}"
        deploy-notify:
          events: ["push"]
          secret: "deploy-secret"
          prompt: "新推送至 {repository.full_name} 分支 {ref}：{head_commit.message}"
          deliver: "telegram"
```

### 提示模板

提示使用点表示法访问 webhook 有效载荷中的嵌套字段：

- `{pull_request.title}` 解析为 `payload["pull_request"]["title"]`
- `{repository.full_name}` 解析为 `payload["repository"]["full_name"]`
- `{__raw__}` — 特殊令牌，将**整个有效载荷**作为缩进的 JSON 转储（在 4000 个字符处截断）。对于监控警报或智能体需要完整上下文的通用 webhook 很有用。
- 缺失的键保留为文字 `{key}` 字符串（无错误）
- 嵌套的字典和列表被 JSON 序列化并在 2000 个字符处截断

您可以将 `{__raw__}` 与常规模板变量混合使用：

```yaml
prompt: "PR #{pull_request.number} by {pull_request.user.login}：{__raw__}"
```

如果未为路由配置 `prompt` 模板，则整个有效载荷会以缩进的 JSON 形式转储（在 4000 个字符处截断）。

相同的点表示法模板在 `deliver_extra` 值中工作。

### 论坛主题传递

将 webhook 响应传递到 Telegram 时，您可以通过在 `deliver_extra` 中包含 `message_thread_id`（或 `thread_id`）来定位特定的论坛主题：

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

如果 `deliver_extra` 中未提供 `chat_id`，传递会回退到为目标平台配置的主频道。

---

## GitHub PR 审查（分步）{#github-pr-review}

本演练设置了对每个拉取请求的自动代码审查。

### 1. 在 GitHub 中创建 webhook

1. 转到您的仓库 → **Settings** → **Webhooks** → **Add webhook**
2. 将 **Payload URL** 设置为 `http://your-server:8644/webhooks/github-pr`
3. 将 **Content type** 设置为 `application/json`
4. 将 **Secret** 设置为与您的路由配置匹配（例如 `github-webhook-secret`）
5. 在 **Which events?** 下，选择 **Let me select individual events** 并勾选 **Pull requests**
6. 点击 **Add webhook**

### 2. 添加路由配置

将 `github-pr` 路由添加到您的 `~/.hermes/config.yaml`，如上面的示例所示。

### 3. 确保 `gh` CLI 已认证

`github_comment` 传递类型使用 GitHub CLI 发表评论：

```bash
gh auth login
```

### 4. 测试

在仓库上打开一个拉取请求。Webhook 触发，Hermes 处理事件，并在 PR 上发表审查评论。

---

## GitLab Webhook 设置 {#gitlab-webhook-setup}

GitLab webhook 工作方式类似，但使用不同的认证机制。GitLab 将密钥作为普通的 `X-Gitlab-Token` 头（精确字符串匹配，不是 HMAC）发送。

### 1. 在 GitLab 中创建 webhook

1. 转到您的项目 → **Settings** → **Webhooks**
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
            审查这个合并请求：
            项目：{project.path_with_namespace}
            MR !{object_attributes.iid}：{object_attributes.title}
            作者：{object_attributes.last_commit.author.name}
            URL：{object_attributes.url}
            动作：{object_attributes.action}
          deliver: "log"
```

---

## 传递选项 {#delivery-options}

`deliver` 字段控制智能体处理 webhook 事件后响应的去向。

| 传递类型 | 描述 |
|-------------|-------------|
| `log` | 将响应记录到网关日志输出。这是默认值，对于测试很有用。 |
| `github_comment` | 通过 `gh` CLI 将响应作为 PR/issue 评论发布。需要 `deliver_extra.repo` 和 `deliver_extra.pr_number`。`gh` CLI 必须在网关主机上安装并认证（`gh auth login`）。 |
| `telegram` | 将响应路由到 Telegram。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `discord` | 将响应路由到 Discord。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `slack` | 将响应路由到 Slack。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `signal` | 将响应路由到 Signal。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `sms` | 通过 Twilio 将响应路由到 SMS。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `whatsapp` | 将响应路由到 WhatsApp。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `matrix` | 将响应路由到 Matrix。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `mattermost` | 将响应路由到 Mattermost。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `homeassistant` | 将响应路由到 Home Assistant。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `email` | 将响应路由到 Email。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `dingtalk` | 将响应路由到 DingTalk。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `feishu` | 将响应路由到 Feishu/Lark。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `wecom` | 将响应路由到 WeCom。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `weixin` | 将响应路由到 Weixin（微信）。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |
| `bluebubbles` | 将响应路由到 BlueBubbles（iMessage）。使用主频道，或在 `deliver_extra` 中指定 `chat_id`。 |

对于跨平台传递，目标平台也必须在网关中启用和连接。如果 `deliver_extra` 中未提供 `chat_id`，响应将发送到该平台配置的主频道。

---

## 动态订阅（CLI）{#dynamic-subscriptions}

除了 `config.yaml` 中的静态路由外，您还可以使用 `hermes webhook` CLI 命令动态创建 webhook 订阅。这在智能体本身需要设置事件驱动的触发器时特别有用。

### 创建订阅

```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New issue #{issue.number}: {issue.title}\nBy: {issue.user.login}\n\n{issue.body}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789" \
  --description "Triage new GitHub issues"
```

这会返回 webhook URL 和自动生成的 HMAC 密钥。将您的服务配置为 POST 到该 URL。

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

### 动态订阅的工作原理

- 订阅存储在 `~/.hermes/webhook_subscriptions.json` 中
- webhook 适配器在每个传入请求上热重新加载此文件（受 mtime 限制，开销可忽略）
- 来自 `config.yaml` 的静态路由始终优先于具有相同名称的动态路由
- 动态订阅使用与静态路由相同的路由格式和功能（事件、提示模板、技能、传递）
- 无需重启网关 — 订阅后立即生效

### 智能体驱动的订阅

智能体可以在 `webhook-subscriptions` 技能的指导下通过终端工具创建订阅。要求智能体"为 GitHub issues 设置 webhook"，它将运行适当的 `hermes webhook subscribe` 命令。

---

## 安全性 {#security}

Webhook 适配器包括多个安全层：

### HMAC 签名验证

适配器使用适合每个源的方法验证传入的 webhook 签名：

- **GitHub**：`X-Hub-Signature-256` 头 — 带有 `sha256=` 前缀的 HMAC-SHA256 十六进制摘要
- **GitLab**：`X-Gitlab-Token` 头 — 纯密钥字符串匹配
- **通用**：`X-Webhook-Signature` 头 — 原始 HMAC-SHA256 十六进制摘要

如果配置了密钥但没有识别的签名头，请求将被拒绝。

### 密钥是必需的

每个路由都必须有密钥 — 要么直接在路由上设置，要么从全局 `secret` 继承。没有密钥的路由会导致适配器在启动时失败并显示错误。仅用于开发/测试，您可以将密钥设置为 `"INSECURE_NO_AUTH"` 以完全跳过验证。

### 速率限制

每个路由默认限制为**每分钟 30 个请求**（固定窗口）。全局配置：

```yaml
platforms:
  webhook:
    extra:
      rate_limit: 60  # 每分钟请求数
```

超过限制的请求会收到 `429 Too Many Requests` 响应。

### 幂等性

传递 ID（来自 `X-GitHub-Delivery`、`X-Request-ID` 或时间戳回退）缓存 **1 小时**。重复传递（例如 webhook 重试）会以 `200` 响应静默跳过，防止重复的智能体运行。

### 正文大小限制

超过 **1 MB** 的有效载荷在读取正文之前被拒绝。配置：

```yaml
platforms:
  webhook:
    extra:
      max_body_bytes: 2097152  # 2 MB
```

### 提示注入风险

:::warning
Webhook 有效载荷包含攻击者控制的数据 — PR 标题、提交消息、问题描述等都可能包含恶意指令。当暴露在互联网上时，在沙盒环境（Docker、VM）中运行网关。考虑使用 Docker 或 SSH 终端后端进行隔离。
:::

---

## 故障排除 {#troubleshooting}

### Webhook 未到达

- 验证端口是否暴露并且可从 webhook 源访问
- 检查防火墙规则 — 端口 `8644`（或您配置的端口）必须打开
- 验证 URL 路径是否匹配：`http://your-server:8644/webhooks/<route-name>`
- 使用 `/health` 端点确认服务器正在运行

### 签名验证失败

- 确保路由配置中的密钥与 webhook 源中配置的密钥完全匹配
- 对于 GitHub，密钥是基于 HMAC 的 — 检查 `X-Hub-Signature-256`
- 对于 GitLab，密钥是纯令牌匹配 — 检查 `X-Gitlab-Token`
- 检查网关日志中的 `Invalid signature` 警告

### 事件被忽略

- 检查事件类型是否在路由的 `events` 列表中
- GitHub 事件使用 `pull_request`、`push`、`issues` 等值（`X-GitHub-Event` 头值）
- GitLab 事件使用 `merge_request`、`push` 等值（`X-GitLab-Event` 头值）
- 如果 `events` 为空或未设置，接受所有事件

### 智能体不响应

- 在前台运行网关查看日志：`hermes gateway run`
- 检查提示模板是否正确渲染
- 验证传递目标是否已配置并连接

### 重复响应

- 幂等性缓存应该防止这种情况 — 检查 webhook 源是否发送传递 ID 头（`X-GitHub-Delivery` 或 `X-Request-ID`）
- 传递 ID 缓存 1 小时

### `gh` CLI 错误（GitHub 评论传递）

- 在网关主机上运行 `gh auth login`
- 确保认证的 GitHub 用户对仓库有写权限
- 检查 `gh` 是否已安装并在 PATH 中

---

## 环境变量 {#environment-variables}

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `WEBHOOK_ENABLED` | 启用 webhook 平台适配器 | `false` |
| `WEBHOOK_PORT` | 用于接收 webhook 的 HTTP 服务器端口 | `8644` |
| `WEBHOOK_SECRET` | 全局 HMAC 密钥（当路由不指定自己的密钥时用作回退） | _(无)_ |