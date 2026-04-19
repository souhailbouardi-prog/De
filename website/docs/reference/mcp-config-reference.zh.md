---
sidebar_position: 8
title: "MCP 配置参考"
description: "Hermes Agent MCP 配置键、过滤语义和实用工具策略参考"
---

# MCP 配置参考

本页面是主要 MCP 文档的紧凑参考指南。

如需概念性指导，请参阅：
- [MCP (Model Context Protocol)](/docs/user-guide/features/mcp.zh)
- [在 Hermes 中使用 MCP](/docs/guides/use-mcp-with-hermes.zh)

## 根配置结构

```yaml
mcp_servers:
  <server_name>:
    command: "..."      # stdio 服务器
    args: []
    env: {}

    # 或者
    url: "..."          # HTTP 服务器
    headers: {}

    enabled: true
    timeout: 120
    connect_timeout: 60
    tools:
      include: []
      exclude: []
      resources: true
      prompts: true
```

## 服务器键

| 键 | 类型 | 适用于 | 含义 |
|---|---|---|---|
| `command` | string | stdio | 要启动的可执行文件 |
| `args` | list | stdio | 子进程的参数 |
| `env` | mapping | stdio | 传递给子进程的环境变量 |
| `url` | string | HTTP | 远程 MCP 端点 |
| `headers` | mapping | HTTP | 远程服务器请求的头信息 |
| `enabled` | bool | 两者 | 为 false 时完全跳过服务器 |
| `timeout` | number | 两者 | 工具调用超时时间 |
| `connect_timeout` | number | 两者 | 初始连接超时时间 |
| `tools` | mapping | 两者 | 过滤和实用工具策略 |
| `auth` | string | HTTP | 认证方法。设置为 `oauth` 以启用带 PKCE 的 OAuth 2.1 |
| `sampling` | mapping | 两者 | 服务器发起的 LLM 请求策略（参见 MCP 指南） |

## `tools` 策略键

| 键 | 类型 | 含义 |
|---|---|---|
| `include` | string 或 list | 白名单服务器原生 MCP 工具 |
| `exclude` | string 或 list | 黑名单服务器原生 MCP 工具 |
| `resources` | bool-like | 启用/禁用 `list_resources` + `read_resource` |
| `prompts` | bool-like | 启用/禁用 `list_prompts` + `get_prompt` |

## 过滤语义

### `include`

如果设置了 `include`，则只注册那些服务器原生 MCP 工具。

```yaml
tools:
  include: [create_issue, list_issues]
```

### `exclude`

如果设置了 `exclude` 且未设置 `include`，则注册除那些名称之外的所有服务器原生 MCP 工具。

```yaml
tools:
  exclude: [delete_customer]
```

### 优先级

如果两者都设置，则 `include` 优先。

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

结果：
- `create_issue` 仍然被允许
- `delete_issue` 被忽略，因为 `include` 优先

## 实用工具策略

Hermes 可能会为每个 MCP 服务器注册这些实用工具包装器：

资源：
- `list_resources`
- `read_resource`

提示：
- `list_prompts`
- `get_prompt`

### 禁用资源

```yaml
tools:
  resources: false
```

### 禁用提示

```yaml
tools:
  prompts: false
```

### 能力感知注册

即使当 `resources: true` 或 `prompts: true` 时，Hermes 也只会在 MCP 会话实际暴露相应能力时才注册这些实用工具。

所以这是正常的：
- 你启用了提示
- 但没有出现提示实用工具
- 因为服务器不支持提示

## `enabled: false`

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

行为：
- 不尝试连接
- 不进行发现
- 不注册工具
- 配置保持原位以供以后重用

## 空结果行为

如果过滤移除了所有服务器原生工具且未注册任何实用工具，Hermes 不会为该服务器创建空的 MCP 运行时工具集。

## 示例配置

### 安全的 GitHub 白名单

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue, search_code]
      resources: false
      prompts: false
```

### Stripe 黑名单

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

### 仅资源文档服务器

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      include: []
      resources: true
      prompts: false
```

## 重新加载配置

更改 MCP 配置后，使用以下命令重新加载服务器：

```text
/reload-mcp
```

## 工具命名

服务器原生 MCP 工具变为：

```text
mcp_<server>_<tool>
```

示例：
- `mcp_github_create_issue`
- `mcp_filesystem_read_file`
- `mcp_my_api_query_data`

实用工具遵循相同的前缀模式：
- `mcp_<server>_list_resources`
- `mcp_<server>_read_resource`
- `mcp_<server>_list_prompts`
- `mcp_<server>_get_prompt`

### 名称清理

服务器名称和工具名称中的连字符 (`-`) 和点 (`.`) 在注册前会被替换为下划线。这确保工具名称是 LLM 函数调用 API 的有效标识符。

例如，一个名为 `my-api` 的服务器暴露一个名为 `list-items.v2` 的工具，变为：

```text
mcp_my_api_list_items_v2
```

编写 `include` / `exclude` 过滤器时请记住这一点 — 使用 **原始** MCP 工具名称（带连字符/点），而不是清理后的版本。

## OAuth 2.1 认证

对于需要 OAuth 的 HTTP 服务器，在服务器条目上设置 `auth: oauth`：

```yaml
mcp_servers:
  protected_api:
    url: "https://mcp.example.com/mcp"
    auth: oauth
```

行为：
- Hermes 使用 MCP SDK 的 OAuth 2.1 PKCE 流程（元数据发现、动态客户端注册、令牌交换和刷新）
- 首次连接时，会打开浏览器窗口进行授权
- 令牌会持久化到 `~/.hermes/mcp-tokens/<server>.json` 并在会话之间重用
- 令牌刷新是自动的；仅当刷新失败时才会重新授权
- 仅适用于 HTTP/StreamableHTTP 传输（基于 `url` 的服务器）