---
sidebar_position: 9
sidebar_label: "构建插件"
title: "构建 Hermes 插件"
description: "构建完整 Hermes 插件的分步指南，包括工具、钩子、数据文件和技能"
---

# 构建 Hermes 插件

本指南将引导您从头开始构建一个完整的 Hermes 插件。到最后，您将拥有一个可工作的插件，包含多个工具、生命周期钩子、打包的数据文件和一个捆绑的技能 — 插件系统支持的所有功能。

## 您将构建什么

一个**计算器**插件，包含两个工具：
- `calculate` — 评估数学表达式 (`2**16`, `sqrt(144)`, `pi * 5**2`)
- `unit_convert` — 单位转换 (`100 F → 37.78 C`, `5 km → 3.11 mi`)

加上一个记录每个工具调用的钩子，以及一个捆绑的技能文件。

## 步骤 1：创建插件目录

```bash
mkdir -p ~/.hermes/plugins/calculator
cd ~/.hermes/plugins/calculator
```

## 步骤 2：编写清单

创建 `plugin.yaml`：

```yaml
name: calculator
version: 1.0.0
description: 数学计算器 — 评估表达式和转换单位
provides_tools:
  - calculate
  - unit_convert
provides_hooks:
  - post_tool_call
```

这告诉 Hermes："我是一个名为 calculator 的插件，我提供工具和钩子。" `provides_tools` 和 `provides_hooks` 字段是插件注册的内容列表。

您可以添加的可选字段：
```yaml
author: 您的姓名
requires_env:          # 根据环境变量控制加载；在安装期间提示
  - SOME_API_KEY       # 简单格式 — 如果缺失则禁用插件
  - name: OTHER_KEY    # 丰富格式 — 在安装期间显示描述/URL
    description: "Other 服务的密钥"
    url: "https://other.com/keys"
    secret: true
```

## 步骤 3：编写工具架构

创建 `schemas.py` — 这是 LLM 读取以决定何时调用您的工具的内容：

```python
"""工具架构 — LLM 看到的内容。"""

CALCULATE = {
    "name": "calculate",
    "description": (
        "评估数学表达式并返回结果。"
        "支持算术（+、-、*、/、**）、函数（sqrt、sin、cos、"
        "log、abs、round、floor、ceil）和常数（pi、e）。"
        "对用户询问的任何数学问题使用此工具。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要评估的数学表达式（例如，'2**10'、'sqrt(144)'）",
            },
        },
        "required": ["expression"],
    },
}

UNIT_CONVERT = {
    "name": "unit_convert",
    "description": (
        "在单位之间转换值。支持长度（m、km、mi、ft、in）、"
        "重量（kg、lb、oz、g）、温度（C、F、K）、数据（B、KB、MB、GB、TB）、"
        "和时间（s、min、hr、day）。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "要转换的数值",
            },
            "from_unit": {
                "type": "string",
                "description": "源单位（例如，'km'、'lb'、'F'、'GB'）",
            },
            "to_unit": {
                "type": "string",
                "description": "目标单位（例如，'mi'、'kg'、'C'、'MB'）",
            },
        },
        "required": ["value", "from_unit", "to_unit"],
    },
}
```

**为什么架构很重要：** `description` 字段是 LLM 决定何时使用您的工具的方式。具体说明它做什么以及何时使用它。`parameters` 定义 LLM 传递的参数。

## 步骤 4：编写工具处理程序

创建 `tools.py` — 这是 LLM 调用您的工具时实际执行的代码：

```python
"""工具处理程序 — LLM 调用每个工具时运行的代码。"""

import json
import math

# 用于表达式评估的安全全局变量 — 无文件/网络访问
_SAFE_MATH = {
    "abs": abs, "round": round, "min": min, "max": max,
    "pow": pow, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan": math.tan, "log": math.log, "log2": math.log2, "log10": math.log10,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e,
    "factorial": math.factorial,
}


def calculate(args: dict, **kwargs) -> str:
    """安全地评估数学表达式。

    处理程序的规则：
    1. 接收 args (dict) — LLM 传递的参数
    2. 执行工作
    3. 返回 JSON 字符串 — 始终如此，即使在错误时
    4. 接受 **kwargs 以实现向前兼容性
    """
    expression = args.get("expression", "").strip()
    if not expression:
        return json.dumps({"error": "未提供表达式"})

    try:
        result = eval(expression, {"__builtins__": {}}, _SAFE_MATH)
        return json.dumps({"expression": expression, "result": result})
    except ZeroDivisionError:
        return json.dumps({"expression": expression, "error": "除以零"})
    except Exception as e:
        return json.dumps({"expression": expression, "error": f"无效：{e}"})


# 转换表 — 值以基本单位表示
_LENGTH = {"m": 1, "km": 1000, "mi": 1609.34, "ft": 0.3048, "in": 0.0254, "cm": 0.01}
_WEIGHT = {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.0283495}
_DATA = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
_TIME = {"s": 1, "ms": 0.001, "min": 60, "hr": 3600, "day": 86400}


def _convert_temp(value, from_u, to_u):
    # 归一化为摄氏度
    c = {"F": (value - 32) * 5/9, "K": value - 273.15}.get(from_u, value)
    # 转换为目标
    return {"F": c * 9/5 + 32, "K": c + 273.15}.get(to_u, c)


def unit_convert(args: dict, **kwargs) -> str:
    """在单位之间转换。"""
    value = args.get("value")
    from_unit = args.get("from_unit", "").strip()
    to_unit = args.get("to_unit", "").strip()

    if value is None or not from_unit or not to_unit:
        return json.dumps({"error": "需要 value、from_unit 和 to_unit"})

    try:
        # 温度
        if from_unit.upper() in {"C","F","K"} and to_unit.upper() in {"C","F","K"}:
            result = _convert_temp(float(value), from_unit.upper(), to_unit.upper())
            return json.dumps({"input": f"{value} {from_unit}", "result": round(result, 4),
                             "output": f"{round(result, 4)} {to_unit}"})

        # 基于比率的转换
        for table in (_LENGTH, _WEIGHT, _DATA, _TIME):
            lc = {k.lower(): v for k, v in table.items()}
            if from_unit.lower() in lc and to_unit.lower() in lc:
                result = float(value) * lc[from_unit.lower()] / lc[to_unit.lower()]
                return json.dumps({"input": f"{value} {from_unit}",
                                 "result": round(result, 6),
                                 "output": f"{round(result, 6)} {to_unit}"})

        return json.dumps({"error": f"无法转换 {from_unit} → {to_unit}"})
    except Exception as e:
        return json.dumps({"error": f"转换失败：{e}"})
```

**处理程序的关键规则：**
1. **签名：** `def my_handler(args: dict, **kwargs) -> str`
2. **返回：** 始终是 JSON 字符串。成功和错误都一样。
3. **永不引发：** 捕获所有异常，改为返回错误 JSON。
4. **接受 `**kwargs`：** Hermes 将来可能会传递额外的上下文。

## 步骤 5：编写注册

创建 `__init__.py` — 这将架构连接到处理程序：

```python
"""计算器插件 — 注册。"""

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)

# 通过钩子跟踪工具使用
_call_log = []

def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """钩子：在每次工具调用后运行（不仅仅是我们的）。"""
    _call_log.append({"tool": tool_name, "session": task_id})
    if len(_call_log) > 100:
        _call_log.pop(0)
    logger.debug("工具调用：%s（会话 %s）", tool_name, task_id)


def register(ctx):
    """将架构连接到处理程序并注册钩子。"""
    ctx.register_tool(name="calculate", toolset="calculator",
                      schema=schemas.CALCULATE, handler=tools.calculate)
    ctx.register_tool(name="unit_convert", toolset="calculator",
                      schema=schemas.UNIT_CONVERT, handler=tools.unit_convert)

    # 此钩子为所有工具调用触发，不仅仅是我们的
    ctx.register_hook("post_tool_call", _on_post_tool_call)
```

**`register()` 做什么：**
- 在启动时精确调用一次
- `ctx.register_tool()` 将您的工具放入注册表 — 模型立即看到它
- `ctx.register_hook()` 订阅生命周期事件
- `ctx.register_cli_command()` 注册 CLI 子命令（例如，`hermes my-plugin <subcommand>`）
- 如果此函数崩溃，插件被禁用但 Hermes 继续正常运行

## 步骤 6：测试它

启动 Hermes：

```bash
hermes
```

您应该在横幅的工具列表中看到 `calculator: calculate, unit_convert`。

尝试这些提示：
```
2 的 16 次方是多少？
将 100 华氏度转换为摄氏度
2 乘以 pi 的平方根是多少？
1.5 太字节是多少千兆字节？
```

检查插件状态：
```
/plugins
```

输出：
```
插件（1）：
  ✓ calculator v1.0.0（2 个工具，1 个钩子）
```

## 您插件的最终结构

```
~/.hermes/plugins/calculator/
├── plugin.yaml      # "我是计算器，我提供工具和钩子"
├── __init__.py      # 连接：架构 → 处理程序，注册钩子
├── schemas.py       # LLM 读取的内容（描述 + 参数规范）
└── tools.py         # 运行的内容（calculate、unit_convert 函数）
```

四个文件，清晰的分离：
- **清单** 声明插件是什么
- **架构** 为 LLM 描述工具
- **处理程序** 实现实际逻辑
- **注册** 连接一切

## 插件还能做什么？

### 打包数据文件

将任何文件放在插件目录中，并在导入时读取它们：

```python
# 在 tools.py 或 __init__.py 中
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_DATA_FILE = _PLUGIN_DIR / "data" / "languages.yaml"

with open(_DATA_FILE) as f:
    _DATA = yaml.safe_load(f)
```

### 捆绑技能

插件可以提供智能体通过 `skill_view("plugin:skill")` 加载的技能文件。在您的 `__init__.py` 中注册它们：

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

智能体现在可以使用它们的命名空间名称加载您的技能：

```python
skill_view("my-plugin:my-workflow")   # → 插件的版本
skill_view("my-workflow")              # → 内置版本（未更改）
```

**关键属性：**
- 插件技能是**只读的** — 它们不会进入 `~/.hermes/skills/` 并且不能通过 `skill_manage` 编辑。
- 插件技能**不会**在系统提示的 `<available_skills>` 索引中列出 — 它们是选择加入的显式加载。
- 裸技能名称不受影响 — 命名空间防止与内置技能的名称冲突。
- 当智能体加载插件技能时，会预先添加一个捆绑上下文横幅，列出来自同一插件的同级技能。

:::tip 传统模式
旧的 `shutil.copy2` 模式（将技能复制到 `~/.hermes/skills/`）仍然有效，但会创建与内置技能的名称冲突风险。对于新插件，首选 `ctx.register_skill()`。
:::

### 基于环境变量限制

如果您的插件需要 API 密钥：

```yaml
# plugin.yaml — 简单格式（向后兼容）
requires_env:
  - WEATHER_API_KEY
```

如果未设置 `WEATHER_API_KEY`，插件会被禁用并显示清晰的消息。不会崩溃，智能体中没有错误 — 只是"插件天气已禁用（缺失：WEATHER_API_KEY）"。

当用户运行 `hermes plugins install` 时，他们会**被交互式提示**输入任何缺失的 `requires_env` 变量。值会自动保存到 `.env`。

为了更好的安装体验，使用带有描述和注册 URL 的丰富格式：

```yaml
# plugin.yaml — 丰富格式
requires_env:
  - name: WEATHER_API_KEY
    description: "OpenWeather 的 API 密钥"
    url: "https://openweathermap.org/api"
    secret: true
```

| 字段 | 必需 | 描述 |
|-------|----------|-------------|
| `name` | 是 | 环境变量名称 |
| `description` | 否 | 在安装提示期间显示给用户 |
| `url` | 否 | 在哪里获取凭据 |
| `secret` | 否 | 如果为 `true`，输入被隐藏（像密码字段一样） |

两种格式可以在同一列表中混合使用。已设置的变量会被静默跳过。

### 条件工具可用性

对于依赖于可选库的工具：

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

每个钩子都在 **[事件钩子参考](/docs/user-guide/features/hooks#plugin-hooks)** 中完整记录 — 回调签名、参数表、每个钩子何时精确触发以及示例。以下是摘要：

| 钩子 | 触发时 | 回调签名 | 返回 |
|------|-----------|-------------------|---------|
| [`pre_tool_call`](/docs/user-guide/features/hooks#pre_tool_call) | 任何工具执行之前 | `tool_name: str, args: dict, task_id: str` | 忽略 |
| [`post_tool_call`](/docs/user-guide/features/hooks#post_tool_call) | 任何工具返回之后 | `tool_name: str, args: dict, result: str, task_id: str` | 忽略 |
| [`pre_llm_call`](/docs/user-guide/features/hooks#pre_llm_call) | 每轮一次，在工具调用循环之前 | `session_id: str, user_message: str, conversation_history: list, is_first_turn: bool, model: str, platform: str` | [上下文注入](#pre_llm_call-上下文注入) |
| [`post_llm_call`](/docs/user-guide/features/hooks#post_llm_call) | 每轮一次，在工具调用循环之后（仅成功轮次） | `session_id: str, user_message: str, assistant_response: str, conversation_history: list, model: str, platform: str` | 忽略 |
| [`on_session_start`](/docs/user-guide/features/hooks#on_session_start) | 创建新会话（仅第一轮） | `session_id: str, model: str, platform: str` | 忽略 |
| [`on_session_end`](/docs/user-guide/features/hooks#on_session_end) | 每次 `run_conversation` 调用的结束 + CLI 退出 | `session_id: str, completed: bool, interrupted: bool, model: str, platform: str` | 忽略 |
| [`pre_api_request`](/docs/user-guide/features/hooks#pre_api_request) | 每次 HTTP 请求到 LLM 提供商之前 | `method: str, url: str, headers: dict, body: dict` | 忽略 |
| [`post_api_request`](/docs/user-guide/features/hooks#post_api_request) | 每次 HTTP 响应从 LLM 提供商之后 | `method: str, url: str, status_code: int, response: dict` | 忽略 |

大多数钩子是触发即忘记的观察者 — 它们的返回值被忽略。例外是 `pre_llm_call`，它可以将上下文注入到对话中。

所有回调都应该接受 `**kwargs` 以实现向前兼容性。如果钩子回调崩溃，它会被记录并跳过。其他钩子和智能体继续正常运行。

### `pre_llm_call` 上下文注入

这是唯一返回值重要的钩子。当 `pre_llm_call` 回调返回带有 `"context"` 键的字典（或纯字符串）时，Hermes 会将该文本注入到**当前轮次的用户消息**中。这是记忆插件、RAG 集成、护栏以及任何需要为模型提供额外上下文的插件的机制。

#### 返回格式

```python
# 带有 context 键的字典
return {"context": "回忆的记忆：\n- 用户偏好深色模式\n- 上次项目：hermes-agent"}

# 纯字符串（等同于上面的字典形式）
return "回忆的记忆：\n- 用户偏好深色模式"

# 返回 None 或不返回 → 无注入（仅观察者）
return None
```

任何非 None、非空的带有 `"context"` 键（或非空纯字符串）的返回都会被收集并附加到当前轮次的用户消息。

#### 注入如何工作

注入的上下文被附加到**用户消息**，而不是系统提示。这是一个深思熟虑的设计选择：

- **提示缓存保留** — 系统提示在轮次之间保持相同。Anthropic 和 OpenRouter 缓存系统提示前缀，因此保持稳定可以在多轮对话中节省 75%+ 的输入令牌。如果插件修改了系统提示，每轮都会是缓存未命中。
- **短暂的** — 注入仅在 API 调用时间发生。对话历史中的原始用户消息永远不会被改变，并且没有任何内容被持久化到会话数据库。
- **系统提示是 Hermes 的领域** — 它包含模型特定的指导、工具执行规则、个性指令和缓存的技能内容。插件与用户的输入一起提供上下文，而不是通过更改智能体的核心指令。

#### 示例：记忆回忆插件

```python
"""记忆插件 — 从向量存储中回忆相关上下文。"""

import httpx

MEMORY_API = "https://your-memory-api.example.com"

def recall_context(session_id, user_message, is_first_turn, **kwargs):
    """在每个 LLM 轮次之前调用。返回回忆的记忆。"""
    try:
        resp = httpx.post(f"{MEMORY_API}/recall", json={
            "session_id": session_id,
            "query": user_message,
        }, timeout=3)
        memories = resp.json().get("results", [])
        if not memories:
            return None  # 没有内容可注入

        text = "从先前会话回忆的上下文：\n"
        text += "\n".join(f"- {m['text']}" for m in memories)
        return {"context": text}
    except Exception:
        return None  # 静默失败，不要破坏智能体

def register(ctx):
    ctx.register_hook("pre_llm_call", recall_context)
```

#### 示例：护栏插件

```python
"""护栏插件 — 强制执行内容策略。"""

POLICY = """您必须在此会话中遵循这些内容策略：
- 永远不要生成访问工作目录之外文件系统的代码
- 在执行破坏性操作之前始终警告
- 拒绝涉及个人数据提取的请求"""

def inject_guardrails(**kwargs):
    """将策略文本注入到每个轮次。"""
    return {"context": POLICY}

def register(ctx):
    ctx.register_hook("pre_llm_call", inject_guardrails)
```

#### 示例：仅观察者钩子（无注入）

```python
"""分析插件 — 跟踪轮次元数据而不注入上下文。"""

import logging
logger = logging.getLogger(__name__)

def log_turn(session_id, user_message, model, is_first_turn, **kwargs):
    """在每个 LLM 调用之前触发。返回 None — 无上下文注入。"""
    logger.info("轮次：会话=%s 模型=%s 首次=%s 消息长度=%d",
                session_id, model, is_first_turn, len(user_message or ""))
    # 无返回 → 无注入

def register(ctx):
    ctx.register_hook("pre_llm_call", log_turn)
```

#### 多个插件返回上下文

当多个插件从 `pre_llm_call` 返回上下文时，它们的输出会用双换行符连接并一起附加到用户消息。顺序遵循插件发现顺序（按插件目录名称字母顺序）。

### 注册 CLI 命令

插件可以添加自己的 `hermes <plugin>` 子命令树：

```python
def _my_command(args):
    """hermes my-plugin <subcommand> 的处理程序。"""
    sub = getattr(args, "my_command", None)
    if sub == "status":
        print("一切正常！")
    elif sub == "config":
        print("当前配置：...")
    else:
        print("用法：hermes my-plugin <status|config>")

def _setup_argparse(subparser):
    """为 hermes my-plugin 构建 argparse 树。"""
    subs = subparser.add_subparsers(dest="my_command")
    subs.add_parser("status", help="显示插件状态")
    subs.add_parser("config", help="显示插件配置")
    subparser.set_defaults(func=_my_command)

def register(ctx):
    ctx.register_tool(...)
    ctx.register_cli_command("my-plugin", _setup_argparse)
```

现在用户可以运行：

```bash
hermes my-plugin status
hermes my-plugin config
```

## 打包和分发

### 创建可安装包

```bash
cd ~/.hermes/plugins/calculator
python -m build
```

这创建 `dist/` 目录，其中包含 `.whl` 文件。

### 发布到 PyPI

```bash
python -m twine upload dist/*
```

### 本地安装

```bash
hermes plugins install ~/.hermes/plugins/calculator/dist/calculator-1.0.0-py3-none-any.whl
```

## 高级主题

### 插件间通信

插件可以通过共享状态进行通信：

```python
# 在插件 A 中
def register(ctx):
    ctx.set_shared_state("my_data", {"key": "value"})

# 在插件 B 中
def register(ctx):
    data = ctx.get_shared_state("my_data")  # {"key": "value"}
```

### 动态工具注册

根据配置注册不同的工具：

```python
def register(ctx):
    if os.getenv("ENABLE_ADVANCED"):
        ctx.register_tool(name="advanced_tool", ...)
    else:
        ctx.register_tool(name="basic_tool", ...)
```

### 错误处理

始终优雅地处理错误：

```python
def my_handler(args: dict, **kwargs) -> str:
    try:
        # 执行工作
        return json.dumps({"result": "成功"})
    except Exception as e:
        logger.error(f"工具失败：{e}")
        return json.dumps({"error": f"处理失败：{e}"})
```

## 故障排除

### 插件未加载

检查：
- `plugin.yaml` 语法是否正确
- Python 语法是否正确
- `requires_env` 变量是否已设置（如果需要）
- 插件目录结构是否正确

### 工具未显示

检查：
- 工具是否在 `provides_tools` 中列出
- `register()` 是否调用 `ctx.register_tool()`
- `check_fn` 是否返回 `True`（如果使用）

### 钩子未触发

检查：
- 钩子是否在 `provides_hooks` 中列出
- `register()` 是否调用 `ctx.register_hook()`
- 钩子名称是否正确

## 下一步

- [事件钩子参考](/docs/user-guide/features/hooks#plugin-hooks) — 所有钩子的完整文档
- [工具参考](/docs/reference/tools-reference) — 内置工具示例
- [技能系统](/docs/user-guide/features/skills) — 如何创建技能
- [配置](/docs/user-guide/configuration) — Hermes 配置选项

---

*有问题或建议？在 [GitHub](https://github.com/NousResearch/hermes-agent) 上打开 issue 或 PR。*