---
sidebar_position: 3
title: "代理循环内部原理"
description: "AIAgent 执行、API 模式、工具、回调和回退行为的详细说明"
---

# 代理循环内部原理

核心编排引擎是 `run_agent.py` 中的 `AIAgent` 类 — 约 10,700 行代码，处理从提示组装到工具调度到提供商故障转移的所有内容。

## 核心职责

`AIAgent` 负责：

- 通过 `prompt_builder.py` 组装有效的系统提示和工具架构
- 选择正确的提供商/API 模式（chat_completions、codex_responses、anthropic_messages）
- 进行可中断的模型调用，支持取消
- 执行工具调用（顺序或通过线程池并发）
- 以 OpenAI 消息格式维护对话历史
- 处理压缩、重试和回退模型切换
- 跟踪父代理和子代理的迭代预算
- 在上下文丢失前刷新持久记忆

## 两个入口点

```python
# 简单接口 — 返回最终响应字符串
response = agent.chat("Fix the bug in main.py")

# 完整接口 — 返回包含消息、元数据、使用统计信息的字典
result = agent.run_conversation(
    user_message="Fix the bug in main.py",
    system_message=None,           # 省略时自动构建
    conversation_history=None,      # 省略时从会话自动加载
    task_id="task_abc123"
)
```

`chat()` 是 `run_conversation()` 的薄包装，从结果字典中提取 `final_response` 字段。

## API 模式

Hermes 支持三种 API 执行模式，根据提供商选择、显式参数和基本 URL 启发式解析：

| API 模式 | 用途 | 客户端类型 |
|----------|----------|-------------|
| `chat_completions` | OpenAI 兼容端点（OpenRouter、自定义、大多数提供商） | `openai.OpenAI` |
| `codex_responses` | OpenAI Codex / Responses API | `openai.OpenAI` 带 Responses 格式 |
| `anthropic_messages` | 原生 Anthropic Messages API | 通过适配器的 `anthropic.Anthropic` |

模式决定了消息如何格式化、工具调用如何结构化、响应如何解析以及缓存/流式传输如何工作。所有三种模式在 API 调用前后都收敛到相同的内部消息格式（OpenAI 风格的 `role`/`content`/`tool_calls` 字典）。

**模式解析顺序：**
1. 显式 `api_mode` 构造函数参数（最高优先级）
2. 提供商特定检测（例如，`anthropic` 提供商 → `anthropic_messages`）
3. 基本 URL 启发式（例如，`api.anthropic.com` → `anthropic_messages`）
4. 默认：`chat_completions`

## 轮次生命周期

代理循环的每次迭代遵循以下顺序：

```text
run_conversation()
  1. 如果未提供，生成 task_id
  2. 将用户消息追加到对话历史
  3. 构建或重用缓存的系统提示（prompt_builder.py）
  4. 检查是否需要预压缩（>50% 上下文）
  5. 从对话历史构建 API 消息
     - chat_completions: 直接使用 OpenAI 格式
     - codex_responses: 转换为 Responses API 输入项
     - anthropic_messages: 通过 anthropic_adapter.py 转换
  6. 注入临时提示层（预算警告、上下文压力）
  7. 如果在 Anthropic 上，应用提示缓存标记
  8. 进行可中断的 API 调用（_api_call_with_interrupt）
  9. 解析响应：
     - 如果是 tool_calls: 执行它们，追加结果，循环回到步骤 5
     - 如果是文本响应: 持久化会话，必要时刷新记忆，返回
```

### 消息格式

所有消息在内部使用 OpenAI 兼容格式：

```python
{"role": "system", "content": "..."}
{"role": "user", "content": "..."}
{"role": "assistant", "content": "...", "tool_calls": [...]}
{"role": "tool", "tool_call_id": "...", "content": "..."}
```

推理内容（来自支持扩展思考的模型）存储在 `assistant_msg["reasoning"]` 中，并可通过 `reasoning_callback` 选择性显示。

### 消息交替规则

代理循环强制执行严格的消息角色交替：

- 系统消息后：`User → Assistant → User → Assistant → ...`
- 工具调用期间：`Assistant (with tool_calls) → Tool → Tool → ... → Assistant`
- **永远不会**连续两个 assistant 消息
- **永远不会**连续两个 user 消息
- **只有** `tool` 角色可以有连续条目（并行工具结果）

提供商验证这些序列，会拒绝格式错误的历史记录。

## 可中断的 API 调用

API 请求被包装在 `_api_call_with_interrupt()` 中，该函数在后台线程中运行实际的 HTTP 调用，同时监控中断事件：

```text
┌────────────────────────────────────────────────────┐
│  主线程                  API 线程           │
│                                                    │
│   等待：                     HTTP POST           │
│    - 响应就绪     ───▶   到提供商         │
│    - 中断事件                               │
│    - 超时                                       │
└────────────────────────────────────────────────────┘
```

当被中断时（用户发送新消息、`/stop` 命令或信号）：
- API 线程被放弃（响应被丢弃）
- 代理可以处理新输入或干净地关闭
- 不会将部分响应注入对话历史

## 工具执行

### 顺序与并发

当模型返回工具调用时：

- **单个工具调用** → 直接在主线程中执行
- **多个工具调用** → 通过 `ThreadPoolExecutor` 并发执行
  - 例外：标记为交互式的工具（例如 `clarify`）强制顺序执行
  - 结果按原始工具调用顺序重新插入，无论完成顺序如何

### 执行流程

```text
for each tool_call in response.tool_calls:
    1. 从 tools/registry.py 解析处理程序
    2. 触发 pre_tool_call 插件钩子
    3. 检查是否为危险命令（tools/approval.py）
       - 如果危险：调用 approval_callback，等待用户
    4. 使用参数 + task_id 执行处理程序
    5. 触发 post_tool_call 插件钩子
    6. 向历史追加 {"role": "tool", "content": result}
```

### 代理级工具

某些工具在到达 `handle_function_call()` 之前被 `run_agent.py` 拦截：

| 工具 | 为什么被拦截 |
|------|--------------------|
| `todo` | 读写代理本地任务状态 |
| `memory` | 写入具有字符限制的持久记忆文件 |
| `session_search` | 通过代理的会话数据库查询会话历史 |
| `delegate_task` | 生成具有隔离上下文的子代理 |

这些工具直接修改代理状态并返回合成工具结果，而不通过注册表。

## 回调接口

`AIAgent` 支持平台特定的回调，在 CLI、网关和 ACP 集成中实现实时进度：

| 回调 | 触发时机 | 使用者 |
|----------|-----------|---------|
| `tool_progress_callback` | 每个工具执行前后 | CLI  spinner、网关进度消息 |
| `thinking_callback` | 模型开始/停止思考时 | CLI "thinking..." 指示器 |
| `reasoning_callback` | 模型返回推理内容时 | CLI 推理显示、网关推理块 |
| `clarify_callback` | 调用 `clarify` 工具时 | CLI 输入提示、网关交互式消息 |
| `step_callback` | 每个完整代理轮次后 | 网关步骤跟踪、ACP 进度 |
| `stream_delta_callback` | 每个流式令牌（启用时） | CLI 流式显示 |
| `tool_gen_callback` | 从流中解析工具调用时 | CLI spinner 中的工具预览 |
| `status_callback` | 状态变化（思考、执行等） | ACP 状态更新 |

## 预算和回退行为

### 迭代预算

代理通过 `IterationBudget` 跟踪迭代：

- 默认：90 次迭代（可通过 `agent.max_turns` 配置）
- 每个代理都有自己的预算。子代理获得独立预算，上限为 `delegation.max_iterations`（默认 50）— 父代理 + 子代理的总迭代次数可以超过父代理的上限
- 达到 100% 时，代理停止并返回已完成工作的摘要

### 回退模型

当主模型失败时（429 速率限制、5xx 服务器错误、401/403 认证错误）：

1. 检查配置中的 `fallback_providers` 列表
2. 按顺序尝试每个回退
3. 成功时，使用新提供商继续对话
4. 对于 401/403，在故障转移前尝试凭证刷新

回退系统也独立覆盖辅助任务 — 视觉、压缩、Web 提取和会话搜索各有自己的回退链，可通过 `auxiliary.*` 配置部分配置。

## 压缩和持久化

### 压缩触发时机

- **预压缩**（API 调用前）：如果对话超过模型上下文窗口的 50%
- **网关自动压缩**：如果对话超过 85%（更激进，在轮次之间运行）

### 压缩期间发生的情况

1. 首先将记忆刷新到磁盘（防止数据丢失）
2. 中间对话轮次被总结为紧凑摘要
3. 最后 N 条消息保持完整（`compression.protect_last_n`，默认：20）
4. 工具调用/结果消息对保持在一起（永不拆分）
5. 生成新的会话谱系 ID（压缩创建"子"会话）

### 会话持久化

每轮之后：
- 消息保存到会话存储（通过 `hermes_state.py` 的 SQLite）
- 记忆更改刷新到 `MEMORY.md` / `USER.md`
- 会话可以稍后通过 `/resume` 或 `hermes chat --resume` 恢复

## 关键源文件

| 文件 | 用途 |
|------|---------|
| `run_agent.py` | AIAgent 类 — 完整的代理循环（~10,700 行） |
| `agent/prompt_builder.py` | 从记忆、技能、上下文文件、个性组装系统提示 |
| `agent/context_engine.py` | ContextEngine ABC — 可插拔上下文管理 |
| `agent/context_compressor.py` | 默认引擎 — 有损摘要算法 |
| `agent/prompt_caching.py` | Anthropic 提示缓存标记和缓存指标 |
| `agent/auxiliary_client.py` | 辅助 LLM 客户端，用于辅助任务（视觉、摘要） |
| `model_tools.py` | 工具架构集合，`handle_function_call()` 调度 |

## 相关文档

- [提供商运行时解析](./provider-runtime.md)
- [提示组装](./prompt-assembly.md)
- [上下文压缩和提示缓存](./context-compression-and-caching.md)
- [工具运行时](./tools-runtime.md)
- [架构概述](./architecture.md)
