---
sidebar_position: 9
sidebar_label: "构建插件"
title: "构建Hermes插件"
description: "逐步指南，构建包含工具、钩子、数据文件和技能的完整Hermes插件"
---

# 构建Hermes插件

本指南将引导您从头开始构建完整的Hermes插件。完成后，您将拥有一个工作插件，包含多个工具、生命周期钩子、附带的数据文件和捆绑的技能 — 插件系统支持的所有功能。

## 您正在构建什么

一个**计算器**插件，包含两个工具：
- `calculate` — 评估数学表达式（`2**16`、`sqrt(144)`、`pi * 5**2`）
- `unit_convert` — 在单位之间转换（`100 F → 37.78 C`、`5 km → 3.11 mi`）

加上一个记录每个工具调用的钩子，以及一个捆绑的技能文件。

## 步骤1：创建插件目录

```bash
mkdir -p ~/.hermes/plugins/calculator
cd ~/.hermes/plugins/calculator
```

## 步骤2：编写清单

创建`plugin.yaml`：

```yaml
name: calculator
version: 1.0.0
description: Math calculator — evaluate expressions and convert units
provides_tools:
  - calculate
  - unit_convert
provides_hooks:
  - post_tool_call
```

这告诉Hermes："我是一个名为calculator的插件，我提供工具和钩子。" `provides_tools`和`provides_hooks`字段是插件注册的内容列表。

您可以添加的可选字段：
```yaml
author: Your Name
requires_env:          # 基于环境变量控制加载；安装时提示
  - SOME_API_KEY       # 简单格式 — 缺少时插件禁用
  - name: OTHER_KEY    # 丰富格式 — 安装时显示描述/URL
    description: "Key for the Other service"
    url: "https://other.com/keys"
    secret: true
```

## 步骤3：编写工具架构

创建`schemas.py` — 这是LLM读取以决定何时调用您的工具的内容：

```python
"""Tool schemas — what the LLM sees."""

CALCULATE = {
    "name": "calculate",
    "description": (
        "Evaluate a mathematical expression and return the result. "
        "Supports arithmetic (+, -, *, /, **), functions (sqrt, sin, cos, "
        "log, abs, round, floor, ceil), and constants (pi, e). "
        "Use this for any math the user asks about."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate (e.g., '2**10', 'sqrt(144)')",
            },
        },
        "required": ["expression"],
    },
}

UNIT_CONVERT = {
    "name": "unit_convert",
    "description": (
        "Convert a value between units. Supports length (m, km, mi, ft, in), "
        "weight (kg, lb, oz, g), temperature (C, F, K), data (B, KB, MB, GB, TB), "
        "and time (s, min, hr, day)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "The numeric value to convert",
            },
            "from_unit": {
                "type": "string",
                "description": "Source unit (e.g., 'km', 'lb', 'F', 'GB')",
            },
            "to_unit": {
                "type": "string",
                "description": "Target unit (e.g., 'mi', 'kg', 'C', 'MB')",
            },
        },
        "required": ["value", "from_unit", "to_unit"],
    },
}
```

**架构为何重要：** `description`字段是LLM决定何时使用您的工具的方式。具体说明它做什么以及何时使用它。`parameters`定义LLM传递的参数。

## 步骤4：编写工具处理器

创建`tools.py` — 这是LLM调用您的工具时实际执行的代码：

```python
"""Tool handlers — the code that runs when the LLM calls each tool."""

import json
import math

# Safe globals for expression evaluation — no file/network access
_SAFE_MATH = {
    "abs": abs, "round": round, "min": min, "max": max,
    "pow": pow, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan": math.tan, "log": math.log, "log2": math.log2, "log10": math.log10,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e,
    "factorial": math.factorial,
}


def calculate(args: dict, **kwargs) -> str:
    """Evaluate a math expression safely.

    Rules for handlers:
    1. Receive args (dict) — the parameters the LLM passed
    2. Do the work
    3. Return a JSON string — ALWAYS, even on error
    4. Accept **kwargs for forward compatibility
    """
    expression = args.get("expression", "").strip()
    if not expression:
        return json.dumps({"error": "No expression provided"})

    try:
        result = eval(expression, {"__builtins__": {}}, _SAFE_MATH)
        return json.dumps({"expression": expression, "result": result})
    except ZeroDivisionError:
        return json.dumps({"expression": expression, "error": "Division by zero"})
    except Exception as e:
        return json.dumps({"expression": expression, "error": f"Invalid: {e}"})


# Conversion tables — values are in base units
_LENGTH = {"m": 1, "km": 1000, "mi": 1609.34, "ft": 0.3048, "in": 0.0254, "cm": 0.01}
_WEIGHT = {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.0283495}
_DATA = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
_TIME = {"s": 1, "ms": 0.001, "min": 60, "hr": 3600, "day": 86400}


def _convert_temp(value, from_u, to_u):
    # Normalize to Celsius
    c = {"F": (value - 32) * 5/9, "K": value - 273.15}.get(from_u, value)
    # Convert to target
    return {"F": c * 9/5 + 32, "K": c + 273.15}.get(to_u, c)


def unit_convert(args: dict, **kwargs) -> str:
    """Convert between units."""
    value = args.get("value")
    from_unit = args.get("from_unit", "").strip()
    to_unit = args.get("to_unit", "").strip()

    if value is None or not from_unit or not to_unit:
        return json.dumps({"error": "Need value, from_unit, and to_unit"})

    try:
        # Temperature
        if from_unit.upper() in {"C","F","K"} and to_unit.upper() in {"C","F","K"}:
            result = _convert_temp(float(value), from_unit.upper(), to_unit.upper())
            return json.dumps({"input": f"{value} {from_unit}", "result": round(result, 4),
                             "output": f"{round(result, 4)} {to_unit}"})

        # Ratio-based conversions
        for table in (_LENGTH, _WEIGHT, _DATA, _TIME):
            lc = {k.lower(): v for k, v in table.items()}
            if from_unit.lower() in lc and to_unit.lower() in lc:
                result = float(value) * lc[from_unit.lower()] / lc[to_unit.lower()]
                return json.dumps({"input": f"{value} {from_unit}",
                                 "result": round(result, 6),
                                 "output": f"{round(result, 6)} {to_unit}"})

        return json.dumps({"error": f"Cannot convert {from_unit} → {to_unit}"})
    except Exception as e:
        return json.dumps({"error": f"Conversion failed: {e}"})
```

**处理器的关键规则：**
1. **签名：** `def my_handler(args: dict, **kwargs) -> str`
2. **返回：** 始终是JSON字符串。无论成功还是错误。
3. **永不抛出：** 捕获所有异常，返回错误JSON。
4. **接受`**kwargs`：** Hermes将来可能会传递额外的上下文。

## 步骤5：编写注册

创建`__init__.py` — 这将架构连接到处理器：

```python
"""Calculator plugin — registration."""

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)

# Track tool usage via hooks
_call_log = []

def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Hook: runs after every tool call (not just ours)."""
    _call_log.append({"tool": tool_name, "session": task_id})
    if len(_call_log) > 100:
        _call_log.pop(0)
    logger.debug("Tool called: %s (session %s)", tool_name, task_id)


def register(ctx):
    """Wire schemas to handlers and register hooks."""
    ctx.register_tool(name="calculate",    toolset="calculator",
                      schema=schemas.CALCULATE,    handler=tools.calculate)
    ctx.register_tool(name="unit_convert", toolset="calculator",
                      schema=schemas.UNIT_CONVERT, handler=tools.unit_convert)

    # This hook fires for ALL tool calls, not just ours
    ctx.register_hook("post_tool_call", _on_post_tool_call)
```

**`register()`的作用：**
- 在启动时恰好调用一次
- `ctx.register_tool()`将您的工具放入注册表 — 模型立即看到它
- `ctx.register_hook()`订阅生命周期事件
- `ctx.register_cli_command()`注册CLI子命令（例如 `hermes my-plugin <subcommand>`）
- 如果此函数崩溃，插件被禁用但Hermes继续正常运行

## 步骤6：测试它

启动Hermes：

```bash
hermes
```

您应该在横幅的工具列表中看到`calculator: calculate, unit_convert`。

尝试这些提示：
```
2的16次方是多少？
将100华氏度转换为摄氏度
2的平方根乘以pi是多少？
1.5太字节等于多少千兆字节？
```

检查插件状态：
```
/plugins
```

输出：
```
Plugins (1):
  ✓ calculator v1.0.0 (2 tools, 1 hooks)
```

## 您的插件的最终结构

```
~/.hermes/plugins/calculator/
├── plugin.yaml      # "I'm calculator, I provide tools and hooks"
├── __init__.py      # 连接：架构 → 处理器，注册钩子
├── schemas.py       # LLM读取的内容（描述 + 参数规范）
└── tools.py         # 运行的内容（calculate, unit_convert函数）
```

四个文件，清晰分离：
- **清单** 声明插件是什么
- **架构** 描述LLM的工具
- **处理器** 实现实际逻辑
- **注册** 连接一切

## 插件还能做什么？

### 附带数据文件

将任何文件放入插件目录并在导入时读取：

```python
# In tools.py or __init__.py
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_DATA_FILE = _PLUGIN_DIR / "data" / "languages.yaml"

with open(_DATA_FILE) as f:
    _DATA = yaml.safe_load(f)
```

### 捆绑技能

插件可以附带技能文件，代理通过`skill_view("plugin:skill")`加载。在`__init__.py`中注册它们：

```
~/.hermes/plugins/my-plugin/
├── __init__.py
├── plugin.yaml
└── skills/
    ├── my-workflow/
    │   └── SKILL.md
    └── my-checklist/
        └── SKILL.md
```

```python
from pathlib import Path

def register(ctx):
    skills_dir = Path(__file__).parent / "skills"
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)
```

代理现在可以使用其命名空间名称加载您的技能：

```python
skill_view("my-plugin:my-workflow")   # → 插件版本
skill_view("my-workflow")              # → 内置版本（未更改）
```

**关键属性：**
- 插件技能是**只读**的 — 它们不会进入`~/.hermes/skills/`，也不能通过`skill_manage`编辑。
- 插件技能**不会**列在系统提示的`<available_skills>`索引中 — 它们是选择加入的显式加载。
- 裸技能名称不受影响 — 命名空间防止与内置技能冲突。
- 当代理加载插件技能时，会前置一个捆绑上下文横幅，列出同一插件的兄弟技能。

:::tip 传统模式
旧的`shutil.copy2`模式（将技能复制到`~/.hermes/skills/`）仍然有效，但会与内置技能产生名称冲突风险。新插件首选`ctx.register_skill()`。
:::

### 基于环境变量控制

如果您的插件需要API密钥：

```yaml
# plugin.yaml — 简单格式（向后兼容）
requires_env:
  - WEATHER_API_KEY
```

如果`WEATHER_API_KEY`未设置，插件会被禁用，并显示清晰的消息。不会崩溃，代理中不会有错误 — 只是"Plugin weather disabled (missing: WEATHER_API_KEY)"。

当用户运行`hermes plugins install`时，他们会**交互式提示**输入任何缺失的`requires_env`变量。值会自动保存到`.env`。

为了更好的安装体验，使用带有描述和注册URL的丰富格式：

```yaml
# plugin.yaml — 丰富格式
requires_env:
  - name: WEATHER_API_KEY
    description: "API key for OpenWeather"
    url: "https://openweathermap.org/api"
    secret: true
```

| 字段 | 必填 | 描述 |
|-------|----------|-------------|
| `name` | 是 | 环境变量名称 |
| `description` | 否 | 安装提示时显示给用户 |
| `url` | 否 | 获取凭证的位置 |
| `secret` | 否 | 如果为`true`，输入被隐藏（如密码字段） |

两种格式可以在同一列表中混合。已经设置的变量会被静默跳过。

### 条件工具可用性

对于依赖可选库的工具：

```python
ctx.register_tool(
    name="my_tool",
    schema={...},
    handler=my_handler,
    check_fn=lambda: _has_optional_lib(),  # False = 工具对模型隐藏
)
```

### 注册多个钩子

```python
def register(ctx):
    ctx.register_hook("pre_tool_call", before_any_tool)
    ctx.register_hook("post_tool_call", after_any_tool)
    ctx.register_hook("pre_llm_call", inject_memory)
    ctx.register_hook("on_session_start", on_new_session)
    ctx.register_hook("on_session_end", on_session_end)
```

### 钩子参考

每个钩子在**[事件钩子参考](/docs/user-guide/features/hooks#plugin-hooks)**中有完整文档 — 回调签名、参数表、每个钩子的确切触发时间以及示例。以下是摘要：

| 钩子 | 触发时机 | 回调签名 | 返回值 |
|------|-----------|-------------------|---------|
| [`pre_tool_call`](/docs/user-guide/features/hooks#pre_tool_call) | 任何工具执行前 | `tool_name: str, args: dict, task_id: str` | 忽略 |
| [`post_tool_call`](/docs/user-guide/features/hooks#post_tool_call) | 任何工具返回后 | `tool_name: str, args: dict, result: str, task_id: str` | 忽略 |
| [`pre_llm_call`](/docs/user-guide/features/hooks#pre_llm_call) | 每轮一次，工具调用循环前 | `session_id: str, user_message: str, conversation_history: list, is_first_turn: bool, model: str, platform: str` | [上下文注入](#pre_llm_call-context-injection) |
| [`post_llm_call`](/docs/user-guide/features/hooks#post_llm_call) | 每轮一次，工具调用循环后（仅成功轮次） | `session_id: str, user_message: str, assistant_response: str, conversation_history: list, model: str, platform: str` | 忽略 |
| [`on_session_start`](/docs/user-guide/features/hooks#on_session_start) | 新会话创建（仅第一轮） | `session_id: str, model: str, platform: str` | 忽略 |
| [`on_session_end`](/docs/user-guide/features/hooks#on_session_end) | 每次`run_conversation`调用结束 + CLI退出 | `session_id: str, completed: bool, interrupted: bool, model: str, platform: str` | 忽略 |
| [`pre_api_request`](/docs/user-guide/features/hooks#pre_api_request) | 每次向LLM提供商的HTTP请求前 | `method: str, url: str, headers: dict, body: dict` | 忽略 |
| [`post_api_request`](/docs/user-guide/features/hooks#post_api_request) | 每次从LLM提供商的HTTP响应后 | `method: str, url: str, status_code: int, response: dict` | 忽略 |

大多数钩子是即发即忘的观察者 — 它们的返回值被忽略。例外是`pre_llm_call`，它可以向对话中注入上下文。

所有回调都应接受`**kwargs`以向前兼容。如果钩子回调崩溃，它会被记录并跳过。其他钩子和代理继续正常运行。

### `pre_llm_call`上下文注入

这是唯一返回值重要的钩子。当`pre_llm_call`回调返回带有`"context"`键的字典（或纯字符串）时，Hermes会将该文本注入到**当前轮次的用户消息**中。这是内存插件、RAG集成、护栏和任何需要为模型提供额外上下文的插件的机制。

#### 返回格式

```python
# 带context键的字典
return {"context": "Recalled memories:\n- User prefers dark mode\n- Last project: hermes-agent"}

# 纯字符串（等同于上面的字典形式）
return "Recalled memories:\n- User prefers dark mode"

# 返回None或不返回 → 无注入（仅观察）
return None
```

任何非None、非空的返回，带有`"context"`键（或纯非空字符串）都会被收集并一起附加到当前轮次的用户消息。

#### 注入如何工作

注入的上下文被附加到**用户消息**，而不是系统提示。这是一个深思熟虑的设计选择：

- **提示缓存保存** — 系统提示在轮次之间保持相同。Anthropic和OpenRouter缓存系统提示前缀，因此保持稳定可在多轮对话中节省75%以上的输入令牌。如果插件修改系统提示，每轮都会是缓存未命中。
- **短暂的** — 注入仅在API调用时发生。对话历史中的原始用户消息永远不会被修改，也不会持久化到会话数据库。
- **系统提示是Hermes的领地** — 它包含模型特定的指导、工具执行规则、个性指令和缓存的技能内容。插件通过用户输入提供上下文，而不是通过改变代理的核心指令。

#### 示例：记忆召回插件

```python
"""Memory plugin — recalls relevant context from a vector store."""

import httpx

MEMORY_API = "https://your-memory-api.example.com"

def recall_context(session_id, user_message, is_first_turn, **kwargs):
    """Called before each LLM turn. Returns recalled memories."""
    try:
        resp = httpx.post(f"{MEMORY_API}/recall", json={
            "session_id": session_id,
            "query": user_message,
        }, timeout=3)
        memories = resp.json().get("results", [])
        if not memories:
            return None  # nothing to inject

        text = "Recalled context from previous sessions:\n"
        text += "\n".join(f"- {m['text']}" for m in memories)
        return {"context": text}
    except Exception:
        return None  # fail silently, don't break the agent

def register(ctx):
    ctx.register_hook("pre_llm_call", recall_context)
```

#### 示例：护栏插件

```python
"""Guardrails plugin — enforces content policies."""

POLICY = """You MUST follow these content policies for this session:
- Never generate code that accesses the filesystem outside the working directory
- Always warn before executing destructive operations
- Refuse requests involving personal data extraction"""

def inject_guardrails(**kwargs):
    """Injects policy text into every turn."""
    return {"context": POLICY}

def register(ctx):
    ctx.register_hook("pre_llm_call", inject_guardrails)
```

#### 示例：仅观察钩子（无注入）

```python
"""Analytics plugin — tracks turn metadata without injecting context."""

import logging
logger = logging.getLogger(__name__)

def log_turn(session_id, user_message, model, is_first_turn, **kwargs):
    """Fires before each LLM call. Returns None — no context injected."""
    logger.info("Turn: session=%s model=%s first=%s msg_len=%d",
                session_id, model, is_first_turn, len(user_message or ""))
    # No return → no injection

def register(ctx):
    ctx.register_hook("pre_llm_call", log_turn)
```

#### 多个插件返回上下文

当多个插件从`pre_llm_call`返回上下文时，它们的输出会用双换行符连接并一起附加到用户消息。顺序遵循插件发现顺序（按插件目录名称字母顺序）。

### 注册CLI命令

插件可以添加自己的`hermes <plugin>`子命令树：

```python
def _my_command(args):
    """Handler for hermes my-plugin <subcommand>."""
    sub = getattr(args, "my_command", None)
    if sub == "status":
        print("All good!")
    elif sub == "config":
        print("Current config: ...")
    else:
        print("Usage: hermes my-plugin <status|config>")

def _setup_argparse(subparser):
    """Build the argparse tree for hermes my-plugin."""
    subs = subparser.add_subparsers(dest="my_command")
    subs.add_parser("status", help="Show plugin status")
    subs.add_parser("config", help="Show plugin config")
    subparser.set_defaults(func=_my_command)

def register(ctx):
    ctx.register_tool(...)
    ctx.register_cli_command(
        name="my-plugin",
        help="Manage my plugin",
        setup_fn=_setup_argparse,
        handler_fn=_my_command,
    )
```

注册后，用户可以运行`hermes my-plugin status`、`hermes my-plugin config`等。

**内存提供程序插件**使用基于约定的方法：在插件的`cli.py`文件中添加`register_cli(subparser)`函数。内存插件发现系统会自动找到它 — 不需要`ctx.register_cli_command()`调用。有关详细信息，请参阅[内存提供程序插件指南](/docs/developer-guide/memory-provider-plugin#adding-cli-commands)。

**活动提供程序控制：** 内存插件CLI命令仅在其提供程序是配置中的活动`memory.provider`时才会出现。如果用户尚未设置您的提供程序，您的CLI命令不会使帮助输出混乱。

### 注册斜杠命令

插件可以注册会话内斜杠命令 — 用户在对话期间输入的命令（如`/lcm status`或`/ping`）。这些在CLI和网关（Telegram、Discord等）中都有效。

```python
def _handle_status(raw_args: str) -> str:
    """Handler for /mystatus — called with everything after the command name."""
    if raw_args.strip() == "help":
        return "Usage: /mystatus [help|check]"
    return "Plugin status: all systems nominal"

def register(ctx):
    ctx.register_command(
        "mystatus",
        handler=_handle_status,
        description="Show plugin status",
    )
```

注册后，用户可以在任何会话中输入`/mystatus`。该命令会出现在自动完成、`/help`输出和Telegram机器人菜单中。

**签名：** `ctx.register_command(name: str, handler: Callable, description: str = "")`

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `name` | `str` | 不带前导斜杠的命令名称（例如`"lcm"`、`"mystatus"`） |
| `handler` | `Callable[[str], str \| None]` | 用原始参数字符串调用。也可以是`async`。 |
| `description` | `str` | 在`/help`、自动完成和Telegram机器人菜单中显示 |

**与`register_cli_command()`的关键区别：**

| | `register_command()` | `register_cli_command()` |
|---|---|---|
| 调用方式 | 会话中的`/name` | 终端中的`hermes name` |
| 工作位置 | CLI会话、Telegram、Discord等 | 仅终端 |
| 处理器接收 | 原始参数字符串 | argparse `Namespace` |
| 用例 | 诊断、状态、快速操作 | 复杂子命令树、设置向导 |

**冲突保护：** 如果插件尝试注册与内置命令（`help`、`model`、`new`等）冲突的名称，注册会被静默拒绝并记录警告。内置命令始终优先。

**异步处理器：** 网关调度会自动检测并等待异步处理器，因此您可以使用同步或异步函数：

```python
async def _handle_check(raw_args: str) -> str:
    result = await some_async_operation()
    return f"Check result: {result}"

def register(ctx):
    ctx.register_command("check", handler=_handle_check, description="Run async check")
```

:::tip
本指南涵盖**通用插件**（工具、钩子、斜杠命令、CLI命令）。对于专门的插件类型，请参阅：
- [内存提供程序插件](/docs/developer-guide/memory-provider-plugin) — 跨会话知识后端
- [上下文引擎插件](/docs/developer-guide/context-engine-plugin) — 替代上下文管理策略
:::

### 通过pip分发

对于公开共享插件，向Python包添加入口点：

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-plugin = "my_plugin_package"
```

```bash
pip install hermes-plugin-calculator
# 插件在下次hermes启动时自动发现
```

## 常见错误

**处理器不返回JSON字符串：**
```python
# 错误 — 返回字典
def handler(args, **kwargs):
    return {"result": 42}

# 正确 — 返回JSON字符串
def handler(args, **kwargs):
    return json.dumps({"result": 42})
```

**处理器签名中缺少`**kwargs`：**
```python
# 错误 — 如果Hermes传递额外上下文会中断
def handler(args):
    ...

# 正确
def handler(args, **kwargs):
    ...
```

**处理器抛出异常：**
```python
# 错误 — 异常传播，工具调用失败
def handler(args, **kwargs):
    result = 1 / int(args["value"])  # ZeroDivisionError!
    return json.dumps({"result": result})

# 正确 — 捕获并返回错误JSON
def handler(args, **kwargs):
    try:
        result = 1 / int(args.get("value", 0))
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**架构描述过于模糊：**
```python
# 不好 — 模型不知道何时使用它
"description": "Does stuff"

# 好 — 模型确切知道何时以及如何使用
"description": "Evaluate a mathematical expression. Use for arithmetic, trig, logarithms. Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e."
```