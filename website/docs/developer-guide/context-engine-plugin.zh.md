---
sidebar_position: 9
title: "上下文引擎插件"
description: "如何构建一个替换内置 ContextCompressor 的上下文引擎插件"
---

# 构建上下文引擎插件

上下文引擎插件可以替换内置的 `ContextCompressor`，使用替代策略来管理对话上下文。例如，无损上下文管理 (LCM) 引擎可以构建知识 DAG（有向无环图），而不是使用有损摘要。

## 工作原理

代理的上下文管理基于 `ContextEngine` ABC（抽象基类），位于 `agent/context_engine.py`。内置的 `ContextCompressor` 是默认实现。插件引擎必须实现相同的接口。

同一时间只能有**一个**上下文引擎处于活动状态。选择是通过配置驱动的：

```yaml
# config.yaml
context:
  engine: "compressor"    # 默认内置引擎
  engine: "lcm"           # 激活名为 "lcm" 的插件引擎
```

插件引擎**永远不会自动激活**——用户必须显式地将 `context.engine` 设置为插件的名称。

## 目录结构

每个上下文引擎位于 `plugins/context_engine/<name>/` 目录中：

```
plugins/context_engine/lcm/
├── __init__.py      # 导出 ContextEngine 子类
├── plugin.yaml      # 元数据（名称、描述、版本）
└── ...              # 引擎需要的其他模块
```

## ContextEngine 抽象基类

你的引擎必须实现以下**必需**方法：

```python
from agent.context_engine import ContextEngine

class LCMEngine(ContextEngine):

    @property
    def name(self) -> str:
        """简短标识符，例如 'lcm'。必须与 config.yaml 中的值匹配。"""
        return "lcm"

    def update_from_response(self, usage: dict) -> None:
        """每次 LLM 调用后使用 usage 字典调用。

        从响应中更新 self.last_prompt_tokens、self.last_completion_tokens
        和 self.last_total_tokens。
        """

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """如果本轮应该触发压缩，则返回 True。"""

    def compress(self, messages: list, current_tokens: int = None) -> list:
        """压缩消息列表并返回一个新的（可能更短的）列表。

        返回的列表必须是有效的 OpenAI 格式消息序列。
        """
```

### 引擎必须维护的类属性

代理直接读取这些属性用于显示和日志记录：

```python
last_prompt_tokens: int = 0
last_completion_tokens: int = 0
last_total_tokens: int = 0
threshold_tokens: int = 0        # 压缩触发的阈值
context_length: int = 0          # 模型的完整上下文窗口
compression_count: int = 0       # compress() 运行的次数
```

### 可选方法

这些方法在 ABC 中都有合理的默认实现。根据需要进行重写：

| 方法 | 默认实现 | 何时重写 |
|--------|---------|--------------|
| `on_session_start(session_id, **kwargs)` | 空操作 | 需要加载持久化状态（DAG、数据库）时 |
| `on_session_end(session_id, messages)` | 空操作 | 需要刷新状态、关闭连接时 |
| `on_session_reset()` | 重置令牌计数器 | 有会话级状态需要清除时 |
| `update_model(model, context_length, ...)` | 更新 context_length + threshold | 需要在模型切换时重新计算预算时 |
| `get_tool_schemas()` | 返回 `[]` | 引擎提供代理可调用的工具（例如 `lcm_grep`）时 |
| `handle_tool_call(name, args, **kwargs)` | 返回错误 JSON | 实现工具处理程序时 |
| `should_compress_preflight(messages)` | 返回 `False` | 可以在 API 调用前进行廉价估算时 |
| `get_status()` | 标准令牌/阈值字典 | 有自定义指标要公开时 |

## 引擎工具

上下文引擎可以公开代理直接调用的工具。从 `get_tool_schemas()` 返回工具模式，并在 `handle_tool_call()` 中处理调用：

```python
def get_tool_schemas(self):
    return [{
        "name": "lcm_grep",
        "description": "搜索上下文知识图谱",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"}
            },
            "required": ["query"],
        },
    }]

def handle_tool_call(self, name, args, **kwargs):
    if name == "lcm_grep":
        results = self._search_dag(args["query"])
        return json.dumps({"results": results})
    return json.dumps({"error": f"Unknown tool: {name}"})
```

引擎工具在启动时被注入到代理的工具列表中并自动分发——不需要注册表注册。

## 注册

### 通过目录（推荐）

将你的引擎放在 `plugins/context_engine/<name>/` 目录中。`__init__.py` 必须导出一个 `ContextEngine` 子类。发现系统会自动找到并实例化它。

### 通过通用插件系统

通用插件也可以注册上下文引擎：

```python
def register(ctx):
    engine = LCMEngine(context_length=200000)
    ctx.register_context_engine(engine)
```

只能注册一个引擎。尝试注册第二个引擎的插件会被拒绝并发出警告。

## 生命周期

```
1. 引擎实例化（插件加载或目录发现）
2. on_session_start() — 对话开始
3. update_from_response() — 每次 API 调用后
4. should_compress() — 每轮检查
5. compress() — 当 should_compress() 返回 True 时调用
6. on_session_end() — 会话边界（CLI 退出、/reset、网关过期）
```

`on_session_reset()` 在 `/new` 或 `/reset` 时调用，用于清除会话级状态而不需要完全关闭。

## 配置

用户可以通过 `hermes plugins` → Provider Plugins → Context Engine 选择你的引擎，或通过编辑 `config.yaml`：

```yaml
context:
  engine: "lcm"   # 必须与引擎的 name 属性匹配
```

`compression` 配置块（`compression.threshold`、`compression.protect_last_n` 等）特定于内置的 `ContextCompressor`。你的引擎如果需要，应该定义自己的配置格式，在初始化期间从 `config.yaml` 读取。

## 测试

```python
from agent.context_engine import ContextEngine

def test_engine_satisfies_abc():
    engine = YourEngine(context_length=200000)
    assert isinstance(engine, ContextEngine)
    assert engine.name == "your-name"

def test_compress_returns_valid_messages():
    engine = YourEngine(context_length=200000)
    msgs = [{"role": "user", "content": "hello"}]
    result = engine.compress(msgs)
    assert isinstance(result, list)
    assert all("role" in m for m in result)
```

请参阅 `tests/agent/test_context_engine.py` 获取完整的 ABC 合约测试套件。

## 另请参阅

- [上下文压缩和缓存](/docs/developer-guide/context-compression-and-caching) — 内置压缩器的工作原理
- [内存提供程序插件](/docs/developer-guide/memory-provider-plugin) — 内存的类似单选插件系统
- [插件](/docs/user-guide/features/plugins) — 通用插件系统概述