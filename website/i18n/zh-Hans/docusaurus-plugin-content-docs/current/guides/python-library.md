---
sidebar_position: 5
title: "将 Hermes 用作 Python 库"
description: "将 AIAgent 嵌入到您自己的 Python 脚本、Web 应用或自动化管道中 — 无需 CLI"
---

# 将 Hermes 用作 Python 库

Hermes 不仅仅是一个 CLI 工具。您可以直接导入 `AIAgent` 并以编程方式在您自己的 Python 脚本、Web 应用程序或自动化管道中使用它。本指南向您展示如何操作。

---

## 安装

直接从仓库安装 Hermes：

```bash
pip install git+https://github.com/NousResearch/hermes-agent.git
```

或使用 [uv](https://docs.astral.sh/uv/)：

```bash
uv pip install git+https://github.com/NousResearch/hermes-agent.git
```

您还可以将其固定在您的 `requirements.txt` 中：

```text
hermes-agent @ git+https://github.com/NousResearch/hermes-agent.git
```

:::tip
使用 Hermes 作为库时，需要与 CLI 相同的环境变量。至少设置 `OPENROUTER_API_KEY`（或如果使用直接提供商访问，则设置 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）。
:::

---

## 基本用法

使用 Hermes 的最简单方法是 `chat()` 方法 — 传递消息，获取字符串返回：

```python
from run_agent import AIAgent

agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
)
response = agent.chat("What is the capital of France?")
print(response)
```

`chat()` 在内部处理完整的对话循环 — 工具调用、重试，所有内容 — 并仅返回最终的文本响应。

:::warning
在将 Hermes 嵌入到您自己的代码中时，始终设置 `quiet_mode=True`。否则，智能体会打印 CLI 旋转器、进度指示器和其他终端输出，这会使您应用程序的输出变得混乱。
:::

---

## 完整对话控制

要对对话进行更多控制，请直接使用 `run_conversation()`。它返回一个包含完整响应、消息历史和元数据的字典：

```python
gent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
)

result = agent.run_conversation(
    user_message="Search for recent Python 3.13 features",
    task_id="my-task-1",
)

print(result["final_response"])
print(f"Messages exchanged: {len(result['messages'])}")
```

返回的字典包含：
- **`final_response`** — 智能体的最终文本回复
- **`messages`** — 完整的消息历史（系统、用户、助手、工具调用）
- **`task_id`** — 用于 VM 隔离的任务标识符

您还可以传递自定义系统消息，该消息会覆盖该调用的临时系统提示：

```python
result = agent.run_conversation(
    user_message="Explain quicksort",
    system_message="You are a computer science tutor. Use simple analogies.",
)
```

---

## 配置工具

使用 `enabled_toolsets` 或 `disabled_toolsets` 控制智能体可以访问哪些工具集：

```python
# 仅启用 Web 工具（浏览、搜索）
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    enabled_toolsets=["web"],
    quiet_mode=True,
)

# 启用除终端访问外的所有功能
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    disabled_toolsets=["terminal"],
    quiet_mode=True,
)
```

:::tip
当您想要一个最小、锁定的智能体时（例如，仅用于研究机器人的 Web 搜索），使用 `enabled_toolsets`。当您想要大多数功能但需要限制特定功能时（例如，在共享环境中禁止终端访问），使用 `disabled_toolsets`。
:::

---

## 多轮对话

通过将消息历史传递回来，在多轮对话中保持对话状态：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
)

# 第一轮
result1 = agent.run_conversation("My name is Alice")
history = result1["messages"]

# 第二轮 — 智能体记住上下文
result2 = agent.run_conversation(
    "What's my name?",
    conversation_history=history,
)
print(result2["final_response"])  # "Your name is Alice."
```

`conversation_history` 参数接受来自先前结果的 `messages` 列表。智能体在内部复制它，因此您的原始列表永远不会被修改。

---

## 保存轨迹

启用轨迹保存以 ShareGPT 格式捕获对话 — 对于生成训练数据或调试很有用：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    save_trajectories=True,
    quiet_mode=True,
)

agent.chat("Write a Python function to sort a list")
# 保存到 trajectory_samples.jsonl 中，格式为 ShareGPT
```

每个对话都作为单个 JSONL 行追加，使得从自动化运行中收集数据集变得容易。

---

## 自定义系统提示

使用 `ephemeral_system_prompt` 设置自定义系统提示，指导智能体的行为，但**不**保存到轨迹文件（保持训练数据干净）：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a SQL expert. Only answer database questions.",
    quiet_mode=True,
)

response = agent.chat("How do I write a JOIN query?")
print(response)
```

这对于构建专门的智能体非常理想 — 代码审查员、文档编写者、SQL 助手 — 都使用相同的底层工具。

---

## 批处理

对于并行运行多个提示，Hermes 包含 `batch_runner.py`。它管理具有适当资源隔离的并发 `AIAgent` 实例：

```bash
python batch_runner.py --input prompts.jsonl --output results.jsonl
```

每个提示都有自己的 `task_id` 和隔离环境。如果您需要自定义批处理逻辑，可以直接使用 `AIAgent` 构建自己的逻辑：

```python
import concurrent.futures
from run_agent import AIAgent

prompts = [
    "Explain recursion",
    "What is a hash table?",
    "How does garbage collection work?",
]

def process_prompt(prompt):
    # 为每个任务创建一个新的智能体以确保线程安全
    agent = AIAgent(
        model="anthropic/claude-sonnet-4",
        quiet_mode=True,
        skip_memory=True,
    )
    return agent.chat(prompt)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_prompt, prompts))

for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

:::warning
始终为**每个线程或任务**创建一个**新的 `AIAgent` 实例**。智能体维护内部状态（对话历史、工具会话、迭代计数器），这些状态在共享时不是线程安全的。
:::

---

## 集成示例

### FastAPI 端点

```python
from fastapi import FastAPI
from pydantic import BaseModel
from run_agent import AIAgent

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-sonnet-4"

@app.post("/chat")
async def chat(request: ChatRequest):
    agent = AIAgent(
        model=request.model,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    response = agent.chat(request.message)
    return {"response": response}
```

### Discord 机器人

```python
import discord
from run_agent import AIAgent

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!hermes "):
        query = message.content[8:]
        agent = AIAgent(
            model="anthropic/claude-sonnet-4",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            platform="discord",
        )
        response = agent.chat(query)
        await message.channel.send(response[:2000])

client.run("YOUR_DISCORD_TOKEN")
```

### CI/CD 管道步骤

```python
#!/usr/bin/env python3
"""CI step: auto-review a PR diff."""
import subprocess
from run_agent import AIAgent

diff = subprocess.check_output(["git", "diff", "main...HEAD"]).decode()

agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
    skip_context_files=True,
    skip_memory=True,
    disabled_toolsets=["terminal", "browser"],
)

review = agent.chat(
    f"Review this PR diff for bugs, security issues, and style problems:\n\n{diff}"
)
print(review)
```

---

## 关键构造函数参数

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `model` | `str` | `"anthropic/claude-opus-4.6"` | OpenRouter 格式的模型 |
| `quiet_mode` | `bool` | `False` | 抑制 CLI 输出 |
| `enabled_toolsets` | `List[str]` | `None` | 白名单特定工具集 |
| `disabled_toolsets` | `List[str]` | `None` | 黑名单特定工具集 |
| `save_trajectories` | `bool` | `False` | 将对话保存到 JSONL |
| `ephemeral_system_prompt` | `str` | `None` | 自定义系统提示（不保存到轨迹） |
| `max_iterations` | `int` | `90` | 每次对话的最大工具调用迭代次数 |
| `skip_context_files` | `bool` | `False` | 跳过加载 AGENTS.md 文件 |
| `skip_memory` | `bool` | `False` | 禁用持久记忆读写 |
| `api_key` | `str` | `None` | API 密钥（回退到环境变量） |
| `base_url` | `str` | `None` | 自定义 API 端点 URL |
| `platform` | `str` | `None` | 平台提示（`"discord"`、`"telegram"` 等） |

---

## 重要注意事项

:::tip
- 如果您不希望从工作目录加载 `AGENTS.md` 文件到系统提示中，请设置 **`skip_context_files=True`**。
- 设置 **`skip_memory=True`** 以防止智能体读取或写入持久记忆 — 推荐用于无状态 API 端点。
- `platform` 参数（例如，`"discord"`、`"telegram"`）注入平台特定的格式提示，以便智能体适应其输出风格。
:::

:::warning
- **线程安全**：为每个线程或任务创建一个 `AIAgent`。切勿在并发调用之间共享实例。
- **资源清理**：智能体会在对话结束时自动清理资源（终端会话、浏览器实例）。如果您在长期运行的进程中运行，请确保每个对话正常完成。
- **迭代限制**：默认的 `max_iterations=90` 是慷慨的。对于简单的问答用例，考虑降低它（例如，`max_iterations=10`）以防止失控的工具调用循环并控制成本。
:::