---
sidebar_position: 7
title: "子代理委托"
description: "使用 delegate_task 生成隔离的子代理以并行工作流"
---

# 子代理委托

`delegate_task` 工具生成具有隔离上下文、受限工具集和自己的终端会话的子 AIAgent 实例。每个子代理都获得一个新的对话并独立工作 — 只有它的最终摘要进入父代理的上下文。

## 单个任务

```python
delegate_task(
    goal="Debug why tests fail",
    context="Error: assertion in test_foo.py line 42",
    toolsets=["terminal", "file"]
)
```

## 并行批次

最多 3 个并发子代理：

```python
delegate_task(tasks=[
    {"goal": "Research topic A", "toolsets": ["web"]},
    {"goal": "Research topic B", "toolsets": ["web"]},
    {"goal": "Fix the build", "toolsets": ["terminal", "file"]}
])
```

## 子代理上下文如何工作

:::warning 关键：子代理一无所知
子代理从 **完全新的对话** 开始。它们对父代理的对话历史、先前的工具调用或委托前讨论的任何内容都零知识。子代理的唯一上下文来自您提供的 `goal` 和 `context` 字段。
:::

这意味着您必须传递子代理需要的 **所有内容**：

```python
# 不好 - 子代理不知道"错误"是什么
delegate_task(goal="Fix the error")

# 好 - 子代理有它需要的所有上下文
delegate_task(
    goal="Fix the TypeError in api/handlers.py",
    context="""The file api/handlers.py has a TypeError on line 47:
    'NoneType' object has no attribute 'get'.
    The function process_request() receives a dict from parse_body(),
    but parse_body() returns None when Content-Type is missing.
    The project is at /home/user/myproject and uses Python 3.11."""
)
```

子代理收到一个从您的目标和上下文构建的聚焦系统提示，指示它完成任务并提供它所做工作的结构化摘要、发现的内容、修改的任何文件以及遇到的任何问题。

## 实际示例

### 并行研究

同时研究多个主题并收集摘要：

```python
delegate_task(tasks=[
    {
        "goal": "Research the current state of WebAssembly in 2025",
        "context": "Focus on: browser support, non-browser runtimes, language support",
        "toolsets": ["web"]
    },
    {
        "goal": "Research the current state of RISC-V adoption in 2025",
        "context": "Focus on: server chips, embedded systems, software ecosystem",
        "toolsets": ["web"]
    },
    {
        "goal": "Research quantum computing progress in 2025",
        "context": "Focus on: error correction breakthroughs, practical applications, key players",
        "toolsets": ["web"]
    }
])
```

### 代码审查 + 修复

将审查和修复工作流委托给新的上下文：

```python
delegate_task(
    goal="Review the authentication module for security issues and fix any found",
    context="""Project at /home/user/webapp.
    Auth module files: src/auth/login.py, src/auth/jwt.py, src/auth/middleware.py.
    The project uses Flask, PyJWT, and bcrypt.
    Focus on: SQL injection, JWT validation, password handling, session management.
    Fix any issues found and run the test suite (pytest tests/auth/).""",
    toolsets=["terminal", "file"]
)
```

### 多文件重构

委托一个会淹没父代上下文的大型重构任务：

```python
delegate_task(
    goal="Refactor all Python files in src/ to replace print() with proper logging",
    context="""Project at /home/user/myproject.
    Use the 'logging' module with logger = logging.getLogger(__name__).
    Replace print() calls with appropriate log levels:
    - print(f"Error: ...") -> logger.error(...)
    - print(f"Warning: ...") -> logger.warning(...)
    - print(f"Debug: ...") -> logger.debug(...)
    - Other prints -> logger.info(...)
    Don't change print() in test files or CLI output.
    Run pytest after to verify nothing broke.""",
    toolsets=["terminal", "file"]
)
```

## 批次模式详细信息

当您提供 `tasks` 数组时，子代理使用线程池 **并行** 运行：

- **最大并发：** 3 个任务（如果 `tasks` 数组更长，则截断为 3）
- **线程池：** 使用 `ThreadPoolExecutor` 配合 `MAX_CONCURRENT_CHILDREN = 3` 个工作进程
- **进度显示：** 在 CLI 模式下，树视图实时显示每个子代理的工具调用，并带有每个任务的完成行。在网关模式下，进度被批处理并中继到父代的进度回调
- **结果排序：** 结果按任务索引排序，以匹配输入顺序，无论完成顺序如何
- **中断传播：** 中断父代（例如，发送新消息）会中断所有活动的子代理

单任务委托直接运行，没有线程池开销。

## 模型覆盖

您可以通过 `config.yaml` 为子代理配置不同的模型 — 对于将简单任务委托给更便宜/更快的模型很有用：

```yaml
# 在 ~/.hermes/config.yaml 中
delegation:
  model: "google/gemini-flash-2.0"    # 子代理的更便宜模型
  provider: "openrouter"              # 可选：将子代理路由到不同的提供程序
```

如果省略，子代理使用与父代相同的模型。

## 工具集选择技巧

`toolsets` 参数控制子代理可以访问哪些工具。根据任务选择：

| 工具集模式 | 用例 |
|----------------|----------|
| `["terminal", "file"]` | 代码工作、调试、文件编辑、构建 |
| `["web"]` | 研究、事实核查、文档查找 |
| `["terminal", "file", "web"]` | 全栈任务（默认） |
| `["file"]` | 只读分析、无需执行的代码审查 |
| `["terminal"]` | 系统管理、进程管理 |

无论您指定什么，某些工具集对子代理 **始终被阻止**：
- `delegation` — 无递归委托（防止无限生成）
- `clarify` — 子代理无法与用户交互
- `memory` — 不写入共享持久内存
- `code_execution` — 子代理应该逐步推理
- `send_message` — 无跨平台副作用（例如，发送 Telegram 消息）

## 最大迭代次数

每个子代理都有一个迭代限制（默认：50），控制它可以进行多少个工具调用回合：

```python
delegate_task(
    goal="Quick file check",
    context="Check if /etc/nginx/nginx.conf exists and print its first 10 lines",
    max_iterations=10  # 简单任务，不需要很多回合
)
```

## 深度限制

委托有 **深度限制 2** — 父代（深度 0）可以生成子代（深度 1），但子代不能进一步委托。这防止失控的递归委托链。

## 关键属性

- 每个子代理都获得它自己的 **终端会话**（与父代分开）
- **无嵌套委托** — 子代不能进一步委托（无孙代）
- 子代理 **不能** 调用：`delegate_task`、`clarify`、`memory`、`send_message`、`execute_code`
- **中断传播** — 中断父代会中断所有活动的子代理
- 只有最终摘要进入父代的上下文，保持令牌使用高效
- 子代理继承父代的 **API 密钥、提供程序配置和凭证池**（在速率限制上启用密钥轮换）

## 委托与 execute_code

| 因素 | delegate_task | execute_code |
|--------|--------------|-------------|
| **推理** | 完整的 LLM 推理循环 | 仅 Python 代码执行 |
| **上下文** | 新的隔离对话 | 无对话，仅脚本 |
| **工具访问** | 所有非阻塞工具带推理 | 通过 RPC 的 7 个工具，无推理 |
| **并行性** | 最多 3 个并发子代理 | 单个脚本 |
| **最适合** | 需要判断的复杂任务 | 机械的多步骤管道 |
| **令牌成本** | 更高（完整 LLM 循环） | 更低（仅返回 stdout） |
| **用户交互** | 无（子代理无法澄清） | 无 |

**经验法则：** 当子任务需要推理、判断或多步骤问题解决时，使用 `delegate_task`。当您需要机械数据处理或脚本化工作流时，使用 `execute_code`。

## 配置

```yaml
# 在 ~/.hermes/config.yaml 中
delegation:
  max_iterations: 50                        # 每个子代的最大回合数（默认：50）
  default_toolsets: ["terminal", "file", "web"]  # 默认工具集
  model: "google/gemini-3-flash-preview"             # 可选的提供程序/模型覆盖
  provider: "openrouter"                             # 可选的内置提供程序

# 或者使用直接自定义端点而不是提供程序：
delegation:
  model: "qwen2.5-coder"
  base_url: "http://localhost:1234/v1"
  api_key: "local-key"
```

:::tip
代理根据任务复杂性自动处理委托。您不需要明确要求它委托 — 当有意义时，它会这样做。
:::
