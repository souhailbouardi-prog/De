---
sidebar_position: 4
title: "MCP (模型上下文协议)"
description: "通过 MCP 将 Hermes Agent 连接到外部工具服务器 — 并精确控制 Hermes 加载哪些 MCP 工具"
---

# MCP (模型上下文协议)

MCP 允许 Hermes Agent 连接到外部工具服务器，这样智能体就可以使用 Hermes 本身之外的工具 — GitHub、数据库、文件系统、浏览器栈、内部 API 等。

如果您曾经希望 Hermes 使用已经存在于其他地方的工具，MCP 通常是最干净的实现方式。

## MCP 为您提供什么

- 无需先编写原生 Hermes 工具即可访问外部工具生态系统
- 在同一配置中使用本地 stdio 服务器和远程 HTTP MCP 服务器
- 启动时自动发现和注册工具
- 当服务器支持时，为 MCP 资源和提示提供实用程序包装器
- 每服务器过滤，因此您可以只暴露您实际希望 Hermes 看到的 MCP 工具

## 快速开始

1. 安装 MCP 支持（如果您使用标准安装脚本，已包含）：

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

2. 在 `~/.hermes/config.yaml` 中添加 MCP 服务器：

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

3. 启动 Hermes：

```bash
hermes chat
```

4. 要求 Hermes 使用 MCP 支持的功能。

例如：

```
List the files in /home/user/projects and summarize the repository structure.
```

Hermes 会发现 MCP 服务器的工具并像使用其他工具一样使用它们。

## 两种类型的 MCP 服务器

### Stdio 服务器

Stdio 服务器作为本地子进程运行并通过 stdin/stdout 通信。

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
```

Use stdio servers when:
- The server is installed locally
- You want low-latency access to local resources
- 您正在遵循显示 `command`、`args` 和 `env` 的 MCP 服务器文档

### HTTP 服务器

HTTP MCP 服务器是 Hermes 直接连接的远程端点。

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"
```

Use HTTP servers when:
- The MCP server is hosted elsewhere
- Your organization exposes internal MCP endpoints
- You don't want Hermes to spawn a local subprocess for that integration

## 基础配置参考

Hermes 从 `~/.hermes/config.yaml` 中的 `mcp_servers` 部分读取 MCP 配置。

### Common keys

| Key | Type | Meaning |
|---|---|---|
| `command` | string | stdio MCP 服务器的可执行文件 |
| `args` | list | stdio 服务器的参数 |
| `env` | mapping | 传递给 stdio 服务器的环境变量 |
| `url` | string | HTTP MCP 端点 |
| `headers` | mapping | 远程服务器的 HTTP 头 |
| `timeout` | number | 工具调用超时时间 |
| `connect_timeout` | number | 初始连接超时时间 |
| `enabled` | bool | 如果为 `false`，Hermes 会完全跳过该服务器 |
| `tools` | mapping | 每服务器工具过滤和实用程序策略 |

### 最小 stdio 示例

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

### 最小 HTTP 示例

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.internal.example.com"
    headers:
      Authorization: "Bearer ***"
```

## Hermes 如何注册 MCP 工具

Hermes 为 MCP 工具添加前缀，以避免与内置名称冲突：

```text
mcp_<server_name>_<tool_name>
```

示例：

| 服务器 | MCP 工具 | 注册名称 |
|---|---|---|
| `filesystem` | `read_file` | `mcp_filesystem_read_file` |
| `github` | `create-issue` | `mcp_github_create_issue` |
| `my-api` | `query.data` | `mcp_my_api_query_data` |

实际上，您通常不需要手动调用带前缀的名称 — Hermes 会在正常推理过程中看到工具并选择使用它。

## MCP 实用工具

当支持时，Hermes 还会围绕 MCP 资源和提示注册实用工具：

- `list_resources`
- `read_resource`
- `list_prompts`
- `get_prompt`

这些工具按服务器注册，使用相同的前缀模式，例如：

- `mcp_github_list_resources`
- `mcp_github_get_prompt`

### 重要

这些实用工具现在具有能力感知：
- 只有当 MCP 会话实际支持资源操作时，Hermes 才会注册资源实用程序
- 只有当 MCP 会话实际支持提示操作时，Hermes 才会注册提示实用程序

因此，一个暴露可调用工具但没有资源/提示的服务器不会获得这些额外的包装器。

## 每服务器过滤

您可以控制每个 MCP 服务器向 Hermes 贡献哪些工具，从而允许对工具命名空间进行细粒度管理。

### 完全禁用服务器

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

如果 `enabled: false`，Hermes 会完全跳过该服务器，甚至不会尝试连接。

### 白名单服务器工具

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [create_issue, list_issues]
```

只有那些 MCP 服务器工具会被注册。

### 黑名单服务器工具

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    tools:
      exclude: [delete_customer]
```

除了排除的工具外，所有服务器工具都会被注册。

### 优先级规则

如果两者都存在：

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

`include` 优先。

### 也过滤实用工具

您还可以单独禁用 Hermes 添加的实用程序包装器：

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```

这意味着：
- `tools.resources: false` 禁用 `list_resources` 和 `read_resource`
- `tools.prompts: false` 禁用 `list_prompts` 和 `get_prompt`

### 完整示例

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [create_issue, list_issues, search_code]
      prompts: false

  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer]
      resources: false

  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

## 如果所有内容都被过滤掉会发生什么？

如果您的配置过滤掉了所有可调用工具并禁用或省略了所有支持的实用程序，Hermes 不会为该服务器创建空的运行时 MCP 工具集。

这可以保持工具列表的整洁。

## 运行时行为

### 发现时间

Hermes 在启动时发现 MCP 服务器并将其工具注册到正常的工具注册表中。

### 动态工具发现

MCP 服务器可以通过发送 `notifications/tools/list_changed` 通知来在运行时通知 Hermes 其可用工具的变化。当 Hermes 收到此通知时，它会自动重新获取服务器的工具列表并更新注册表 — 无需手动 `/reload-mcp`。

这对于能力动态变化的 MCP 服务器非常有用（例如，当加载新数据库架构时添加工具，或当服务离线时删除工具的服务器）。

刷新受锁保护，因此来自同一服务器的快速通知不会导致重叠刷新。提示和资源变更通知（`prompts/list_changed`、`resources/list_changed`）会被接收但尚未采取行动。

### 重新加载

如果您更改了 MCP 配置，请使用：

```text
/reload-mcp
```

这会从配置重新加载 MCP 服务器并刷新可用工具列表。对于服务器本身推送的运行时工具变更，请参阅上面的[动态工具发现](#动态工具发现)。

### 工具集

每个配置的 MCP 服务器在贡献至少一个注册工具时还会创建一个运行时工具集：

```text
mcp-<server>
```

这使得在工具集级别更容易理解 MCP 服务器。

## 安全模型

### Stdio 环境过滤

对于 stdio 服务器，Hermes 不会盲目传递您的完整 shell 环境。

只有明确配置的 `env` 加上安全基线会被传递。这减少了意外的密钥泄露。

### 配置级暴露控制

新的过滤支持也是一种安全控制：
- 禁用您不希望模型看到的危险工具
- 只为敏感服务器暴露最小的白名单
- 当您不希望暴露该表面时，禁用资源/提示包装器

## 示例用例

### 具有最小问题管理表面的 GitHub 服务器

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue]
      prompts: false
      resources: false
```

使用方式：

```text
显示标有 bug 的未解决问题，然后为不稳定的 MCP 重新连接行为起草一个新问题。
```

### 移除危险操作的 Stripe 服务器

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

使用方式：

```text
查找最近 10 笔失败的付款并总结常见失败原因。
```

### 单个项目根目录的文件系统服务器

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

使用方式：

```text
检查项目根目录并解释目录布局。
```

## 故障排除

### MCP 服务器未连接

检查：

```bash
# 验证 MCP 依赖是否安装（标准安装中已包含）
cd ~/.hermes/hermes-agent && uv pip install -e ".[mcp]"

node --version
npx --version
```

然后验证您的配置并重启 Hermes。

### 工具未出现

可能的原因：
- 服务器连接失败
- 发现失败
- 您的过滤配置排除了工具
- 该服务器上不存在实用程序能力
- 服务器被 `enabled: false` 禁用

如果您有意过滤，这是预期的。

### 为什么资源或提示实用程序没有出现？

因为 Hermes 现在只有在以下两个条件都为真时才会注册这些包装器：
1. 您的配置允许它们
2. 服务器会话实际支持该能力

这是有意的，可以保持工具列表的真实性。

## MCP 采样支持

MCP 服务器可以通过 `sampling/createMessage` 协议向 Hermes 请求 LLM 推理。这允许 MCP 服务器请求 Hermes 代表它生成文本 — 对于需要 LLM 能力但没有自己的模型访问权限的服务器很有用。

采样默认对所有 MCP 服务器启用（当 MCP SDK 支持时）。在每个服务器的 `sampling` 键下配置：

```yaml
mcp_servers:
  my_server:
    command: "my-mcp-server"
    sampling:
      enabled: true            # 启用采样（默认：true）
      model: "openai/gpt-4o"  # 覆盖采样请求的模型（可选）
      max_tokens_cap: 4096     # 每个采样响应的最大令牌数（默认：4096）
      timeout: 30              # 每个请求的超时时间（秒）（默认：30）
      max_rpm: 10              # 速率限制：每分钟最大请求数（默认：10）
      max_tool_rounds: 5       # 采样循环中的最大工具使用轮数（默认：5）
      allowed_models: []       # 服务器可以请求的模型名称白名单（空 = 任何）
      log_level: "info"        # 审计日志级别：debug、info 或 warning（默认：info）
```

采样处理程序包括滑动窗口速率限制器、每请求超时和工具循环深度限制，以防止失控使用。指标（请求计数、错误、使用的令牌）按服务器实例跟踪。

要为特定服务器禁用采样：

```yaml
mcp_servers:
  untrusted_server:
    url: "https://mcp.example.com"
    sampling:
      enabled: false
```

## 将 Hermes 作为 MCP 服务器运行

除了连接到 MCP 服务器外，Hermes 还可以作为 MCP 服务器。这允许其他支持 MCP 的智能体（Claude Code、Cursor、Codex 或任何 MCP 客户端）使用 Hermes 的消息传递功能 — 列出对话、阅读消息历史记录，并在所有连接的平台上发送消息。

### 何时使用

- 您希望 Claude Code、Cursor 或其他编码智能体通过 Hermes 发送和阅读 Telegram/Discord/Slack 消息
- 您想要一个单一的 MCP 服务器，同时桥接到 Hermes 所有连接的消息传递平台
- 您已经有一个运行中的 Hermes 网关，连接了各种平台

### 快速开始

```bash
hermes mcp serve
```

这会启动一个 stdio MCP 服务器。MCP 客户端（不是您）管理进程生命周期。

### MCP 客户端配置

将 Hermes 添加到您的 MCP 客户端配置中。例如，在 Claude Code 的 `~/.claude/claude_desktop_config.json` 中：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

或者如果您在特定位置安装了 Hermes：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "/home/user/.hermes/hermes-agent/venv/bin/hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 可用工具

MCP 服务器公开 10 个工具，匹配 OpenClaw 的通道桥接表面加上 Hermes 特定的通道浏览器：

| 工具 | 描述 |
|------|-------------|
| `conversations_list` | 列出活动的消息传递对话。按平台过滤或按名称搜索。 |
| `conversation_get` | 通过会话键获取一个对话的详细信息。 |
| `messages_read` | 读取对话的最近消息历史记录。 |
| `attachments_fetch` | 从特定消息中提取非文本附件（图像、媒体）。 |
| `events_poll` | 轮询自游标位置以来的新对话事件。 |
| `events_wait` | 长轮询/阻塞直到下一个事件到达（近实时）。 |
| `messages_send` | 通过平台发送消息（例如 `telegram:123456`、`discord:#general`）。 |
| `channels_list` | 列出所有平台上可用的消息传递目标。 |
| `permissions_list_open` | 列出在此桥接会话期间观察到的待批准请求。 |
| `permissions_respond` | 允许或拒绝待批准请求。 |

### 事件系统

MCP 服务器包含一个实时事件桥，用于轮询 Hermes 的会话数据库以获取新消息。这使 MCP 客户端能够近实时地了解传入的对话：

```
# 轮询新事件（非阻塞）
events_poll(after_cursor=0)

# 等待下一个事件（最多阻塞超时时间）
events_wait(after_cursor=42, timeout_ms=30000)
```

事件类型：`message`、`approval_requested`、`approval_resolved`

事件队列在内存中，在桥接连接时启动。旧消息可通过 `messages_read` 获得。

### 选项

```bash
hermes mcp serve              # 正常模式
hermes mcp serve --verbose    # 在 stderr 上显示调试日志
```

### 工作原理

MCP 服务器直接从 Hermes 的会话存储（`~/.hermes/sessions/sessions.json` 和 SQLite 数据库）读取对话数据。后台线程轮询数据库以获取新消息并维护内存中的事件队列。对于发送消息，它使用与 Hermes 智能体本身相同的 `send_message` 基础架构。

网关不需要运行即可进行读取操作（列出对话、阅读历史记录、轮询事件）。发送操作确实需要网关运行，因为平台适配器需要活动连接。

### 当前限制

- 仅支持 stdio 传输（尚未支持 HTTP MCP 传输）
- 通过 mtime 优化的 DB 轮询以约 200ms 间隔进行事件轮询（文件未更改时跳过工作）
- 尚未实现 `claude/channel` 推送通知协议
- 仅支持文本发送（通过 `messages_send` 不支持媒体/附件发送）

## 相关文档

- [在 Hermes 中使用 MCP](/docs/guides/use-mcp-with-hermes)
- [CLI 命令](/docs/reference/cli-commands)
- [斜杠命令](/docs/reference/slash-commands)
- [常见问题](/docs/reference/faq)