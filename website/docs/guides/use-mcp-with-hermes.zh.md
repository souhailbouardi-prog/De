---
sidebar_position: 6
title: "在Hermes中使用MCP"
description: "连接MCP服务器到Hermes Agent、过滤其工具并在实际工作流中安全使用的实用指南"
---

# 在Hermes中使用MCP

本指南展示如何在日常工作流中实际使用MCP与Hermes Agent。

如果功能页面解释了MCP是什么，本指南则是关于如何快速安全地从中获取价值。

## 何时应该使用MCP？

在以下情况使用MCP：
- 工具已经以MCP形式存在，而您不想构建原生Hermes工具
- 您希望Hermes通过干净的RPC层对本地或远程系统进行操作
- 您希望进行细粒度的每服务器曝光控制
- 您希望将Hermes连接到内部API、数据库或公司系统，而无需修改Hermes核心

在以下情况不要使用MCP：
- 内置的Hermes工具已经很好地解决了任务
- 服务器暴露了巨大的危险工具表面，而您没有准备好过滤它
- 您只需要一个非常狭窄的集成，原生工具会更简单、更安全

## 心智模型

将MCP视为适配器层：

- Hermes仍然是代理
- MCP服务器提供工具
- Hermes在启动或重新加载时发现这些工具
- 模型可以像普通工具一样使用它们
- 您控制每个服务器的可见程度

最后一点很重要。良好的MCP使用不仅仅是"连接一切"。而是"以最小的有用表面连接正确的东西"。

## 步骤1：安装MCP支持

如果您使用标准安装脚本安装Hermes，MCP支持已经包含在内（安装程序运行`uv pip install -e ".[all]"`）。

如果您在没有额外包的情况下安装，需要单独添加MCP：

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

对于基于npm的服务器，确保Node.js和`npx`可用。

对于许多Python MCP服务器，`uvx`是一个不错的默认选择。

## 步骤2：先添加一个服务器

从单个、安全的服务器开始。

示例：只对一个项目目录的文件系统访问。

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

然后启动Hermes：

```bash
hermes chat
```

现在询问具体内容：

```text
检查这个项目并总结仓库布局。
```

## 步骤3：验证MCP已加载

您可以通过几种方式验证MCP：

- 配置后，Hermes横幅/状态应显示MCP集成
- 询问Hermes有哪些可用工具
- 在配置更改后使用`/reload-mcp`
- 如果服务器连接失败，检查日志

实用测试提示：

```text
告诉我现在哪些MCP支持的工具可用。
```

## 步骤4：立即开始过滤

如果服务器暴露了许多工具，不要等到以后再过滤。

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

对于敏感系统，这通常是最佳默认设置。

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

### 示例：也禁用实用包装器

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```

## 过滤实际上影响什么？

Hermes中有两类MCP暴露的功能：

1. 服务器原生MCP工具
- 过滤方式：
  - `tools.include`
  - `tools.exclude`

2. Hermes添加的实用包装器
- 过滤方式：
  - `tools.resources`
  - `tools.prompts`

### 您可能看到的实用包装器

资源：
- `list_resources`
- `read_resource`

提示：
- `list_prompts`
- `get_prompt`

这些包装器仅在以下情况下出现：
- 您的配置允许它们，并且
- MCP服务器会话实际上支持这些功能

因此，如果服务器不支持资源/提示，Hermes不会假装它有。

## 常见模式

### 模式1：本地项目助手

当您希望Hermes在有界工作区上推理时，使用MCP进行仓库本地文件系统或git服务器。

```yaml
mcp_servers:
  fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]

  git:
    command: "uvx"
    args: ["mcp-server-git", "--repository", "/home/user/project"]
```

良好的提示：

```text
审查项目结构并确定配置所在位置。
```

```text
检查本地git状态并总结最近的更改。
```

### 模式2：GitHub分类助手

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

良好的提示：

```text
列出关于MCP的开放问题，按主题聚类，并为最常见的bug起草高质量问题。
```

```text
搜索仓库中对_discover_and_register_server的使用，并解释MCP工具如何注册。
```

### 模式3：内部API助手

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

良好的提示：

```text
查找客户ACME Corp并总结最近的发票活动。
```

对于这种情况，严格的白名单远胜于排除列表。

### 模式4：文档/知识服务器

一些MCP服务器暴露的提示或资源更像是共享知识资产，而不是直接操作。

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: true
      resources: true
```

良好的提示：

```text
列出文档服务器提供的MCP资源，然后阅读入职指南并总结。
```

```text
列出文档服务器暴露的提示，并告诉我哪些对事件响应有帮助。
```

## 教程：带过滤的端到端设置

以下是一个实用的进展。

### 阶段1：添加带有严格白名单的GitHub MCP

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

启动Hermes并询问：

```text
搜索代码库中对MCP的引用，并总结主要集成点。
```

### 阶段2：仅在需要时扩展

如果您后来也需要问题更新：

```yaml
tools:
  include: [list_issues, create_issue, update_issue, search_code]
```

然后重新加载：

```text
/reload-mcp
```

### 阶段3：添加具有不同策略的第二个服务器

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

现在Hermes可以将它们结合起来：

```text
检查本地项目文件，然后创建一个GitHub问题总结您发现的错误。
```

这就是MCP的强大之处：无需更改Hermes核心的多系统工作流。

## 安全使用建议

### 对危险系统首选允许列表

对于任何财务、面向客户或破坏性的系统：
- 使用`tools.include`
- 从最小可能的集合开始

### 禁用未使用的实用程序

如果您不希望模型浏览服务器提供的资源/提示，请将它们关闭：

```yaml
tools:
  resources: false
  prompts: false
```

### 保持服务器范围狭窄

示例：
- 文件系统服务器根目录指向一个项目目录，而不是整个主目录
- git服务器指向一个仓库
- 内部API服务器默认具有读取繁重的工具曝光

### 配置更改后重新加载

```text
/reload-mcp
```

在更改以下内容后执行此操作：
- 包含/排除列表
- 启用标志
- 资源/提示切换
- 身份验证头/环境

## 按症状故障排除

### "服务器连接但我期望的工具缺失"

可能的原因：
- 被`tools.include`过滤
- 被`tools.exclude`排除
- 通过`resources: false`或`prompts: false`禁用了实用包装器
- 服务器实际上不支持资源/提示

### "服务器已配置但无加载"

检查：
- 配置中没有留下`enabled: false`
- 命令/运行时存在（`npx`、`uvx`等）
- HTTP端点可访问
- 身份验证环境或头正确

### "为什么我看到的工具比MCP服务器宣传的少？"

因为Hermes现在尊重您的每服务器策略和能力感知注册。这是预期的，通常是可取的。

### "如何在不删除配置的情况下移除MCP服务器？"

使用：

```yaml
enabled: false
```

这样可以保留配置，但防止连接和注册。

## 推荐的首个MCP设置

对大多数用户来说的良好首个服务器：
- 文件系统
- git
- GitHub
- 获取/文档MCP服务器
- 一个狭窄的内部API

不是很好的首个服务器：
- 具有大量破坏性操作且无过滤的大型业务系统
- 您不够了解以约束的任何内容

## 相关文档

- [MCP（模型上下文协议）](/docs/user-guide/features/mcp)
- [常见问题](/docs/reference/faq)
- [斜杠命令](/docs/reference/slash-commands)