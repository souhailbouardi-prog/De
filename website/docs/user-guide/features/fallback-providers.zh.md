---
title: "备用提供者"
description: "配置当主模型不可用时自动故障转移到备份 LLM 提供者"
sidebar_label: "备用提供者"
sidebar_position: 8
---

# 备用提供者

Hermes Agent 有三层弹性机制，可在提供者遇到问题时保持会话运行：

1. **[凭证池](./credential-pools.zh.md)** — 在*同一*提供者的多个 API 密钥之间轮换（优先尝试）
2. **主模型备用** — 当主模型失败时自动切换到*不同*的提供者:模型
3. **辅助任务备用** — 用于视觉、压缩和网页提取等侧任务的独立提供者解析

凭证池处理同提供者轮换（例如，多个 OpenRouter 密钥）。本页面介绍跨提供者备用。两者都是可选的，并且独立工作。

## 主模型备用

当您的主 LLM 提供者遇到错误 — 速率限制、服务器过载、认证失败、连接断开 — Hermes 可以在会话中自动切换到备份提供者:模型对，而不会丢失您的对话。

### 配置

在 `~/.hermes/config.yaml` 中添加 `fallback_model` 部分：

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

`provider` 和 `model` 都是**必需的**。如果任一缺失，备用功能将被禁用。

### 支持的提供者

| 提供者 | 值 | 要求 |
|-------|------|------|
| AI Gateway | `ai-gateway` | `AI_GATEWAY_API_KEY` |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` |
| Nous Portal | `nous` | `hermes auth`（OAuth） |
| OpenAI Codex | `openai-codex` | `hermes model`（ChatGPT OAuth） |
| GitHub Copilot | `copilot` | `COPILOT_GITHUB_TOKEN`、`GH_TOKEN` 或 `GITHUB_TOKEN` |
| GitHub Copilot ACP | `copilot-acp` | 外部进程（编辑器集成） |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` 或 Claude Code 凭证 |
| z.ai / GLM | `zai` | `GLM_API_KEY` |
| Kimi / Moonshot | `kimi-coding` | `KIMI_API_KEY` |
| MiniMax | `minimax` | `MINIMAX_API_KEY` |
| MiniMax (中国) | `minimax-cn` | `MINIMAX_CN_API_KEY` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| NVIDIA NIM | `nvidia` | `NVIDIA_API_KEY`（可选：`NVIDIA_BASE_URL`） |
| Ollama Cloud | `ollama-cloud` | `OLLAMA_API_KEY` |
| Google Gemini (OAuth) | `google-gemini-cli` | `hermes model`（Google OAuth；可选：`HERMES_GEMINI_PROJECT_ID`） |
| xAI (Grok) | `xai`（别名 `grok`） | `XAI_API_KEY`（可选：`XAI_BASE_URL`） |
| OpenCode Zen | `opencode-zen` | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | `opencode-go` | `OPENCODE_GO_API_KEY` |
| Kilo Code | `kilocode` | `KILOCODE_API_KEY` |
| Xiaomi MiMo | `xiaomi` | `XIAOMI_API_KEY` |
| Arcee AI | `arcee` | `ARCEEAI_API_KEY` |
| Alibaba / DashScope | `alibaba` | `DASHSCOPE_API_KEY` |
| Hugging Face | `huggingface` | `HF_TOKEN` |
| 自定义端点 | `custom` | `base_url` + `api_key_env`（见下文） |

### 自定义端点备用

对于自定义兼容 OpenAI 的端点，添加 `base_url` 和可选的 `api_key_env`：

```yaml
fallback_model:
  provider: custom
  model: my-local-model
  base_url: http://localhost:8000/v1
  api_key_env: MY_LOCAL_KEY          # 包含 API 密钥的环境变量名称
```

### 备用触发条件

当主模型因以下原因失败时，备用功能会自动激活：

- **速率限制**（HTTP 429）— 用尽重试尝试后
- **服务器错误**（HTTP 500、502、503）— 用尽重试尝试后
- **认证失败**（HTTP 401、403）— 立即（无需重试）
- **未找到**（HTTP 404）— 立即
- **无效响应** — 当 API 反复返回格式错误或空响应时

触发时，Hermes：

1. 解析备用提供者的凭证
2. 构建新的 API 客户端
3. 就地交换模型、提供者和客户端
4. 重置重试计数器并继续对话

切换是无缝的 — 您的对话历史、工具调用和上下文都被保留。代理从它离开的确切位置继续，只是使用不同的模型。

:::info 一次性
备用功能在每个会话中**最多激活一次**。如果备用提供者也失败，正常的错误处理会接管（重试，然后错误消息）。这可以防止级联故障转移循环。
:::

### 示例

**OpenRouter 作为 Anthropic 原生的备用：**
```yaml
model:
  provider: anthropic
  default: claude-sonnet-4-6

fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

**Nous Portal 作为 OpenRouter 的备用：**
```yaml
model:
  provider: openrouter
  default: anthropic/claude-opus-4

fallback_model:
  provider: nous
  model: nous-hermes-3
```

**本地模型作为云端的备用：**
```yaml
fallback_model:
  provider: custom
  model: llama-3.1-70b
  base_url: http://localhost:8000/v1
  api_key_env: LOCAL_API_KEY
```

**Codex OAuth 作为备用：**
```yaml
fallback_model:
  provider: openai-codex
  model: gpt-5.3-codex
```

### 备用功能适用的上下文

| 上下文 | 支持备用 |
|--------|---------|
| CLI 会话 | ✔ |
| 消息网关（Telegram、Discord 等） | ✔ |
| 子代理委托 | ✘（子代理不继承备用配置） |
| Cron 作业 | ✘（使用固定提供者运行） |
| 辅助任务（视觉、压缩） | ✘（使用自己的提供者链 — 见下文） |

:::tip
`fallback_model` 没有环境变量 — 它仅通过 `config.yaml` 配置。这是有意的：备用配置是一个深思熟虑的选择，不是过时的 shell 导出应该覆盖的东西。
:::

---

## 辅助任务备用

Hermes 使用单独的轻量级模型处理侧任务。每个任务都有自己的提供者解析链，作为内置的备用系统。

### 具有独立提供者解析的任务

| 任务 | 功能 | 配置键 |
|------|------|--------|
| 视觉 | 图像分析、浏览器截图 | `auxiliary.vision` |
| 网页提取 | 网页摘要 | `auxiliary.web_extract` |
| 压缩 | 上下文压缩摘要 | `auxiliary.compression` |
| 会话搜索 | 过去会话摘要 | `auxiliary.session_search` |
| 技能中心 | 技能搜索和发现 | `auxiliary.skills_hub` |
| MCP | MCP 辅助操作 | `auxiliary.mcp` |
| 记忆刷新 | 记忆整合 | `auxiliary.flush_memories` |

### 自动检测链

当任务的提供者设置为 `"auto"`（默认值）时，Hermes 按顺序尝试提供者，直到找到一个有效的：

**对于文本任务（压缩、网页提取等）：**

```text
OpenRouter → Nous Portal → 自定义端点 → Codex OAuth →
API 密钥提供者（z.ai、Kimi、MiniMax、Xiaomi MiMo、Hugging Face、Anthropic）→ 放弃
```

**对于视觉任务：**

```text
主提供者（如果支持视觉）→ OpenRouter → Nous Portal →
Codex OAuth → Anthropic → 自定义端点 → 放弃
```

如果解析的提供者在调用时失败，Hermes 还有一个内部重试：如果提供者不是 OpenRouter 且没有设置明确的 `base_url`，它会尝试 OpenRouter 作为最后的备用选项。

### 配置辅助提供者

每个任务可以在 `config.yaml` 中独立配置：

```yaml
auxiliary:
  vision:
    provider: "auto"              # auto | openrouter | nous | codex | main | anthropic
    model: ""                     # 例如 "openai/gpt-4o"
    base_url: ""                  # 直接端点（优先于提供者）
    api_key: ""                   # base_url 的 API 密钥

  web_extract:
    provider: "auto"
    model: ""

  compression:
    provider: "auto"
    model: ""

  session_search:
    provider: "auto"
    model: ""

  skills_hub:
    provider: "auto"
    model: ""

  mcp:
    provider: "auto"
    model: ""

  flush_memories:
    provider: "auto"
    model: ""
```

上面的每个任务都遵循相同的**提供者 / 模型 / base_url** 模式。上下文压缩在 `auxiliary.compression` 下配置：

```yaml
auxiliary:
  compression:
    provider: main                                    # 与其他辅助任务相同的提供者选项
    model: google/gemini-3-flash-preview
    base_url: null                                    # 自定义 OpenAI 兼容端点
```

备用模型使用：

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
  # base_url: http://localhost:8000/v1               # 可选的自定义端点
```

所有三个 — 辅助、压缩、备用 — 工作方式相同：设置 `provider` 选择谁处理请求，`model` 选择哪个模型，`base_url` 指向自定义端点（覆盖提供者）。

### 辅助任务的提供者选项

这些选项仅适用于 `auxiliary:`、`compression:` 和 `fallback_model:` 配置 — `"main"` **不是** 顶级 `model.provider` 的有效值。对于自定义端点，请在 `model:` 部分使用 `provider: custom`（见 [AI 提供者](/docs/integrations/providers)）。

| 提供者 | 描述 | 要求 |
|------|------|------|
| `"auto"` | 按顺序尝试提供者，直到找到一个有效的（默认） | 至少配置了一个提供者 |
| `"openrouter"` | 强制使用 OpenRouter | `OPENROUTER_API_KEY` |
| `"nous"` | 强制使用 Nous Portal | `hermes auth` |
| `"codex"` | 强制使用 Codex OAuth | `hermes model` → Codex |
| `"main"` | 使用主代理使用的任何提供者（仅辅助任务） | 配置了活动的主提供者 |
| `"anthropic"` | 强制使用 Anthropic 原生 | `ANTHROPIC_API_KEY` 或 Claude Code 凭证 |

### 直接端点覆盖

对于任何辅助任务，设置 `base_url` 会完全绕过提供者解析，直接将请求发送到该端点：

```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` 优先于 `provider`。Hermes 使用配置的 `api_key` 进行认证，如果未设置，则回退到 `OPENAI_API_KEY`。它**不会**为自定义端点重用 `OPENROUTER_API_KEY`。

---

## 上下文压缩备用

上下文压缩使用 `auxiliary.compression` 配置块来控制哪个模型和提供者处理摘要：

```yaml
auxiliary:
  compression:
    provider: "auto"                              # auto | openrouter | nous | main
    model: "google/gemini-3-flash-preview"
```

:::info 遗留迁移
带有 `compression.summary_model` / `compression.summary_provider` / `compression.summary_base_url` 的旧配置会在首次加载时自动迁移到 `auxiliary.compression.*`（配置版本 17）。
:::

如果没有可用的压缩提供者，Hermes 会在不生成摘要的情况下删除中间对话轮次，而不是使会话失败。

---

## 委托提供者覆盖

由 `delegate_task` 生成的子代理**不**使用主备用模型。但是，它们可以被路由到不同的提供者:模型对以优化成本：

```yaml
delegation:
  provider: "openrouter"                      # 覆盖所有子代理的提供者
  model: "google/gemini-3-flash-preview"      # 覆盖模型
  # base_url: "http://localhost:1234/v1"      # 或使用直接端点
  # api_key: "local-key"
```

有关完整配置详细信息，请参阅 [子代理委托](/docs/user-guide/features/delegation)。

---

## Cron 作业提供者

Cron 作业使用执行时配置的任何提供者运行。它们不支持备用模型。要为 cron 作业使用不同的提供者，请在 cron 作业本身上配置 `provider` 和 `model` 覆盖：

```python
cronjob(
    action="create",
    schedule="every 2h",
    prompt="Check server status",
    provider="openrouter",
    model="google/gemini-3-flash-preview"
)
```

有关完整配置详细信息，请参阅 [计划任务 (Cron)](/docs/user-guide/features/cron)。

---

## 总结

| 功能 | 备用机制 | 配置位置 |
|------|---------|---------|
| 主代理模型 | `fallback_model` 在 config.yaml 中 — 错误时一次性故障转移 | `fallback_model:`（顶级） |
| 视觉 | 自动检测链 + 内部 OpenRouter 重试 | `auxiliary.vision` |
| 网页提取 | 自动检测链 + 内部 OpenRouter 重试 | `auxiliary.web_extract` |
| 上下文压缩 | 自动检测链，不可用时降级为无摘要 | `auxiliary.compression` |
| 会话搜索 | 自动检测链 | `auxiliary.session_search` |
| 技能中心 | 自动检测链 | `auxiliary.skills_hub` |
| MCP 辅助 | 自动检测链 | `auxiliary.mcp` |
| 记忆刷新 | 自动检测链 | `auxiliary.flush_memories` |
| 委托 | 仅提供者覆盖（无自动备用） | `delegation.provider` / `delegation.model` |
| Cron 作业 | 仅每个作业的提供者覆盖（无自动备用） | 每个作业的 `provider` / `model` |