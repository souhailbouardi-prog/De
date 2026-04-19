---
sidebar_position: 7
title: "子智能体委托"
description: "使用 delegate_task 为并行工作流生成隔离的子智能体"
---

# 子智能体委托

`delegate_task` 工具生成具有隔离上下文、受限工具集和自己的终端会话的子 AIAgent 实例。每个子智能体获得一个新的对话并独立工作 — 只有其最终摘要进入父智能体的上下文。

## 单个任务

```python
delegate_task(
    goal="Debug why tests fail",
    context="Error: assertion in test_foo.py line 42",
    toolsets=["terminal", "file"]
)
```

## 并行批处理

最多 3 个并发子智能体：

```python
delegate_task(tasks=[
    {"goal": "Research topic A", "toolsets": ["web"]},
    {"goal": "Research topic B", "toolsets": ["web"]},
    {"goal": "Fix the build", "toolsets": ["terminal", "file"]}
])
```

## 子智能体上下文如何工作

:::warning 关键：子智能体一无所知
子智能体以**完全新的对话**开始。它们对父智能体的对话历史、之前的工具调用或委托之前讨论的任何内容都一无所知。子智能体的唯一上下文来自您提供的 `goal` 和 `context` 字段。
:::

这意味着您必须传递**子智能体所需的一切**：

```python
# 错误 - 子智能体不知道 "the error" 是什么
delegate_task(goal="Fix the error")

# 正确 - 子智能体拥有所需的所有上下文
delegate_task(
    goal="Fix the TypeError in api/handlers.py",
    context="""The file api/handlers.py has a TypeError on line 47:
    'NoneType' object has no attribute 'get'.
    The function process_request() receives a dict from parse_body(),
    but parse_body() returns None when Content-Type is missing.
    The project is at /home/user/myproject and uses Python 3.11."""
)
```

子智能体接收一个从您的目标和上下文构建的专注系统提示，指示它完成任务并提供结构化摘要，包括它做了什么、发现了什么、修改了哪些文件以及遇到了哪些问题。

## 实用示例

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

将可能淹没父智能体上下文的大型重构任务委托出去：

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

## 批处理模式详情

当您提供 `tasks` 数组时，子智能体使用线程池**并行**运行：

- **最大并发数：** 3 个任务（如果 `tasks` 数组更长，则截断为 3 个）
- **线程池：** 使用 `ThreadPoolExecutor`，配置 `MAX_CONCURRENT_CHILDREN = 3` 个工作线程
- **进度显示：** 在 CLI 模式下，树状视图实时显示每个子智能体的工具调用，并显示每个任务的完成行。在网关模式下，进度被批处理并转发到父智能体的进度回调
- **结果排序：** 结果按任务索引排序，以匹配输入顺序，无论完成顺序如何
- **中断传播：** 中断父智能体（例如，发送新消息）会中断所有活动的子智能体

单个任务委托直接运行，没有线程池开销。

## 模型覆盖

您可以通过 `config.yaml` 为子智能体配置不同的模型 — 这对于将简单任务委托给更便宜/更快的模型很有用：

```yaml
# 在 ~/.hermes/config.yaml 中
delegation:
  model: "google/gemini-flash-2.0"    # 子智能体使用更便宜的模型
  provider: "openrouter"              # 可选：将子智能体路由到不同的提供商
```

如果省略，子智能体使用与父智能体相同的模型。

## 工具集选择提示

`toolsets` 参数控制子智能体可以访问的工具。根据任务选择：

| 工具集模式 | 使用场景 |
|----------------|----------|
| `["terminal", "file"]` | 代码工作、调试、文件编辑、构建 |
| `["web"]` | 研究、事实检查、文档查找 |
| `["terminal", "file", "web"]` | 全栈任务（默认） |
| `["file"]` | 只读分析、无需执行的代码审查 |
| `["terminal"]` | 系统管理、进程管理 |

无论您指定什么，某些工具集对子智能体**始终被阻止**：
- `delegation` — 无递归委托（防止无限生成）
- `clarify` — 子智能体无法与用户交互
- `memory` — 无共享持久内存写入
- `code_execution` — 子智能体应逐步推理
- `send_message` — 无跨平台副作用（例如，发送 Telegram 消息）

## 最大迭代次数

每个子智能体有一个迭代限制（默认：50），控制它可以进行多少次工具调用轮次：

```python
delegate_task(
    goal="Quick file check",
    context="Check if /etc/nginx/nginx.conf exists and print its first 10 lines",
    max_iterations=10  # 简单任务，不需要很多轮次
)
```

## 深度限制

委托有**深度限制为 2** — 父智能体（深度 0）可以生成子智能体（深度 1），但子智能体不能进一步委托。这防止失控的递归委托链。

## 关键特性

- 每个子智能体获得**自己的终端会话**（与父智能体分开）
- **无嵌套委托** — 子智能体不能进一步委托（无孙智能体）
- 子智能体**不能**调用：`delegate_task`、`clarify`、`memory`、`send_message`、`execute_code`
- **中断传播** — 中断父智能体会中断所有活动的子智能体
- 只有最终摘要进入父智能体的上下文，保持令牌使用高效
- 子智能体继承父智能体的**API 密钥、提供商配置和凭证池**（启用基于速率限制的密钥轮换）

## 委托与 execute_code 的比较

| 因素 | delegate_task | execute_code |
|--------|--------------|-------------|
| **推理** | 完整的 LLM 推理循环 | 仅 Python 代码执行 |
| **上下文** | 新的隔离对话 | 无对话，仅脚本 |
| **工具访问** | 所有非阻塞工具，带推理 | 7 个工具通过 RPC，无推理 |
| **并行性** | 最多 3 个并发子智能体 | 单个脚本 |
| **最适合** | 需要判断的复杂任务 | 机械多步骤管道 |
| **令牌成本** | 更高（完整 LLM 循环） | 更低（仅返回标准输出） |
| **用户交互** | 无（子智能体不能澄清） | 无 |

**经验法则：** 当子任务需要推理、判断或多步骤问题解决时，使用 `delegate_task`。当您需要机械数据处理或脚本化工作流时，使用 `execute_code`。

## 配置

```yaml
# 在 ~/.hermes/config.yaml 中
delegation:
  max_iterations: 50                        # 每个子智能体的最大轮次（默认：50）
  default_toolsets: ["terminal", "file", "web"]  # 默认工具集
  model: "google/gemini-3-flash-preview"             # 可选的提供商/模型覆盖
  provider: "openrouter"                             # 可选的内置提供商

# 或者使用直接的自定义端点而不是提供商：
delegation:
  model: "qwen2.5-coder"
  base_url: "http://localhost:1234/v1"
  api_key: "local-key"
```

:::tip
智能体会根据任务复杂度自动处理委托。您不需要明确要求它委托 — 当有意义时它会自动这样做。
:::