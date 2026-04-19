---
sidebar_position: 4
title: "MCP (模型上下文协议)"
description: "通过 MCP 将 Hermes Agent 连接到外部工具服务器 — 并精确控制 Hermes 加载哪些 MCP 工具"
---

# MCP (模型上下文协议)

MCP 让 Hermes Agent 连接到外部工具服务器，以便代理可以使用 Hermes 本身之外的工具 — GitHub、数据库、文件系统、浏览器堆栈、内部 API 等。

如果您曾经希望 Hermes 使用其他地方已存在的工具，MCP 通常是最干净的方法。

## MCP 给您带来什么

- 访问外部工具生态系统，而无需先编写原生 Hermes 工具
- 在同一配置中的本地 stdio 服务器和远程 HTTP MCP 服务器
- 启动时自动工具发现和注册
- 当服务器支持时，MCP 资源和提示的实用程序包装器
- 每服务器过滤，以便您可以仅公开您实际希望 Hermes 看到的 MCP 工具

## 快速开始

1. 安装 MCP 支持（如果您使用了标准安装脚本，则已包含）：

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

2. 将 MCP 服务器添加到 `~/.hermes/config.yaml`：

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

```text
List the files in /home/user/projects and summarize the repo structure.
```

Hermes 将发现 MCP 服务器的工具并像使用任何其他工具一样使用它们。

## 两种 MCP 服务器

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

在以下情况下使用 stdio 服务器：
- 服务器在本地安装
- 您想要对本地资源的低延迟访问
- 您正在遵循显示 `command`、`args` 和 `env` 的 MCP 服务器文档

### HTTP 服务器

HTTP MCP 服务器是 Hermes 直接连接到的远程端点。

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"
```

在以下情况下使用 HTTP 服务器：
- MCP 服务器托管在其他地方
- 您的组织公开内部 MCP 端点
- 您不希望 Hermes 为该集成生成本地子进程

## 基本配置参考

Hermes 从 `~/.hermes/config.yaml` 中的 `mcp_servers` 下读取 MCP 配置。

### 常用键

| 键 | 类型 | 含义 |
|---|---|---|
| `command` | string | stdio MCP 服务器的可执行文件 |
| `args` | list | stdio 服务器的参数 |
| `env` | mapping | 传递给 stdio 服务器的环境变量 |
| `url` | string | HTTP MCP 端点 |
| `headers` | mapping | 远程服务器的 HTTP 头 |
| `timeout` | number | 工具调用超时 |
| `connect_timeout` | number | 初始连接超时 |
| `enabled` | bool | 如果为 `false`，Hermes 会完全跳过服务器 |
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

Hermes 为 MCP 工具添加前缀，以便它们不会与内置名称冲突：

```text
mcp_<server_name>_<tool_name>
```

示例：

| 服务器 | MCP 工具 | 注册名称 |
|---|---|---|
| `filesystem` | `read_file` | `mcp_filesystem_read_file` |
| `github` | `create-issue` | `mcp_github_create_issue` |
| `my-api` | `query.data` | `mcp_my_api_query_data` |

实际上，您通常不需要手动调用带前缀的名称 — Hermes 会看到工具并在正常推理期间选择它。

## MCP 实用程序工具

当支持时，Hermes 还会围绕 MCP 资源和提示注册实用程序工具：

- `list_resources`
- `read_resource`
- `list_prompts`
- `get_prompt`

这些按服务器使用相同的前缀模式注册，例如：

- `mcp_github_list_resources`
- `mcp_github_get_prompt`

### 重要

这些实用程序工具现在是功能感知的：
- 仅当 MCP 会话实际支持资源操作时，Hermes 才会注册资源实用程序
- 仅当 MCP 会话实际支持提示操作时，Hermes 才会注册提示实用程序

因此，公开可调用工具但没有资源/提示的服务器不会获得那些额外的包装器。

## 每服务器过滤

您可以控制每个 MCP 服务器向 Hermes 贡献哪些工具，从而实现工具命名空间的细粒度管理。

### 完全禁用服务器

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

如果 `enabled: false`，Hermes 会完全跳过服务器，甚至不尝试连接。

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

仅注册那些 MCP 服务器工具。

### 黑名单服务器工具

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    tools:
      exclude: [delete_customer]
```

除排除的工具外，所有服务器工具都已注册。

### 优先级规则

如果两者都存在：

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

`include` 获胜。

### 也过滤实用程序工具

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

## 如果所有内容都被过滤掉会怎样？

如果您的配置过滤掉所有可调用工具并禁用或省略所有支持的实用程序，Hermes 不会为该服务器创建空的运行时 MCP 工具集。

这保持工具列表清洁。

## 运行时行为

### 发现时间

Hermes 在启动时发现 MCP 服务器并将其工具注册到正常工具注册表中。

### 动态工具发现

MCP 服务器可以在运行时通过发送 `notifications/tools/list_changed` 通知来通知 Hermes 其可用工具何时更改。当 Hermes 收到此通知时，它会自动重新获取服务器的工具列表并更新注册表 — 无需手动 `/reload-mcp`。

这对于功能动态更改的 MCP 服务器很有用（例如，当加载新数据库架构时添加工具的服务器，或当服务脱机时删除工具的服务器）。

刷新是受锁保护的，因此来自同一服务器的快速通知不会导致重叠刷新。提示和资源更改通知（`prompts/list_changed`、`resources/list_changed`）已接收但尚未采取行动。

### 重新加载

如果您更改 MCP 配置，请使用：

```text
/reload-mcp
```

这会从配置重新加载 MCP 服务器并刷新可用工具列表。对于服务器本身推送的运行时工具更改，请参阅上面的[动态工具发现](#动态工具发现)。

### 工具集

每个配置的 MCP 服务器在贡献至少一个注册工具时也会创建一个运行时工具集：

```text
mcp-<server>
```

这使 MCP 服务器在工具集级别更容易推理。

## 安全模型

### Stdio 环境过滤

对于 stdio 服务器，Hermes 不会盲目传递您的完整 shell 环境。

仅传递显式配置的 `env` 加上安全基线。这减少了意外的机密泄露。

### 配置级暴露控制

新的过滤支持也是一种安全控制：
- 禁用您不希望模型看到的危险工具
- 仅为敏感服务器公开最小白名单
- 当您不希望该表面暴露时，禁用资源/提示包装器

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

像这样使用它：

```text
Show me open issues labeled bug, then draft a new issue for the flaky MCP reconnection behavior.
```

### 删除了危险操作的 Stripe 服务器

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

像这样使用它：

```text
Look up the last 10 failed payments and summarize common failure reasons.
```

### 单个项目根目录的文件系统服务器

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

像这样使用它：

```text
Inspect the project root and explain the directory layout.
```

## 故障排除

### MCP 服务器未连接

检查：

```bash
# 验证 MCP 依赖项已安装（已包含在标准安装中）
cd ~/.hermes/hermes-agent && uv pip install -e ".[mcp]"

node --version
npx --version
```

然后验证您的配置并重启 Hermes。

### 工具未出现

可能的原因：
- 服务器连接失败
- 发现失败
- 您的过滤器配置排除了工具
- 该服务器上不存在实用程序功能
- 服务器使用 `enabled: false` 禁用

如果您有意过滤，这是预期的。

### 为什么资源或提示实用程序没有出现？

因为 Hermes 现在仅在两者都为真时才注册那些包装器：
1. 您的配置允许它们
2. 服务器会话实际支持该功能

这是有意的，并保持工具列表诚实。

## MCP 采样支持

MCP 服务器可以通过 `sampling/createMessage` 协议从 Hermes 请求 LLM 推理。这允许 MCP 服务器要求 Hermes 代表其生成文本 — 对于需要 LLM 功能但没有自己的模型访问权限的服务器很有用。

默认情况下，对所有 MCP 服务器**启用采样**（当 MCP SDK 支持时）。在 `sampling` 键下按服务器配置它：

```yaml
mcp_servers:
  my_server:
    command: "my-mcp-server"
    sampling:
      enabled: true            # 启用采样（默认：true）
      model: "openai/gpt-4o"  # 覆盖采样请求的模型（可选）
      max_tokens_cap: 4096     # 每个采样响应的最大 tokens（默认：4096）
      timeout: 30              # 每个请求的超时（秒）（默认：30）
      max_rpm: 10              # 速率限制：每分钟最大请求数（默认：10）
      max_tool_rounds: 5       # 采样循环中的最大工具使用回合（默认：5）
      allowed_models: []       # 服务器可能请求的模型名称白名单（空 = 任意）
      log_level: "info"        # 审计日志级别：debug、info 或 warning（默认：info）
```

采样处理程序包括滑动窗口速率限制器、每个请求的超时和工具循环深度限制，以防止失控使用。指标（请求计数、错误、使用的 tokens）按服务器实例跟踪。

要为特定服务器禁用采样：

```yaml
mcp_servers:
  untrusted_server:
    url: "https://mcp.example.com"
    sampling:
      enabled: false
```

## 将 Hermes 作为 MCP 服务器运行

除了连接**到** MCP 服务器之外，Hermes 还可以**作为** MCP 服务器。这让其他支持 MCP 的代理（Claude Code、Cursor、Codex 或任何 MCP 客户端）使用 Hermes 的消息传递功能 — 列出对话、阅读消息历史记录，并通过所有连接的平台发送消息。

### 何时使用此功能

- 您希望 Claude Code、Cursor 或其他编码代理通过 Hermes 发送和阅读 Telegram/Discord/Slack 消息
- 您想要一个单一的 MCP 服务器，它可以同时桥接到 Hermes 的所有连接消息平台
- 您已经有一个运行的 Hermes 网关，带有连接的平台

### 快速开始

```bash
hermes mcp serve
```

这启动一个 stdio MCP 服务器。MCP 客户端（不是您）管理进程生命周期。

### MCP 客户端配置

将 Hermes 添加到您的 MCP 客户端配置。例如，在 Claude Code 的 `~/.claude/claude_desktop_config.json` 中：

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
| `conversations_list` | 列出活动的消息对话。按平台过滤或按名称搜索。 |
| `conversation_get` | 通过会话键获取有关一个对话的详细信息。 |
| `messages_read` | 阅读对话的最近消息历史记录。 |
| `attachments_fetch` | 从特定消息中提取非文本附件（图像、媒体）。 |
| `events_poll` | 自游标位置以来轮询新的对话事件。 |
| `events_wait` | 长轮询 / 阻塞直到下一个事件到达（近实时）。 |
| `messages_send` | 通过平台发送消息（例如 `telegram:123456`、`discord:#general`）。 |
| `channels_list` | 列出所有平台上的可用消息目标。 |
| `permissions_list_open` | 列出在此桥接会话期间观察到的待处理批准请求。 |
| `permissions_respond` | 允许或拒绝待处理的批准请求。 |

### 事件系统

MCP 服务器包含一个实时事件桥接，轮询 Hermes 的会话数据库以获取新消息。这让 MCP 客户端近实时地感知传入对话：

```
# 轮询新事件（非阻塞）
events_poll(after_cursor=0)

# 等待下一个事件（阻塞直到超时）
events_wait(after_cursor=42, timeout_ms=30000)
```

事件类型：`message`、`approval_requested`、`approval_resolved`

事件队列在内存中，并在桥接连接时启动。较旧的消息可通过 `messages_read` 获得。

### 选项

```bash
hermes mcp serve              # 正常模式
hermes mcp serve --verbose    # stderr 上的调试日志记录
```

### 工作原理

MCP 服务器直接从 Hermes 的会话存储（`~/.hermes/sessions/sessions.json` 和 SQLite 数据库）读取对话数据。后台线程轮询数据库以获取新消息并维护内存中的事件队列。对于发送消息，它使用与 Hermes 代理本身相同的 `send_message` 基础设施。

网关**不需要**运行以进行读取操作（列出对话、阅读历史记录、轮询事件）。它**确实**需要运行以进行发送操作，因为平台适配器需要活动连接。

### 当前限制

- 仅 Stdio 传输（尚未有 HTTP MCP 传输）
- 通过 mtime 优化的 DB 轮询以约 200ms 间隔进行事件轮询（当文件未更改时跳过工作）
- 尚未有 `claude/channel` 推送通知协议
- 仅文本发送（没有通过 `messages_send` 发送媒体/附件）

## 相关文档

- [在 Hermes 中使用 MCP](/docs/guides/use-mcp-with-hermes)
- [CLI 命令](/docs/reference/cli-commands)
- [斜杠命令](/docs/reference/slash-commands)
- [常见问题解答](/docs/reference/faq)
