---
sidebar_position: 4
title: "提供商运行时解析"
description: "Hermes 如何在运行时解析提供商、凭证、API 模式和辅助模型"
---

# 提供商运行时解析

Hermes 有一个共享的提供商运行时解析器，用于：

- CLI
- 网关
- 计划任务
- ACP
- 辅助模型调用

主要实现：

- `hermes_cli/runtime_provider.py` — 凭证解析，`_resolve_custom_runtime()`
- `hermes_cli/auth.py` — 提供商注册表，`resolve_provider()`
- `hermes_cli/model_switch.py` — 共享的 `/model` 切换管道（CLI + 网关）
- `agent/auxiliary_client.py` — 辅助模型路由

如果您尝试添加新的一级推理提供商，请同时阅读[添加提供商](./adding-providers.md)。

## 解析优先级

从高层次看，提供商解析使用：

1. 显式 CLI/运行时请求
2. `config.yaml` 模型/提供商配置
3. 环境变量
4. 提供商特定的默认值或自动解析

这个顺序很重要，因为 Hermes 将保存的模型/提供商选择视为正常运行的真实来源。这可以防止过时的 shell 导出静默覆盖用户上次在 `hermes model` 中选择的端点。

## 提供商

当前提供商系列包括：

- AI Gateway (Vercel)
- OpenRouter
- Nous Portal
- OpenAI Codex
- Copilot / Copilot ACP
- Anthropic (原生)
- Google / Gemini
- 阿里巴巴 / DashScope
- DeepSeek
- Z.AI
- Kimi / Moonshot
- MiniMax
- MiniMax China
- Kilo Code
- Hugging Face
- OpenCode Zen / OpenCode Go
- 自定义 (`provider: custom`) — 任何 OpenAI 兼容端点的一级提供商
- 命名自定义提供商（`config.yaml` 中的 `custom_providers` 列表）

## 运行时解析的输出

运行时解析器返回的数据包括：

- `provider`
- `api_mode`
- `base_url`
- `api_key`
- `source`
- 提供商特定的元数据，如过期/刷新信息

## 为什么这很重要

这个解析器是 Hermes 能够在以下之间共享认证/运行时逻辑的主要原因：

- `hermes chat`
- 网关消息处理
- 在新会话中运行的计划任务
- ACP 编辑器会话
- 辅助模型任务

## AI Gateway

在 `~/.hermes/.env` 中设置 `AI_GATEWAY_API_KEY` 并使用 `--provider ai-gateway` 运行。Hermes 从网关的 `/models` 端点获取可用模型，过滤到支持工具使用的语言模型。

## OpenRouter、AI Gateway 和自定义 OpenAI 兼容的基本 URL

当存在多个提供商密钥时（例如 `OPENROUTER_API_KEY`、`AI_GATEWAY_API_KEY` 和 `OPENAI_API_KEY`），Hermes 包含逻辑以避免将错误的 API 密钥泄露给自定义端点。

每个提供商的 API 密钥都限定在自己的基本 URL 内：

- `OPENROUTER_API_KEY` 仅发送到 `openrouter.ai` 端点
- `AI_GATEWAY_API_KEY` 仅发送到 `ai-gateway.vercel.sh` 端点
- `OPENAI_API_KEY` 用于自定义端点并作为回退

Hermes 还区分：

- 用户选择的真实自定义端点
- 未配置自定义端点时使用的 OpenRouter 回退路径

这种区分对于以下情况特别重要：

- 本地模型服务器
- 非 OpenRouter/非 AI Gateway 的 OpenAI 兼容 API
- 无需重新运行设置即可切换提供商
- 即使当前 shell 中未导出 `OPENAI_BASE_URL`，通过 `hermes model` 保存的自定义端点也应保持工作

## 原生 Anthropic 路径

Anthropic 不再只是"通过 OpenRouter"。

当提供商解析选择 `anthropic` 时，Hermes 使用：

- `api_mode = anthropic_messages`
- 原生 Anthropic Messages API
- `agent/anthropic_adapter.py` 进行转换

原生 Anthropic 的凭证解析现在在两者都存在时，优先使用可刷新的 Claude Code 凭证而不是复制的环境令牌。实际上，这意味着：

- 当 Claude Code 凭证文件包含可刷新的认证时，它们被视为首选来源
- 手动 `ANTHROPIC_TOKEN` / `CLAUDE_CODE_OAUTH_TOKEN` 值仍然作为显式覆盖有效
- Hermes 在原生 Messages API 调用之前预检查 Anthropic 凭证刷新
- Hermes 仍然在重建 Anthropic 客户端后对 401 错误重试一次，作为回退路径

## OpenAI Codex 路径

Codex 使用单独的 Responses API 路径：

- `api_mode = codex_responses`
- 专用凭证解析和认证存储支持

## 辅助模型路由

辅助任务如：

- 视觉
- Web 提取摘要
- 上下文压缩摘要
- 会话搜索摘要
- 技能中心操作
- MCP 辅助操作
- 记忆刷新

可以使用自己的提供商/模型路由，而不是主对话模型。

当辅助任务配置为提供商 `main` 时，Hermes 通过与普通聊天相同的共享运行时路径解析它。实际上，这意味着：

- 环境驱动的自定义端点仍然有效
- 通过 `hermes model` / `config.yaml` 保存的自定义端点也有效
- 辅助路由可以区分真实保存的自定义端点和 OpenRouter 回退

## 回退模型

Hermes 支持配置的回退模型/提供商对，允许在主模型遇到错误时进行运行时故障转移。

### 内部工作原理

1. **存储**：`AIAgent.__init__` 存储 `fallback_model` 字典并设置 `_fallback_activated = False`。

2. **触发点**：`_try_activate_fallback()` 在 `run_agent.py` 主重试循环中的三个位置被调用：
   - 在无效 API 响应的最大重试后（无选择、缺少内容）
   - 在不可重试的客户端错误（HTTP 401、403、404）
   - 在瞬态错误的最大重试后（HTTP 429、500、502、503）

3. **激活流程** (`_try_activate_fallback`)：
   - 如果已经激活或未配置，立即返回 `False`
   - 调用 `auxiliary_client.py` 中的 `resolve_provider_client()` 构建具有正确认证的新客户端
   - 确定 `api_mode`：openai-codex 为 `codex_responses`，anthropic 为 `anthropic_messages`，其他为 `chat_completions`
   - 原地交换：`self.model`、`self.provider`、`self.base_url`、`self.api_mode`、`self.client`、`self._client_kwargs`
   - 对于 anthropic 回退：构建原生 Anthropic 客户端而不是 OpenAI 兼容客户端
   - 重新评估提示缓存（在 OpenRouter 上为 Claude 模型启用）
   - 设置 `_fallback_activated = True` — 防止再次触发
   - 将重试计数重置为 0 并继续循环

4. **配置流程**：
   - CLI：`cli.py` 读取 `CLI_CONFIG["fallback_model"]` → 传递给 `AIAgent(fallback_model=...)`
   - 网关：`gateway/run.py._load_fallback_model()` 读取 `config.yaml` → 传递给 `AIAgent`
   - 验证：`provider` 和 `model` 键都必须非空，否则回退被禁用

### 不支持回退的功能

- **子代理委托** (`tools/delegate_tool.py`)：子代理继承父代理的提供商但不继承回退配置
- **计划任务** (`cron/`)：使用固定提供商运行，无回退机制
- **辅助任务**：使用自己独立的提供商自动检测链（见上面的辅助模型路由）

### 测试覆盖

请参阅 `tests/test_fallback_model.py` 了解涵盖所有支持的提供商、一次性语义和边缘情况的综合测试。

## 相关文档

- [代理循环内部原理](./agent-loop.md)
- [ACP 内部原理](./acp-internals.md)
- [上下文压缩和提示缓存](./context-compression-and-caching.md)
