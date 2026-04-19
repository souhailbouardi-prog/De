---
sidebar_position: 14
title: "API 服务器"
description: "将 hermes-agent 作为兼容 OpenAI 的 API 暴露给任何前端"
---

# API 服务器

API 服务器将 hermes-agent 暴露为兼容 OpenAI 的 HTTP 端点。任何使用 OpenAI 格式的前端 —— Open WebUI、LobeChat、LibreChat、NextChat、ChatBox 以及数百个其他前端 —— 都可以连接到 hermes-agent 并将其用作后端。

您的代理使用其完整工具集（终端、文件操作、网络搜索、记忆、技能）处理请求并返回最终响应。在流式传输时，工具进度指示器会内联显示，以便前端可以显示代理正在做什么。

## 快速开始

### 1. 启用 API 服务器

添加到 `~/.hermes/.env`：

```bash
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
# 可选：仅当浏览器必须直接调用 Hermes 时
# API_SERVER_CORS_ORIGINS=http://localhost:3000
```

### 2. 启动网关

```bash
hermes gateway
```

您会看到：

```
[API Server] API server listening on http://127.0.0.1:8642
```

### 3. 连接前端

将任何兼容 OpenAI 的客户端指向 `http://localhost:8642/v1`：

```bash
# 使用 curl 测试
curl http://localhost:8642/v1/chat/completions \
  -H "Authorization: Bearer change-me-local-dev" \
  -H "Content-Type: application/json" \
  -d '{"model": "hermes-agent", "messages": [{"role": "user", "content": "Hello!"}]}'
```

或者连接 Open WebUI、LobeChat 或任何其他前端 —— 请参阅 [Open WebUI 集成指南](/docs/user-guide/messaging/open-webui) 获取分步说明。

## 端点

### POST /v1/chat/completions

标准 OpenAI 聊天完成格式。无状态 —— 完整对话通过 `messages` 数组包含在每个请求中。

**请求：**
```json
{
  "model": "hermes-agent",
  "messages": [
    {"role": "system", "content": "You are a Python expert."},
    {"role": "user", "content": "Write a fibonacci function"}
  ],
  "stream": false
}
```

**响应：**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "hermes-agent",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Here's a fibonacci function..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 50, "completion_tokens": 200, "total_tokens": 250}
}
```

**流式传输** (`"stream": true`)：返回带有逐令牌响应块的服务器发送事件 (SSE)。对于 **聊天完成**，流使用标准 `chat.completion.chunk` 事件加上 Hermes 的自定义 `hermes.tool.progress` 事件用于工具启动 UX。对于 **响应**，流使用 OpenAI 响应事件类型，如 `response.created`、`response.output_text.delta`、`response.output_item.added`、`response.output_item.done` 和 `response.completed`。

**流中的工具进度**：
- **聊天完成**：Hermes 发出 `event: hermes.tool.progress` 以提供工具启动可见性，而不会污染持久化的助手文本。
- **响应**：Hermes 在 SSE 流期间发出规范原生的 `function_call` 和 `function_call_output` 输出项，因此客户端可以实时渲染结构化工具 UI。

### POST /v1/responses

OpenAI 响应 API 格式。通过 `previous_response_id` 支持服务器端对话状态 —— 服务器存储完整的对话历史（包括工具调用和结果），因此多轮上下文得以保留，无需客户端管理。

**请求：**
```json
{
  "model": "hermes-agent",
  "input": "What files are in my project?",
  "instructions": "You are a helpful coding assistant.",
  "store": true
}
```

**响应：**
```json
{
  "id": "resp_abc123",
  "object": "response",
  "status": "completed",
  "model": "hermes-agent",
  "output": [
    {"type": "function_call", "name": "terminal", "arguments": "{\"command\": \"ls\"}", "call_id": "call_1"},
    {"type": "function_call_output", "call_id": "call_1", "output": "README.md src/ tests/"},
    {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Your project has..."}]}
  ],
  "usage": {"input_tokens": 50, "output_tokens": 200, "total_tokens": 250}
}
```

#### 使用 previous_response_id 进行多轮对话

链接响应以在轮次之间维护完整上下文（包括工具调用）：

```json
{
  "input": "Now show me the README",
  "previous_response_id": "resp_abc123"
}
```

服务器从存储的响应链中重建完整对话 —— 所有先前的工具调用和结果都被保留。链接的请求也共享同一个会话，因此多轮对话在仪表板和会话历史中显示为单个条目。

#### 命名对话

使用 `conversation` 参数而不是跟踪响应 ID：

```json
{"input": "Hello", "conversation": "my-project"}
{"input": "What's in src/?", "conversation": "my-project"}
{"input": "Run the tests", "conversation": "my-project"}
```

服务器自动链接到该对话中的最新响应。就像网关会话的 `/title` 命令一样。

### GET /v1/responses/{id}

通过 ID 检索先前存储的响应。

### DELETE /v1/responses/{id}

删除存储的响应。

### GET /v1/models

将代理列为可用模型。广告的模型名称默认为 [配置文件](/docs/user-guide/features/profiles) 名称（或默认配置文件的 `hermes-agent`）。大多数前端进行模型发现时需要此端点。

### GET /health

健康检查。返回 `{"status": "ok"}`。也可在 **GET /v1/health** 访问，用于期望 `/v1/` 前缀的兼容 OpenAI 的客户端。

## 系统提示处理

当前端发送 `system` 消息（聊天完成）或 `instructions` 字段（响应 API）时，hermes-agent **将其层叠** 在其核心系统提示之上。您的代理保留其所有工具、记忆和技能 —— 前端的系统提示添加额外的指令。

这意味着您可以按前端自定义行为而不丢失功能：
- Open WebUI 系统提示："You are a Python expert. Always include type hints."
- 代理仍然具有终端、文件工具、网络搜索、记忆等。

## 身份验证

通过 `Authorization` 标头进行 Bearer 令牌身份验证：

```
Authorization: Bearer ***
```

通过 `API_SERVER_KEY` 环境变量配置密钥。如果您需要浏览器直接调用 Hermes，还需要将 `API_SERVER_CORS_ORIGINS` 设置为显式允许列表。

:::warning 安全
API 服务器提供对 hermes-agent 工具集的完全访问权限，**包括终端命令**。当绑定到非环回地址（如 `0.0.0.0`）时，**需要** `API_SERVER_KEY`。还应保持 `API_SERVER_CORS_ORIGINS` 狭窄以控制浏览器访问。

默认绑定地址（`127.0.0.1`）仅用于本地使用。浏览器访问默认禁用；仅为明确的受信任来源启用它。
:::

## 配置

### 环境变量

| 变量 | 默认值 | 描述 |
|------|-------|------|
| `API_SERVER_ENABLED` | `false` | 启用 API 服务器 |
| `API_SERVER_PORT` | `8642` | HTTP 服务器端口 |
| `API_SERVER_HOST` | `127.0.0.1` | 绑定地址（默认仅本地主机） |
| `API_SERVER_KEY` | _(无)_ | 用于身份验证的 Bearer 令牌 |
| `API_SERVER_CORS_ORIGINS` | _(无)_ | 逗号分隔的允许浏览器来源 |
| `API_SERVER_MODEL_NAME` | _(配置文件名称)_ | `/v1/models` 上的模型名称。默认为配置文件名称，或默认配置文件的 `hermes-agent`。 |

### config.yaml

```yaml
# 尚未支持 — 使用环境变量。
# 未来版本将支持 config.yaml。
```

## 安全标头

所有响应都包含安全标头：
- `X-Content-Type-Options: nosniff` — 防止 MIME 类型嗅探
- `Referrer-Policy: no-referrer` — 防止引用者泄漏

## CORS

API 服务器默认**不**启用浏览器 CORS。

对于直接浏览器访问，设置显式允许列表：

```bash
API_SERVER_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

启用 CORS 时：
- **预检响应** 包含 `Access-Control-Max-Age: 600`（10 分钟缓存）
- **SSE 流式响应** 包含 CORS 标头，以便浏览器 EventSource 客户端正常工作
- **`Idempotency-Key`** 是允许的请求标头 — 客户端可以发送它进行重复数据删除（响应按密钥缓存 5 分钟）

大多数有文档的前端（如 Open WebUI）通过服务器到服务器连接，根本不需要 CORS。

## 兼容的前端

任何支持 OpenAI API 格式的前端都可以工作。已测试/记录的集成：

| 前端 | 星标 | 连接 |
|------|------|------|
| [Open WebUI](/docs/user-guide/messaging/open-webui) | 126k | 提供完整指南 |
| LobeChat | 73k | 自定义提供者端点 |
| LibreChat | 34k | librechat.yaml 中的自定义端点 |
| AnythingLLM | 56k | 通用 OpenAI 提供者 |
| NextChat | 87k | BASE_URL 环境变量 |
| ChatBox | 39k | API Host 设置 |
| Jan | 26k | 远程模型配置 |
| HF Chat-UI | 8k | OPENAI_BASE_URL |
| big-AGI | 7k | 自定义端点 |
| OpenAI Python SDK | — | `OpenAI(base_url="http://localhost:8642/v1")` |
| curl | — | 直接 HTTP 请求 |

## 使用配置文件的多用户设置

要为多个用户提供他们自己的隔离 Hermes 实例（单独的配置、记忆、技能），请使用 [配置文件](/docs/user-guide/features/profiles)：

```bash
# 为每个用户创建一个配置文件
hermes profile create alice
hermes profile create bob

# 为每个配置文件的 API 服务器配置不同的端口
hermes -p alice config set API_SERVER_ENABLED true
hermes -p alice config set API_SERVER_PORT 8643
hermes -p alice config set API_SERVER_KEY alice-secret

hermes -p bob config set API_SERVER_ENABLED true
hermes -p bob config set API_SERVER_PORT 8644
hermes -p bob config set API_SERVER_KEY bob-secret

# 启动每个配置文件的网关
hermes -p alice gateway &
hermes -p bob gateway &
```

每个配置文件的 API 服务器自动将配置文件名称作为模型 ID 进行广告：

- `http://localhost:8643/v1/models` → 模型 `alice`
- `http://localhost:8644/v1/models` → 模型 `bob`

在 Open WebUI 中，将每个添加为单独的连接。模型下拉菜单显示 `alice` 和 `bob` 作为不同的模型，每个都由完全隔离的 Hermes 实例支持。有关详细信息，请参阅 [Open WebUI 指南](/docs/user-guide/messaging/open-webui#multi-user-setup-with-profiles)。

## 限制

- **响应存储** — 存储的响应（用于 `previous_response_id`）保存在 SQLite 中，并在网关重启后仍然存在。最多 100 个存储的响应（LRU 淘汰）。
- **无文件上传** — 目前不支持通过 API 进行上传文件的视觉/文档分析。
- **模型字段是装饰性的** — 请求中的 `model` 字段被接受，但实际使用的 LLM 模型在服务器端的 config.yaml 中配置。

## 代理模式

API 服务器还作为 **网关代理模式** 的后端。当另一个 Hermes 网关实例配置为 `GATEWAY_PROXY_URL` 指向此 API 服务器时，它会将所有消息转发到这里，而不是运行自己的代理。这启用了拆分部署 — 例如，处理 Matrix E2EE 的 Docker 容器，转发到主机端代理。

有关完整设置指南，请参阅 [Matrix 代理模式](/docs/user-guide/messaging/matrix#proxy-mode-e2ee-on-macos)。