# 轨迹格式

Hermes Agent 以 ShareGPT 兼容的 JSONL 格式保存对话轨迹，用作训练数据、调试工件和强化学习数据集。

源文件：`agent/trajectory.py`、`run_agent.py`（搜索 `_save_trajectory`）、`batch_runner.py`

## 文件命名约定

轨迹写入当前工作目录中的文件：

| 文件 | 何时 |
|------|------|
| `trajectory_samples.jsonl` | 成功完成的对话 (`completed=True`) |
| `failed_trajectories.jsonl` | 失败或被中断的对话 (`completed=False`) |

批处理运行器 (`batch_runner.py`) 为每个批处理写入自定义输出文件（例如 `batch_001_output.jsonl`），带有额外的元数据字段。

你可以通过 `save_trajectory()` 中的 `filename` 参数覆盖文件名。

## JSONL 条目格式

文件中的每一行都是一个自包含的 JSON 对象。有两种变体：

### CLI/交互式格式（来自 `_save_trajectory`）

```json
{
  "conversations": [ ... ],
  "timestamp": "2026-03-30T14:22:31.456789",
  "model": "anthropic/claude-sonnet-4.6",
  "completed": true
}
```

### 批处理运行器格式（来自 `batch_runner.py`）

```json
{
  "prompt_index": 42,
  "conversations": [ ... ],
  "metadata": { "prompt_source": "gsm8k", "difficulty": "hard" },
  "completed": true,
  "partial": false,
  "api_calls": 7,
  "toolsets_used": ["code_tools", "file_tools"],
  "tool_stats": {
    "terminal": {"count": 3, "success": 3, "failure": 0},
    "read_file": {"count": 2, "success": 2, "failure": 0},
    "write_file": {"count": 0, "success": 0, "failure": 0}
  },
  "tool_error_counts": {
    "terminal": 0,
    "read_file": 0,
    "write_file": 0
  }
}
```

`tool_stats` 和 `tool_error_counts` 字典被标准化为包含**所有**可能的工具（来自 `model_tools.TOOL_TO_TOOLSET_MAP`），默认值为零，确保 HuggingFace 数据集加载时条目的架构一致。

## 对话数组（ShareGPT 格式）

`conversations` 数组使用 ShareGPT 角色约定：

| API 角色 | ShareGPT `from` |
|----------|-----------------|
| system | `"system"` |
| user | `"human"` |
| assistant | `"gpt"` |
| tool | `"tool"` |

### 完整示例

```json
{
  "conversations": [
    {
      "from": "system",
      "value": "You are a function calling AI model. You are provided with function signatures within <tools> </tools> XML tags. You may call one or more functions to assist with the user query. If available tools are not relevant in assisting with user query, just respond in natural conversational language. Don't make assumptions about what values to plug into functions. After calling & executing the functions, you will be provided with function results within <tool_response> </tool_response> XML tags. Here are the available tools:\n<tools>\n[{\"name\": \"terminal\", \"description\": \"Execute shell commands\", \"parameters\": {\"type\": \"object\", \"properties\": {\"command\": {\"type\": \"string\"}}}, \"required\": null}]\n</tools>\nFor each function call return a JSON object, with the following pydantic model json schema for each:\n{'title': 'FunctionCall', 'type': 'object', 'properties': {'name': {'title': 'Name', 'type': 'string'}, 'arguments': {'title': 'Arguments', 'type': 'object'}}, 'required': ['name', 'arguments']}\nEach function call should be enclosed within <tool_call> </tool_call> XML tags.\nExample:\n<tool_call>\n{'name': <function-name>,'arguments': <args-dict>}\n</tool_call>"
    },
    {
      "from": "human",
      "value": "What Python version is installed?"
    },
    {
      "from": "gpt",
      "value": "<think>\nThe user wants to know the Python version. I should run python3 --version.\n</think>\n<tool_call>\n{\"name\": \"terminal\", \"arguments\": {\"command\": \"python3 --version\"}}\n</tool_call>"
    },
    {
      "from": "tool",
      "value": "<tool_response>\n{\"tool_call_id\": \"call_abc123\", \"name\": \"terminal\", \"content\": \"Python 3.11.6\"}\n</tool_response>"
    },
    {
      "from": "gpt",
      "value": "<think>\nGot the version. I can now answer the user.\n</think>\nPython 3.11.6 is installed on this system."
    }
  ],
  "timestamp": "2026-03-30T14:22:31.456789",
  "model": "anthropic/claude-sonnet-4.6",
  "completed": true
}
```

## 标准化规则

### 推理内容标记

轨迹转换器将所有推理标准化为 `<think>` 标签，无论模型最初如何产生：

1. **原生思考令牌**（来自 Anthropic、OpenAI o-series 等提供商的 `msg["reasoning"]` 字段）：包装为 `<think>\n{reasoning}\n</think>\n` 并在内容前添加。

2. **REASONING_SCRATCHPAD XML**（当原生思考被禁用且模型通过系统提示指示的 XML 进行推理时）：`<REASONING_SCRATCHPAD>` 标签通过 `convert_scratchpad_to_think()` 转换为 `<think>`。

3. **空思考块**：每个 `gpt` 轮次保证有一个 `<think>` 块。如果没有产生推理，会插入一个空块：`<think>\n</think>\n` — 这确保训练数据的格式一致。

### 工具调用标准化

API 格式的工具调用（带有 `tool_call_id`、函数名、参数作为 JSON 字符串）被转换为 XML 包装的 JSON：

```
<tool_call>
{"name": "terminal", "arguments": {"command": "ls -la"}}
</tool_call>
```

- 参数从 JSON 字符串解析回对象（不双重编码）
- 如果 JSON 解析失败（不应该发生 — 对话期间已验证），使用空 `{}` 并记录警告
- 一个助手轮次中的多个工具调用在单个 `gpt` 消息中产生多个 `<tool_call>` 块

### 工具响应标准化

跟随助手消息的所有工具结果被分组到一个带有 XML 包装的 JSON 响应的 `tool` 轮次中：

```
<tool_response>
{"tool_call_id": "call_abc123", "name": "terminal", "content": "output here"}
</tool_response>
```

- 如果工具内容看起来像 JSON（以 `{` 或 `[` 开头），它会被解析，以便 content 字段包含 JSON 对象/数组而不是字符串
- 多个工具结果在一条消息中用换行符连接
- 工具名称通过位置与父助手的 `tool_calls` 数组匹配

### 系统消息

系统消息在保存时生成（不是从对话中获取）。它遵循 Hermes 函数调用提示模板，包含：

- 解释函数调用协议的前言
- 包含 JSON 工具定义的 `<tools>` XML 块
- `FunctionCall` 对象的模式参考
- `<tool_call>` 示例

工具定义包括 `name`、`description`、`parameters` 和 `required`（设置为 `null` 以匹配规范格式）。

## 加载轨迹

轨迹是标准 JSONL — 使用任何 JSON 行读取器加载：

```python
import json

def load_trajectories(path: str):
    """从 JSONL 文件加载轨迹条目。"""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

# 仅过滤成功完成的
successful = [e for e in load_trajectories("trajectory_samples.jsonl")
              if e.get("completed")]

# 仅提取对话用于训练
training_data = [e["conversations"] for e in successful]
```

### 加载到 HuggingFace 数据集

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="trajectory_samples.jsonl")
```

标准化的 `tool_stats` 架构确保所有条目具有相同的列，防止数据集加载期间的 Arrow 架构不匹配错误。

## 控制轨迹保存

在 CLI 中，轨迹保存由以下控制：

```yaml
# config.yaml
agent:
  save_trajectories: true  # 默认: false
```

或通过 `--save-trajectories` 标志。当代理以 `save_trajectories=True` 初始化时，`_save_trajectory()` 方法在每次对话轮次结束时被调用。

批处理运行器始终保存轨迹（这是其主要目的）。

所有轮次都没有推理的样本会被批处理运行器自动丢弃，以避免用非推理示例污染训练数据。