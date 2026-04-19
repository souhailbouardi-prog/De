---
sidebar_position: 13
title: "委托与并行工作"
description: "何时以及如何使用子代理委托 — 并行研究、代码审查和多文件工作的模式"
---

# 委托与并行工作

Hermes 可以生成孤立的子代理来并行处理任务。每个子代理都有自己的对话、终端会话和工具集。只有最终摘要返回 — 中间工具调用永远不会进入您的上下文窗口。

有关完整功能参考，请参阅 [子代理委托](/docs/user-guide/features/delegation)。

---

## 何时委托

**适合委托的任务：**
- 推理密集型子任务（调试、代码审查、研究综合）
- 会用中间数据淹没您的上下文的任务
- 并行独立工作流（同时研究 A 和 B）
- 您希望代理不带偏见接近的新鲜上下文任务

**使用其他方法：**
- 单个工具调用 → 直接使用工具
- 步骤之间有逻辑的机械多步工作 → `execute_code`
- 需要用户交互的任务 → 子代理不能使用 `clarify`
- 快速文件编辑 → 直接执行

---

## 模式：并行研究

同时研究三个主题并获取结构化摘要：

```
并行研究以下三个主题：
1. 浏览器外 WebAssembly 的当前状态
2. 2025 年 RISC-V 服务器芯片采用情况
3. 实用量子计算应用

关注最近的发展和关键参与者。
```

在幕后，Hermes 使用：

```python
delegate_task(tasks=[
    {
        "goal": "研究 2025 年浏览器外的 WebAssembly",
        "context": "关注：运行时（Wasmtime、Wasmer）、云/边缘用例、WASI 进展",
        "toolsets": ["web"]
    },
    {
        "goal": "研究 RISC-V 服务器芯片采用情况",
        "context": "关注：服务器芯片出货、云提供商采用、软件生态系统",
        "toolsets": ["web"]
    },
    {
        "goal": "研究实用量子计算应用",
        "context": "关注：错误校正突破、实际用例、关键公司",
        "toolsets": ["web"]
    }
])
```

所有三个任务并行运行。每个子代理独立搜索网络并返回摘要。父代理然后将它们合成一个连贯的简报。

---

## 模式：代码审查

将安全审查委托给一个新鲜上下文的子代理，该代理不带先入之见地接近代码：

```
审查 src/auth/ 目录中的身份验证模块以查找安全问题。
检查 SQL 注入、JWT 验证问题、密码处理和会话管理。
修复您发现的任何问题并运行测试。
```

关键是 `context` 字段 — 它必须包含子代理需要的一切：

```python
delegate_task(
    goal="审查 src/auth/ 中的安全问题并修复发现的问题",
    context="""项目位于 /home/user/webapp。Python 3.11、Flask、PyJWT、bcrypt。
    认证文件：src/auth/login.py、src/auth/jwt.py、src/auth/middleware.py
    测试命令：pytest tests/auth/ -v
    关注：SQL 注入、JWT 验证、密码哈希、会话管理。
    修复发现的问题并验证测试通过。""",
    toolsets=["terminal", "file"]
)
```

:::warning 上下文问题
子代理对您的对话**一无所知**。它们完全从头开始。如果您委托"修复我们讨论的 bug"，子代理不知道您指的是什么 bug。始终明确传递文件路径、错误消息、项目结构和约束。
:::

---

## 模式：比较替代方案

并行评估同一问题的多种方法，然后选择最佳方案：

```
我需要为我们的 Django 应用添加全文搜索。并行评估三种方法：
1. PostgreSQL tsvector（内置）
2. 通过 django-elasticsearch-dsl 的 Elasticsearch
3. 通过 meilisearch-python 的 Meilisearch

对于每种方法：设置复杂性、查询能力、资源要求和维护开销。比较它们并推荐一种。
```

每个子代理独立研究一个选项。由于它们是隔离的，因此没有交叉污染 — 每个评估都基于其自身的优点。父代理获取所有三个摘要并进行比较。

---

## 模式：多文件重构

将大型重构任务拆分到并行子代理中，每个子代理处理代码库的不同部分：

```python
delegate_task(tasks=[
    {
        "goal": "重构所有 API 端点处理程序以使用新的响应格式",
        "context": """项目位于 /home/user/api-server。
        文件：src/handlers/users.py、src/handlers/auth.py、src/handlers/billing.py
        旧格式：return {"data": result, "status": "ok"}
        新格式：return APIResponse(data=result, status=200).to_dict()
        导入：from src.responses import APIResponse
        之后运行测试：pytest tests/handlers/ -v""",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "更新所有客户端 SDK 方法以处理新的响应格式",
        "context": """项目位于 /home/user/api-server。
        文件：sdk/python/client.py、sdk/python/models.py
        旧解析：result = response.json()["data"]
        新解析：result = response.json()["data"]（相同键，但添加状态码检查）
        还更新 sdk/python/tests/test_client.py""",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "更新 API 文档以反映新的响应格式",
        "context": """项目位于 /home/user/api-server。
        文档位于：docs/api/。格式：带代码示例的 Markdown。
        将所有响应示例从旧格式更新为新格式。
        在 docs/api/overview.md 中添加一个 '响应格式' 部分，解释模式。""",
        "toolsets": ["terminal", "file"]
    }
])
```

:::tip
每个子代理都有自己的终端会话。只要它们编辑不同的文件，它们就可以在同一个项目目录中工作而不会互相干扰。如果两个子代理可能接触同一个文件，请在并行工作完成后自己处理该文件。
:::

---

## 模式：收集然后分析

使用 `execute_code` 进行机械数据收集，然后委托推理密集型分析：

```python
# 步骤 1：机械收集（这里使用 execute_code 更好 — 不需要推理）
execute_code("""
from hermes_tools import web_search, web_extract

results = []
for query in ["AI funding Q1 2026", "AI startup acquisitions 2026", "AI IPOs 2026"]:
    r = web_search(query, limit=5)
    for item in r["data"]["web"]:
        results.append({"title": item["title"], "url": item["url"], "desc": item["description"]})

# 从最相关的前 5 个中提取完整内容
urls = [r["url"] for r in results[:5]]
content = web_extract(urls)

# 保存以供分析步骤使用
import json
with open("/tmp/ai-funding-data.json", "w") as f:
    json.dump({"search_results": results, "extracted": content["results"]}, f)
print(f"收集了 {len(results)} 个结果，提取了 {len(content['results'])} 个页面")
""")

# 步骤 2：推理密集型分析（这里使用委托更好）
delegate_task(
    goal="分析 AI  funding 数据并撰写市场报告",
    context="""/tmp/ai-funding-data.json 中的原始数据包含关于 2026 年 Q1 AI  funding、收购和 IPO 的搜索结果和提取的网页。
    撰写结构化市场报告：关键交易、趋势、知名参与者和展望。
    关注超过 1 亿美元的交易。""",
    toolsets=["terminal", "file"]
)
```

这通常是最高效的模式：`execute_code` 以低成本处理 10+ 个顺序工具调用，然后子代理使用干净的上下文执行单个昂贵的推理任务。

---

## 工具集选择

根据子代理的需要选择工具集：

| 任务类型 | 工具集 | 原因 |
|-----------|----------|-----|
| 网络研究 | `["web"]` | 仅 web_search + web_extract |
| 代码工作 | `["terminal", "file"]` | Shell 访问 + 文件操作 |
| 全栈 | `["terminal", "file", "web"]` | 除消息传递外的一切 |
| 只读分析 | `["file"]` | 只能读取文件，无 shell |

限制工具集使子代理保持专注并防止意外副作用（例如研究子代理运行 shell 命令）。

---

## 约束

- **默认 3 个并行任务** — 批次默认为 3 个并发子代理（可通过 config.yaml 中的 `delegation.max_concurrent_children` 配置）
- **无嵌套** — 子代理不能调用 `delegate_task`、`clarify`、`memory`、`send_message` 或 `execute_code`
- **独立终端** — 每个子代理都有自己的终端会话，具有独立的工作目录和状态
- **无对话历史** — 子代理只看到您在 `goal` 和 `context` 中放入的内容
- **默认 50 次迭代** — 对于简单任务，设置较低的 `max_iterations` 以节省成本

---

## 提示

**目标要具体**。"修复 bug" 太模糊。"修复 api/handlers.py 第 47 行中的 TypeError，其中 process_request() 从 parse_body() 收到 None" 给子代理足够的工作内容。

**包含文件路径**。子代理不知道您的项目结构。始终包含相关文件的绝对路径、项目根目录和测试命令。

**使用委托进行上下文隔离**。有时您想要一个全新的视角。委托迫使您清晰地表达问题，而子代理会不带您对话中积累的假设来接近它。

**检查结果**。子代理摘要是摘要 — 仅此而已。如果子代理说"修复了 bug 并且测试通过"，请通过自己运行测试或阅读差异来验证。

---

*有关完整的委托参考 — 所有参数、ACP 集成和高级配置 — 请参阅 [子代理委托](/docs/user-guide/features/delegation)。*