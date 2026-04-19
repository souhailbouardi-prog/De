---
sidebar_position: 6
title: "使用 MCP 与 Hermes"
description: "将 MCP 服务器连接到 Hermes Agent、过滤其工具并在实际工作流中安全使用的实用指南"
---

# 使用 MCP 与 Hermes

本指南展示了如何在日常工作中实际使用 MCP 与 Hermes Agent。

如果功能页面解释了 MCP 是什么，本指南则是关于如何快速安全地从中获取价值。

## 何时应该使用 MCP？

在以下情况下使用 MCP：
- 工具已经以 MCP 形式存在，您不想构建原生 Hermes 工具
- 您希望 Hermes 通过干净的 RPC 层操作本地或远程系统
- 您想要细粒度的每服务器暴露控制
- 您希望将 Hermes 连接到内部 API、数据库或公司系统，而无需修改 Hermes 核心

在以下情况下不要使用 MCP：
- 内置的 Hermes 工具已经很好地解决了工作
- 服务器暴露了巨大的危险工具表面，而您没有准备好过滤它
- 您只需要一个非常狭窄的集成，原生工具会更简单和安全

## 心智模型

将 MCP 视为适配器层：
- Hermes 仍然是智能体
- MCP 服务器贡献工具
- Hermes 在启动或重新加载时发现这些工具
- 模型可以像普通工具一样使用它们
- 您控制每个服务器的可见程度

最后一部分很重要。良好的 MCP 使用不仅仅是"连接一切"。而是"连接正确的工具，具有最小的有用表面"。

## 步骤 1：安装 MCP 支持

如果您使用标准安装脚本安装了 Hermes，MCP 支持已经包含在内（安装程序运行 `uv pip install -e ".[all]"`）。

如果您在没有额外功能的情况下安装并需要单独添加 MCP：

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

对于基于 npm 的服务器，请确保 Node.js 和 `npx` 可用。

对于许多 Python MCP 服务器，`uvx` 是一个不错的默认选择。

## 步骤 2：先添加一个服务器

从单个安全服务器开始。

示例：文件系统仅访问一个项目目录。

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

然后启动 Hermes：

```bash
hermes chat
```

现在询问具体内容：

```text
检查这个项目并总结仓库布局。
```

## 步骤 3：验证 MCP 已加载

您可以通过几种方式验证 MCP：

- Hermes 横幅/状态在配置时应显示 MCP 集成
- 询问 Hermes 它有哪些可用工具
- 配置更改后使用 `/reload-mcp`
- 如果服务器连接失败，检查日志

实用测试提示：

```text
告诉我现在哪些 MCP 支持的工具可用。
```

## 步骤 4：立即开始过滤

如果服务器暴露了很多工具，请不要等到以后。

### 示例：只白名单您想要的内容

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, search_code]
```

这通常是敏感系统的最佳默认设置。

### 示例：黑名单危险操作

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

### 示例：也禁用实用工具包装器

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```

## 过滤实际上影响了什么？

Hermes 中 MCP 暴露的功能有两类：

1. 服务器原生 MCP 工具
- 过滤方式：
  - `tools.include`
  - `tools.exclude`

2. Hermes 添加的实用工具包装器
- 过滤方式：
  - `tools.resources`
  - `tools.prompts`

### 您可能看到的实用工具包装器

资源：
- `list_resources`
- `read_resource`

提示：
- `list_prompts`
- `get_prompt`

这些包装器仅在以下情况下出现：
- 您的配置允许它们，并且
- MCP 服务器会话实际支持这些功能

因此，如果服务器不支持资源/提示，Hermes 不会假装它有。

## 常见模式

### 模式 1：本地项目助手

当您希望 Hermes 在有界工作区中推理时，使用 MCP 进行仓库本地文件系统或 git 服务器。

```yaml
mcp_servers:
  fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]

  git:
    command: "uvx"
    args: ["mcp-server-git", "--repository", "/home/user/project"]
```

好的提示：

```text
审查项目结构并确定配置所在位置。
```

```text
检查本地 git 状态并总结最近的更改。
```

### 模式 2：GitHub 分类助手

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue, search_code]
      prompts: false
      resources: false
```

好的提示：

```text
列出关于 MCP 的未解决问题，按主题聚类，并为最常见的错误起草高质量问题。
```

```text
在仓库中搜索 _discover_and_register_server 的使用，并解释 MCP 工具是如何注册的。
```

### 模式 3：内部 API 助手

```yaml
mcp_servers:
  internal_api:
    url: "https://mcp.internal.example.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      include: [list_customers, get_customer, list_invoices]
      resources: false
      prompts: false
```

好的提示：

```text
查找客户 ACME Corp 并总结最近的发票活动。
```

在这种情况下，严格的白名单比排除列表要好得多。

### 模式 4：文档/知识服务器

一些 MCP 服务器暴露的提示或资源更像是共享知识资产，而不是直接操作。

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: true
      resources: true
```

好的提示：

```text
列出 docs 服务器可用的 MCP 资源，然后阅读入职指南并总结它。
```

```text
列出 docs 服务器暴露的提示，并告诉我哪些有助于事件响应。
```

## 教程：带过滤的端到端设置

这里是一个实用的进展过程。

### 阶段 1：添加带有严格白名单的 GitHub MCP

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, search_code]
      prompts: false
      resources: false
```

启动 Hermes 并询问：

```text
搜索代码库中对 MCP 的引用，并总结主要集成点。
```

### 阶段 2：仅在需要时扩展

如果您后来也需要问题更新：

```yaml
tools:
  include: [list_issues, create_issue, update_issue, search_code]
```

然后重新加载：

```text
/reload-mcp
```

### 阶段 3：添加具有不同策略的第二个服务器

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue, search_code]
      prompts: false
      resources: false

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]
```

现在 Hermes 可以结合它们：

```text
检查本地项目文件，然后创建一个 GitHub issue 总结您发现的错误。
```

这就是 MCP 的强大之处：无需更改 Hermes 核心的多系统工作流。

## 安全使用建议

### 对危险系统首选允许列表

对于任何财务、面向客户或破坏性的系统：
- 使用 `tools.include`
- 从最小可能的集合开始

### 禁用未使用的实用工具

如果您不希望模型浏览服务器提供的资源/提示，请将它们关闭：

```yaml
tools:
  resources: false
  prompts: false
```

### 保持服务器范围狭窄

示例：
- 文件系统服务器根目录指向一个项目目录，而不是整个主目录
- git 服务器指向一个仓库
- 内部 API 服务器默认暴露以读取为主的工具

### 配置更改后重新加载

```text
/reload-mcp
```

在更改以下内容后执行此操作：
- include/exclude 列表
- enabled 标志
- resources/prompts 切换
- 认证头部 / 环境变量

## 按症状故障排除

### "服务器连接但我期望的工具缺失"

可能的原因：
- 被 `tools.include` 过滤
- 被 `tools.exclude` 排除
- 实用工具包装器通过 `resources: false` 或 `prompts: false` 禁用
- 服务器实际上不支持资源/提示

### "服务器已配置但未加载任何内容"

检查：
- 配置中是否留有 `enabled: false`
- 命令/运行时是否存在（`npx`、`uvx` 等）
- HTTP 端点是否可访问
- 认证环境或头部是否正确

### "为什么我看到的工具比 MCP 服务器宣传的少？"

因为 Hermes 现在尊重您的每服务器策略和能力感知注册。这是预期的，通常是可取的。

### "如何在不删除配置的情况下移除 MCP 服务器？"

使用：

```yaml
enabled: false
```

这会保留配置但阻止连接和注册。

## 推荐的首个 MCP 设置

大多数用户的良好首选服务器：
- 文件系统
- git
- GitHub
- 获取 / 文档 MCP 服务器
- 一个狭窄的内部 API

不太理想的首选服务器：
- 具有大量破坏性操作且无过滤的大型业务系统
- 您不够了解以至于无法约束的任何系统

## 相关文档

- [MCP (Model Context Protocol)](/docs/user-guide/features/mcp)
- [FAQ](/docs/reference/faq)
- [斜杠命令](/docs/reference/slash-commands)