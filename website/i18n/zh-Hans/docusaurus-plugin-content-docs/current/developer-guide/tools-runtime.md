---
sidebar_position: 9
title: "工具运行时"
description: "工具注册表、工具集、分发和终端环境的运行时行为"
---

# 工具运行时

Hermes 工具是自注册函数，分组到工具集中，并通过中央注册表/分发系统执行。

主要文件：

- `tools/registry.py`
- `model_tools.py`
- `toolsets.py`
- `tools/terminal_tool.py`
- `tools/environments/*`

## 工具注册模型

每个工具模块在导入时调用 `registry.register(...)`。

`model_tools.py` 负责导入/发现工具模块并构建模型使用的模式列表。

### `registry.register()` 如何工作

`tools/` 中的每个工具文件在模块级别调用 `registry.register()` 来声明自身。函数签名为：

```python
registry.register(
    name="terminal",               # 唯一工具名称（用于 API 模式）
    toolset="terminal",            # 此工具所属的工具集
    schema={...},                  # OpenAI 函数调用模式（描述、参数）
    handler=handle_terminal,       # 工具被调用时执行的函数
    check_fn=check_terminal,       # 可选：返回 True/False 表示可用性
    requires_env=["SOME_VAR"],     # 可选：需要的环境变量（用于 UI 显示）
    is_async=False,                # 处理器是否为异步协程
    description="运行命令",        # 人类可读的描述
    emoji="💻",                    # 用于微调器/进度显示的 emoji
)
```

每次调用都会创建一个 `ToolEntry`，存储在单例 `ToolRegistry._tools` 字典中，以工具名称为键。如果跨工具集发生名称冲突，会记录警告，后注册的获胜。

### 发现：`discover_builtin_tools()`

当 `model_tools.py` 被导入时，它会调用 `tools/registry.py` 中的 `discover_builtin_tools()`。此函数使用 AST 解析扫描每个 `tools/*.py` 文件，查找包含顶级 `registry.register()` 调用的模块，然后导入它们：

```python
# tools/registry.py (简化)
def discover_builtin_tools(tools_dir=None):
    tools_path = Path(tools_dir) if tools_dir else Path(__file__).parent
    for path in sorted(tools_path.glob("*.py")):
        if path.name in {"__init__.py", "registry.py", "mcp_tool.py"}:
            continue
        if _module_registers_tools(path):  # AST check for top-level registry.register()
            importlib.import_module(f"tools.{path.stem}")
```

This auto-discovery means new tool files are picked up automatically — no manual list to maintain. The AST check only matches top-level `registry.register()` calls (not calls inside functions), so helper modules in `tools/` are not imported.

Each import triggers the module's `registry.register()` calls. Errors in optional tools (e.g., missing `fal_client` for image generation) are caught and logged — they don't prevent other tools from loading.

After core tool discovery, MCP tools and plugin tools are also discovered:

1. **MCP 工具** — `tools.mcp_tool.discover_mcp_tools()` 读取 MCP 服务器配置并从外部服务器注册工具。
2. **插件工具** — `hermes_cli.plugins.discover_plugins()` 加载可能注册额外工具的用户/项目/pip 插件。

## 工具可用性检查（`check_fn`）

每个工具可以选择提供一个 `check_fn` — 一个在工具可用时返回 `True`、否则返回 `False` 的可调用对象。典型的检查包括：

- **API 密钥存在** — 例如，`lambda: bool(os.environ.get("SERP_API_KEY"))` 用于网页搜索
- **服务运行中** — 例如，检查是否配置了 Honcho 服务器
- **二进制文件已安装** — 例如，验证 `playwright` 是否可用于浏览器工具

当 `registry.get_definitions()` 为模型构建模式列表时，它运行每个工具的 `check_fn()`：

```python
# 简化自 registry.py
if entry.check_fn:
    try:
        available = bool(entry.check_fn())
    except Exception:
        available = False   # 异常 = 不可用
    if not available:
        continue            # 完全跳过此工具
```

关键行为：
- 检查结果**按调用缓存** — 如果多个工具共享相同的 `check_fn`，它只运行一次。
- `check_fn()` 中的异常被视为"不可用"（故障安全）。
- `is_toolset_available()` 方法检查工具集的 `check_fn` 是否通过，用于 UI 显示和工具集解析。

## 工具集解析

工具集是命名的工具捆绑包。Hermes 通过以下方式解析它们：

- 显式启用/禁用工具集列表
- 平台预设（`hermes-cli`、`hermes-telegram` 等）
- 动态 MCP 工具集
- 精选的特殊用途集如 `hermes-acp`

### `get_tool_definitions()` 如何过滤工具

主要入口点是 `model_tools.get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode)`：

1. **如果提供了 `enabled_toolsets`** — 仅包含来自这些工具集的工具。每个工具集名称通过 `resolve_toolset()` 解析，该函数将复合工具集展开为单独的工具名称。

2. **如果提供了 `disabled_toolsets`** — 从所有工具集开始，然后减去禁用的工具集。

3. **如果两者都没有** — 包含所有已知的工具集。

4. **注册表过滤** — 解析的工具名称集被传递给 `registry.get_definitions()`，它应用 `check_fn` 过滤并返回 OpenAI 格式的模式。

5. **Dynamic schema patching** — after filtering, `execute_code` and `browser_navigate` schemas are dynamically adjusted to only reference tools that actually passed filtering (prevents model hallucination of unavailable tools).

### Legacy toolset names

带有 `_tools` 后缀的旧工具集名称（例如 `web_tools`、`terminal_tools`）通过 `_LEGACY_TOOLSET_MAP` 映射到其现代工具名称，以保持向后兼容性。

## 分发

在运行时，工具通过中央注册表分发，智能体循环中有一些智能体级工具（如 memory/todo/session-search 处理）的异常处理。

### 分发流程：模型 tool_call → 处理程序执行

当模型返回 `tool_call` 时，流程如下：

```
Model response with tool_call
    ↓
run_agent.py 智能体循环
    ↓
model_tools.handle_function_call(name, args, task_id, user_task)
    ↓
[智能体循环工具？] → 由智能体循环直接处理（todo、memory、session_search、delegate_task）
    ↓
[插件预钩子] → invoke_hook("pre_tool_call", ...)
    ↓
registry.dispatch(name, args, **kwargs)
    ↓
按名称查找 ToolEntry
    ↓
[异步处理程序？] → 通过 _run_async() 桥接
[同步处理程序？] → 直接调用
    ↓
返回结果字符串（或 JSON 错误）
    ↓
[插件后钩子] → invoke_hook("post_tool_call", ...)
```

### 错误包装

所有工具执行都在两个级别包装了错误处理：

1. **`registry.dispatch()`** — 捕获处理程序中的任何异常并返回 JSON 格式的 `{"error": "Tool execution failed: ExceptionType: message"}`。

2. **`handle_function_call()`** — 在第二次 try/except 中包装整个分发，返回 `{"error": "Error executing tool_name: message"}`。

这确保模型始终收到格式良好的 JSON 字符串，而不是未处理的异常。

### 智能体循环工具

四个工具在注册表分发之前被拦截，因为它们需要智能体级状态（TodoStore、MemoryStore 等）：

- `todo` — 规划/任务跟踪
- `memory` — 持久内存写入
- `session_search` — 跨会话回忆
- `delegate_task` — spawns subagent sessions

These tools' schemas are still registered in the registry (for `get_tool_definitions`), but their handlers return a stub error if dispatch somehow reaches them directly.

### Async bridging

当工具处理程序是异步的时，`_run_async()` 将其桥接到同步分发路径：

- **CLI 路径（无运行循环）** — 使用持久的事件循环保持缓存的异步客户端存活
- **Gateway 路径（运行循环）** — 使用 `asyncio.run()` 启动可处置线程
- **工作线程（并行工具）** — 使用存储在线程本地存储中的每线程持久循环

## DANGEROUS_PATTERNS 审批流程

终端工具集成了在 `tools/approval.py` 中定义的危险命令审批系统：

1. **模式检测** — `DANGEROUS_PATTERNS` 是一个涵盖破坏性操作的 `(regex, description)` 元组列表：
   - 递归删除（`rm -rf`）
   - 文件系统格式化（`mkfs`、`dd`）
   - SQL 破坏性操作（`DROP TABLE`、`DELETE FROM` 没有 `WHERE`）
   - 系统配置覆盖（`> /etc/`）
   - 服务操作（`systemctl stop`）
   - 远程代码执行（`curl | sh`）
   - Fork 炸弹、进程终止等

2. **检测** — 在执行任何终端命令之前，`detect_dangerous_command(command)` 检查所有模式。

3. **审批提示** — 如果找到匹配：
   - **CLI 模式** — 交互式提示要求用户批准、拒绝或永久允许
   - **Gateway 模式** — 异步审批回调将请求发送到消息平台
   - **智能审批** — 可选地，辅助 LLM 可以自动批准匹配模式的低风险命令（例如 `rm -rf node_modules/` 是安全的但匹配"递归删除"）

4. **会话状态** — 审批按会话跟踪。一旦您批准了会话的"递归删除"，后续的 `rm -rf` 命令不会重新提示。

5. **永久允许列表** — "永久允许"选项将模式写入 `config.yaml` 的 `command_allowlist`，跨会话持久化。

## 终端/运行时环境

终端系统支持多种后端：

- local
- docker
- ssh
- singularity
- modal
- daytona

它还支持：

- 每任务 cwd 覆盖
- 后台进程管理
- PTY 模式
- 危险命令的审批回调

## 并发

工具调用可以根据工具组合和交互需求顺序或并发执行。

## 相关文档

- [工具集参考](../reference/toolsets-reference.md)
- [内置工具参考](../reference/tools-reference.md)
- [智能体循环内部机制](./agent-loop.md)
- [ACP 内部机制](./acp-internals.md)