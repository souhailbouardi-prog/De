---
sidebar_position: 2
title: "添加工具"
description: "如何向 Hermes Agent 添加新工具 — 模式、处理器、注册和工具集"
---

# 添加工具

在编写工具之前，请问自己：**这应该是一个[技能](creating-skills.md)吗？**

当能力可以表示为指令 + shell 命令 + 现有工具时，将其设为**技能**（arXiv 搜索、git 工作流、Docker 管理、PDF 处理）。

当需要端到端集成 API 密钥、自定义处理逻辑、二进制数据处理或流式处理时，将其设为**工具**（浏览器自动化、TTS、视觉分析）。

## 概述

添加工具涉及**2 个文件**：

1. **`tools/your_tool.py`** — 处理器、模式、检查函数、`registry.register()` 调用
2. **`toolsets.py`** — 将工具名称添加到 `_HERMES_CORE_TOOLS`（或特定工具集）

任何具有顶级 `registry.register()` 调用的 `tools/*.py` 文件都会在启动时自动发现 — 无需手动导入列表。

## 步骤 1：创建工具文件

每个工具文件都遵循相同的结构：

```python
# tools/weather_tool.py
"""天气工具 — 查找位置的当前天气。"""

import json
import os
import logging

logger = logging.getLogger(__name__)


# --- 可用性检查 ---

def check_weather_requirements() -> bool:
    """如果工具的依赖项可用，则返回 True。"""
    return bool(os.getenv("WEATHER_API_KEY"))


# --- 处理器 ---

def weather_tool(location: str, units: str = "metric") -> str:
    """获取位置的天气。返回 JSON 字符串。"""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return json.dumps({"error": "WEATHER_API_KEY not configured"})
    try:
        # ... call weather API ...
        return json.dumps({"location": location, "temp": 22, "units": units})
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- Schema ---

WEATHER_SCHEMA = {
    "name": "weather",
    "description": "Get current weather for a location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or coordinates (e.g. 'London' or '51.5,-0.1')"
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "Temperature units (default: metric)",
                "default": "metric"
            }
        },
        "required": ["location"]
    }
}


# --- Registration ---

from tools.registry import registry

registry.register(
    name="weather",
    toolset="weather",
    schema=WEATHER_SCHEMA,
    handler=lambda args, **kw: weather_tool(
        location=args.get("location", ""),
        units=args.get("units", "metric")),
    check_fn=check_weather_requirements,
    requires_env=["WEATHER_API_KEY"],
)
```

### Key Rules

:::danger Important
- Handlers **MUST** return a JSON string (via `json.dumps()`), never raw dicts
- Errors **MUST** be returned as `{"error": "message"}`, never raised as exceptions
- The `check_fn` is called when building tool definitions — if it returns `False`, the tool is silently excluded
- The `handler` receives `(args: dict, **kwargs)` where `args` is the LLM's tool call arguments
:::

## Step 2: Add to a Toolset

In `toolsets.py`, add the tool name:

```python
# If it should be available on all platforms (CLI + messaging):
_HERMES_CORE_TOOLS = [
    ...
    "weather",  # <-- add here
]

# Or create a new standalone toolset:
"weather": {
    "description": "Weather lookup tools",
    "tools": ["weather"],
    "includes": []
},
```

## ~~Step 3: Add Discovery Import~~ (No longer needed)

Tool modules with a top-level `registry.register()` call are auto-discovered by `discover_builtin_tools()` in `tools/registry.py`. No manual import list to maintain — just create your file in `tools/` and it's picked up at startup.

## Async Handlers

If your handler needs async code, mark it with `is_async=True`:

```python
async def weather_tool_async(location: str) -> str:
    async with aiohttp.ClientSession() as session:
        ...
    return json.dumps(result)

registry.register(
    name="weather",
    toolset="weather",
    schema=WEATHER_SCHEMA,
    handler=lambda args, **kw: weather_tool_async(args.get("location", "")),
    check_fn=check_weather_requirements,
    is_async=True,  # registry calls _run_async() automatically
)
```

The registry handles async bridging transparently — you never call `asyncio.run()` yourself.

## Handlers That Need task_id

Tools that manage per-session state receive `task_id` via `**kwargs`:

```python
def _handle_weather(args, **kw):
    task_id = kw.get("task_id")
    return weather_tool(args.get("location", ""), task_id=task_id)

registry.register(
    name="weather",
    ...
    handler=_handle_weather,
)
```

## Agent-Loop Intercepted Tools

Some tools (`todo`, `memory`, `session_search`, `delegate_task`) need access to per-session agent state. These are intercepted by `run_agent.py` before reaching the registry. The registry still holds their schemas, but `dispatch()` returns a fallback error if the intercept is bypassed.

## Optional: Setup Wizard Integration

If your tool requires an API key, add it to `hermes_cli/config.py`:

```python
OPTIONAL_ENV_VARS = {
    ...
    "WEATHER_API_KEY": {
        "description": "Weather API key for weather lookup",
        "prompt": "Weather API key",
        "url": "https://weatherapi.com/",
        "tools": ["weather"],
        "password": True,
    },
}
```

## Checklist

- [ ] Tool file created with handler, schema, check function, and registration
- [ ] Added to appropriate toolset in `toolsets.py`
- [ ] Discovery import added to `model_tools.py`
- [ ] Handler returns JSON strings, errors returned as `{"error": "..."}`
- [ ] Optional: API key added to `OPTIONAL_ENV_VARS` in `hermes_cli/config.py`
- [ ] Optional: Added to `toolset_distributions.py` for batch processing
- [ ] Tested with `hermes chat -q "Use the weather tool for London"`