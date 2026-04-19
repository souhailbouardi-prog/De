---
title: "AI 提供商"
sidebar_label: "AI 提供商"
sidebar_position: 1
---

# AI 提供商

本页面涵盖了为 Hermes Agent 设置推理提供商的方法 — 从 OpenRouter 和 Anthropic 等云 API，到 Ollama 和 vLLM 等自托管端点，再到高级路由和备用配置。使用 Hermes 至少需要配置一个提供商。

## 推理提供商

您至少需要一种连接 LLM 的方式。使用 `hermes model` 交互式切换提供商和模型，或直接配置：

| 提供商 | 设置方法 |
|--------|----------|
| **Nous Portal** | `hermes model`（OAuth，基于订阅）|
| **OpenAI Codex** | `hermes model`（ChatGPT OAuth，使用 Codex 模型）|
| **GitHub Copilot** | `hermes model`（OAuth 设备代码流程，`COPILOT_GITHUB_TOKEN`、`GH_TOKEN` 或 `gh auth token`）|
| **GitHub Copilot ACP** | `hermes model`（生成本地 `copilot --acp --stdio`）|
| **Anthropic** | `hermes model`（通过 Claude Code 认证、Anthropic API 密钥或手动设置令牌）|
| **OpenRouter** | 在 `~/.hermes/.env` 中设置 `OPENROUTER_API_KEY`|
| **AI Gateway** | 在 `~/.hermes/.env` 中设置 `AI_GATEWAY_API_KEY`（提供商：`ai-gateway`）|
| **z.ai / GLM** | 在 `~/.hermes/.env` 中设置 `GLM_API_KEY`（提供商：`zai`）|
| **Kimi / Moonshot** | 在 `~/.hermes/.env` 中设置 `KIMI_API_KEY`（提供商：`kimi-coding`）|
| **Kimi / Moonshot (中国)** | 在 `~/.hermes/.env` 中设置 `KIMI_CN_API_KEY`（提供商：`kimi-coding-cn`；别名：`kimi-cn`、`moonshot-cn`）|
| **Arcee AI** | 在 `~/.hermes/.env` 中设置 `ARCEEAI_API_KEY`（提供商：`arcee`；别名：`arcee-ai`、`arceeai`）|
| **MiniMax** | 在 `~/.hermes/.env` 中设置 `MINIMAX_API_KEY`（提供商：`minimax`）|
| **MiniMax 中国** | 在 `~/.hermes/.env` 中设置 `MINIMAX_CN_API_KEY`（提供商：`minimax-cn`）|
| **阿里云** | 在 `~/.hermes/.env` 中设置 `DASHSCOPE_API_KEY`（提供商：`alibaba`，别名：`dashscope`、`qwen`）|
| **Kilo Code** | 在 `~/.hermes/.env` 中设置 `KILOCODE_API_KEY`（提供商：`kilocode`）|
| **小米 MiMo** | 在 `~/.hermes/.env` 中设置 `XIAOMI_API_KEY`（提供商：`xiaomi`，别名：`mimo`、`xiaomi-mimo`）|
| **OpenCode Zen** | 在 `~/.hermes/.env` 中设置 `OPENCODE_ZEN_API_KEY`（提供商：`opencode-zen`）|
| **OpenCode Go** | 在 `~/.hermes/.env` 中设置 `OPENCODE_GO_API_KEY`（提供商：`opencode-go`）|
| **DeepSeek** | 在 `~/.hermes/.env` 中设置 `DEEPSEEK_API_KEY`（提供商：`deepseek`）|
| **Hugging Face** | 在 `~/.hermes/.env` 中设置 `HF_TOKEN`（提供商：`huggingface`，别名：`hf`）|
| **Google / Gemini** | 在 `~/.hermes/.env` 中设置 `GOOGLE_API_KEY`（或 `GEMINI_API_KEY`）（提供商：`gemini`）|
| **Google Gemini (OAuth)** | `hermes model` → "Google Gemini (OAuth)"（提供商：`google-gemini-cli`，支持免费套餐，浏览器 PKCE 登录）|
| **自定义端点** | `hermes model` → 选择 "Custom endpoint"（保存在 `config.yaml` 中）|

:::tip 模型键别名
在 `model:` 配置部分，您可以使用 `default:` 或 `model:` 作为模型 ID 的键名。`model: { default: my-model }` 和 `model: { model: my-model }` 的工作方式完全相同。
:::

### 通过 OAuth 的 Google Gemini (`google-gemini-cli`)

`google-gemini-cli` 提供商使用 Google 的 Cloud Code Assist 后端 — 与 Google 自己的 `gemini-cli` 工具使用的相同 API。这支持**免费套餐**（个人账户的慷慨每日配额）和**付费套餐**（通过 GCP 项目的标准版/企业版）。

**快速开始：**

```bash
hermes model
# → 选择 "Google Gemini (OAuth)"
# → 看到政策警告，确认
# → 浏览器打开到 accounts.google.com，登录
# → 完成 — Hermes 在首次请求时自动配置您的免费套餐
```

Hermes 默认内置了 Google 的**公开** `gemini-cli` 桌面 OAuth 客户端 — 与 Google 在其开源 `gemini-cli` 中包含的相同凭据。桌面 OAuth 客户端不是机密的（PKCE 提供安全性）。您不需要安装 `gemini-cli` 或注册自己的 GCP OAuth 客户端。

**认证工作原理：**
- 针对 `accounts.google.com` 的 PKCE 授权码流程
- 浏览器回调到 `http://127.0.0.1:8085/oauth2callback`（如果繁忙则使用临时端口回退）
- 令牌存储在 `~/.hermes/auth/google_oauth.json`（chmod 0600，原子写入，跨进程 `fcntl` 锁）
- 在过期前 60 秒自动刷新
- 无头环境（SSH，`HERMES_HEADLESS=1`）→ 粘贴模式回退
- 飞行中刷新去重 — 两个并发请求不会重复刷新
- `invalid_grant`（撤销的刷新）→ 凭据文件被擦除，提示用户重新登录

**推理工作原理：**
- 流量前往 `https://cloudcode-pa.googleapis.com/v1internal:generateContent`（或 `:streamGenerateContent?alt=sse` 用于流式传输），而不是付费的 `v1beta/openai` 端点
- 请求体包装为 `{project, model, user_prompt_id, request}`
- 形状为 OpenAI 的 `messages[]`、`tools[]`、`tool_choice` 被转换为 Gemini 的原生 `contents[]`、`tools[].functionDeclarations`、`toolConfig` 形状
- 响应被转换回 OpenAI 形状，以便 Hermes 的其余部分保持不变

**套餐和项目 ID：**

| 您的情况 | 操作 |
|---|---|
| 个人 Google 账户，想要免费套餐 | 无需操作 — 登录，开始聊天 |
| 工作区/标准版/企业版账户 | 将 `HERMES_GEMINI_PROJECT_ID` 或 `GOOGLE_CLOUD_PROJECT` 设置为您的 GCP 项目 ID |
| VPC-SC 保护的组织 | Hermes 检测到 `SECURITY_POLICY_VIOLATED` 并自动强制使用 `standard-tier` |

免费套餐在首次使用时自动配置 Google 管理的项目。无需 GCP 设置。

**配额监控：**

```
/gquota
```

显示每个模型的剩余 Code Assist 配额，带有进度条：

```
Gemini Code Assist quota  (project: 123-abc)

  gemini-2.5-pro                      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░   85%
  gemini-2.5-flash [input]            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░   92%
```

:::warning 政策风险
Google 认为将 Gemini CLI OAuth 客户端与第三方软件一起使用是政策违规。一些用户报告了账户限制。为了最低风险体验，请通过 `gemini` 提供商使用您自己的 API 密钥。Hermes 在 OAuth 开始前显示预先警告并要求明确确认。
:::

**自定义 OAuth 客户端（可选）：**

如果您更愿意注册自己的 Google OAuth 客户端 — 例如，将配额和同意范围限定在您自己的 GCP 项目中 — 设置：

```bash
HERMES_GEMINI_CLIENT_ID=your-client.apps.googleusercontent.com
HERMES_GEMINI_CLIENT_SECRET=...   # 对于桌面客户端可选
```

在 [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials) 注册一个**桌面应用** OAuth 客户端，并启用生成式语言 API。

:::info Codex 说明
OpenAI Codex 提供商通过设备代码进行身份验证（打开 URL，输入代码）。Hermes 将生成的凭据存储在 `~/.hermes/auth.json` 中自己的身份验证存储中，并在存在时可以从 `~/.codex/auth.json` 导入现有的 Codex CLI 凭据。无需安装 Codex CLI。
:::

:::warning
即使使用 Nous Portal、Codex 或自定义端点，某些工具（视觉、网页摘要、MoA）也使用单独的"辅助"模型 — 默认通过 OpenRouter 使用 Gemini Flash。`OPENROUTER_API_KEY` 会自动启用这些工具。您还可以配置这些工具使用哪个模型和提供商 — 请参阅 [辅助模型](/docs/user-guide/configuration#auxiliary-models)。
:::

:::tip Nous 工具网关
付费 Nous Portal 订阅者还可以访问 **[工具网关](/docs/user-guide/features/tool-gateway)** — 通过您的订阅路由的网络搜索、图像生成、TTS 和浏览器自动化。无需额外的 API 密钥。它在 `hermes model` 设置期间自动提供，或稍后使用 `hermes tools` 启用。
:::

### 两个模型管理命令

Hermes 有**两个**模型命令，用于不同的目的：

| 命令 | 运行位置 | 功能 |
|------|----------|------|
| **`hermes model`** | 您的终端（任何会话之外） | 完整设置向导 — 添加提供商、运行 OAuth、输入 API 密钥、配置端点 |
| **`/model`** | 在 Hermes 聊天会话中 | 在**已配置**的提供商和模型之间快速切换 |

如果您尝试切换到尚未设置的提供商（例如，您只配置了 OpenRouter 并想使用 Anthropic），您需要 `hermes model`，而不是 `/model`。先退出会话（`Ctrl+C` 或 `/quit`），运行 `hermes model`，完成提供商设置，然后开始新会话。

### Anthropic（原生）

通过 Anthropic API 直接使用 Claude 模型 — 无需 OpenRouter 代理。支持三种认证方法：

```bash
# 使用 API 密钥（按令牌付费）
export ANTHROPIC_API_KEY=***
hermes chat --provider anthropic --model claude-sonnet-4-6

# 首选：通过 `hermes model` 进行身份验证
# 当可用时，Hermes 将直接使用 Claude Code 的凭据存储
hermes model

# 手动覆盖设置令牌（回退/遗留）
export ANTHROPIC_TOKEN=***  # setup-token 或手动 OAuth 令牌
hermes chat --provider anthropic

# 自动检测 Claude Code 凭据（如果您已经使用 Claude Code）
hermes chat --provider anthropic  # 自动读取 Claude Code 凭据文件
```

当您通过 `hermes model` 选择 Anthropic OAuth 时，Hermes 更喜欢 Claude Code 自己的凭据存储，而不是将令牌复制到 `~/.hermes/.env` 中。这使可刷新的 Claude 凭据保持可刷新。

或者永久设置：
```yaml
model:
  provider: "anthropic"
  default: "claude-sonnet-4-6"
```

:::tip 别名
`--provider claude` 和 `--provider claude-code` 也可以作为 `--provider anthropic` 的简写。
:::

### GitHub Copilot

Hermes 支持 GitHub Copilot 作为一流提供商，具有两种模式：

**`copilot` — 直接 Copilot API**（推荐）。使用您的 GitHub Copilot 订阅通过 Copilot API 访问 GPT-5.x、Claude、Gemini 和其他模型。

```bash
hermes chat --provider copilot --model gpt-5.4
```

**认证选项**（按此顺序检查）：

1. `COPILOT_GITHUB_TOKEN` 环境变量
2. `GH_TOKEN` 环境变量
3. `GITHUB_TOKEN` 环境变量
4. `gh auth token` CLI 回退

如果未找到令牌，`hermes model` 提供**OAuth 设备代码登录** — 与 Copilot CLI 和 opencode 使用的相同流程。

:::warning 令牌类型
Copilot API **不**支持经典个人访问令牌 (`ghp_*`)。支持的令牌类型：

| 类型 | 前缀 | 获取方式 |
|------|--------|----------|
| OAuth 令牌 | `gho_` | `hermes model` → GitHub Copilot → Login with GitHub |
| 细粒度 PAT | `github_pat_` | GitHub 设置 → 开发者设置 → 细粒度令牌（需要 **Copilot Requests** 权限）|
| GitHub App 令牌 | `ghu_` | 通过 GitHub App 安装 |

如果您的 `gh auth token` 返回 `ghp_*` 令牌，请使用 `hermes model` 通过 OAuth 进行身份验证。
:::

**API 路由**：GPT-5+ 模型（除了 `gpt-5-mini`）自动使用 Responses API。所有其他模型（GPT-4o、Claude、Gemini 等）使用 Chat Completions。模型从实时 Copilot 目录中自动检测。

**`copilot-acp` — Copilot ACP 代理后端**。将本地 Copilot CLI 作为子进程生成：

```bash
hermes chat --provider copilot-acp --model copilot-acp
# 需要 PATH 中的 GitHub Copilot CLI 和现有的 `copilot login` 会话
```

**永久配置：**
```yaml
model:
  provider: "copilot"
  default: "gpt-5.4"
```

| 环境变量 | 描述 |
|---------|------|
| `COPILOT_GITHUB_TOKEN` | Copilot API 的 GitHub 令牌（最高优先级）|
| `HERMES_COPILOT_ACP_COMMAND` | 覆盖 Copilot CLI 二进制路径（默认：`copilot`）|
| `HERMES_COPILOT_ACP_ARGS` | 覆盖 ACP 参数（默认：`--acp --stdio`）|

### 一流的中国 AI 提供商

这些提供商具有内置支持，带有专用的提供商 ID。设置 API 密钥并使用 `--provider` 选择：

```bash
# z.ai / ZhipuAI GLM
hermes chat --provider zai --model glm-5
# 需要：GLM_API_KEY 在 ~/.hermes/.env 中

# Kimi / Moonshot AI（国际：api.moonshot.ai）
hermes chat --provider kimi-coding --model kimi-for-coding
# 需要：KIMI_API_KEY 在 ~/.hermes/.env 中

# Kimi / Moonshot AI（中国：api.moonshot.cn）
hermes chat --provider kimi-coding-cn --model kimi-k2.5
# 需要：KIMI_CN_API_KEY 在 ~/.hermes/.env 中

# MiniMax（全球端点）
hermes chat --provider minimax --model MiniMax-M2.7
# 需要：MINIMAX_API_KEY 在 ~/.hermes/.env 中

# MiniMax（中国端点）
hermes chat --provider minimax-cn --model MiniMax-M2.7
# 需要：MINIMAX_CN_API_KEY 在 ~/.hermes/.env 中

# 阿里云 / DashScope（Qwen 模型）
hermes chat --provider alibaba --model qwen3.5-plus
# 需要：DASHSCOPE_API_KEY 在 ~/.hermes/.env 中

# 小米 MiMo
hermes chat --provider xiaomi --model mimo-v2-pro
# 需要：XIAOMI_API_KEY 在 ~/.hermes/.env 中

# Arcee AI（Trinity 模型）
hermes chat --provider arcee --model trinity-large-thinking
# 需要：ARCEEAI_API_KEY 在 ~/.hermes/.env 中
```

或在 `config.yaml` 中永久设置提供商：
```yaml
model:
  provider: "zai"       # 或：kimi-coding, kimi-coding-cn, minimax, minimax-cn, alibaba, xiaomi, arcee
  default: "glm-5"
```

基础 URL 可以通过 `GLM_BASE_URL`、`KIMI_BASE_URL`、`MINIMAX_BASE_URL`、`MINIMAX_CN_BASE_URL`、`DASHSCOPE_BASE_URL` 或 `XIAOMI_BASE_URL` 环境变量覆盖。

:::note Z.AI 端点自动检测
使用 Z.AI / GLM 提供商时，Hermes 会自动探测多个端点（全球、中国、编码变体）以找到接受您 API 密钥的端点。您不需要手动设置 `GLM_BASE_URL` — 工作端点会被自动检测并缓存。
:::

### xAI (Grok) — Responses API + 提示缓存

xAI 通过 Responses API (`codex_responses` 传输) 连接，为 Grok 4 模型提供自动推理支持 — 不需要 `reasoning_effort` 参数，服务器默认进行推理。在 `~/.hermes/.env` 中设置 `XAI_API_KEY` 并在 `hermes model` 中选择 xAI，或者在 `/model grok-4-1-fast-reasoning` 中使用 `grok` 作为快捷方式。

当使用 xAI 作为提供商（任何包含 `x.ai` 的基础 URL）时，Hermes 会通过在每个 API 请求中发送 `x-grok-conv-id` 标头自动启用提示缓存。这会在会话中将请求路由到同一服务器，允许 xAI 的基础设施重用缓存的系统提示和对话历史。

无需配置 — 当检测到 xAI 端点并可获得会话 ID 时，缓存会自动激活。这减少了多轮对话的延迟和成本。

xAI 还提供专用的 TTS 端点 (`/v1/tts`)。在 `hermes tools` → Voice & TTS 中选择 **xAI TTS**，或查看 [Voice & TTS](../user-guide/features/tts.md#text-to-speech) 页面了解配置。

### Ollama Cloud — 托管 Ollama 模型，OAuth + API 密钥

[Ollama Cloud](https://ollama.com/cloud) 托管与本地 Ollama 相同的开放权重目录，但不需要 GPU。在 `hermes model` 中选择 **Ollama Cloud**，粘贴您从 [ollama.com/settings/keys](https://ollama.com/settings/keys) 获取的 API 密钥，Hermes 会自动发现可用模型。

```bash
hermes model
# → 选择 "Ollama Cloud"
# → 粘贴您的 OLLAMA_API_KEY
# → 从发现的模型中选择（gpt-oss:120b, glm-4.6:cloud, qwen3-coder:480b-cloud 等）
```

或直接在 `config.yaml` 中：
```yaml
model:
  provider: "ollama-cloud"
  default: "gpt-oss:120b"
```

模型目录从 `ollama.com/v1/models` 动态获取并缓存一小时。`model:tag` 表示法（例如 `qwen3-coder:480b-cloud`）通过规范化保留 — 不要使用破折号。

:::tip Ollama Cloud vs 本地 Ollama
两者都使用相同的 OpenAI 兼容 API。Cloud 是一流提供商（`--provider ollama-cloud`，`OLLAMA_API_KEY`）；本地 Ollama 通过自定义端点流程访问（基础 URL `http://localhost:11434/v1`，无密钥）。对于本地无法运行的大型模型使用云；对于隐私或离线工作使用本地。
:::

### NVIDIA NIM

通过 [build.nvidia.com](https://build.nvidia.com)（免费 API 密钥）或本地 NIM 端点提供 Nemotron 和其他开源模型。

```bash
# 云（build.nvidia.com）
hermes chat --provider nvidia --model nvidia/nemotron-3-super-120b-a12b
# 需要：NVIDIA_API_KEY 在 ~/.hermes/.env 中

# 本地 NIM 端点 — 覆盖基础 URL
NVIDIA_BASE_URL=http://localhost:8000/v1 hermes chat --provider nvidia --model nvidia/nemotron-3-super-120b-a12b
```

或在 `config.yaml` 中永久设置：
```yaml
model:
  provider: "nvidia"
  default: "nvidia/nemotron-3-super-120b-a12b"
```

:::tip 本地 NIM
对于本地部署（DGX Spark，本地 GPU），设置 `NVIDIA_BASE_URL=http://localhost:8000/v1`。NIM 公开与 build.nvidia.com 相同的 OpenAI 兼容聊天完成 API，因此在云和本地之间切换只需一行环境变量更改。
:::

### Hugging Face 推理提供商

[Hugging Face 推理提供商](https://huggingface.co/docs/inference-providers) 通过统一的 OpenAI 兼容端点 (`router.huggingface.co/v1`) 路由到 20+ 个开放模型。请求自动路由到最快可用的后端（Groq、Together、SambaNova 等），并具有自动故障转移。

```bash
# 使用任何可用模型
hermes chat --provider huggingface --model Qwen/Qwen3-235B-A22B-Thinking-2507
# 需要：HF_TOKEN 在 ~/.hermes/.env 中

# 简短别名
hermes chat --provider hf --model deepseek-ai/DeepSeek-V3.2
```

或在 `config.yaml` 中永久设置：
```yaml
model:
  provider: "huggingface"
  default: "Qwen/Qwen3-235B-A22B-Thinking-2507"
```

在 [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) 获取您的令牌 — 确保启用 "Make calls to Inference Providers" 权限。包含免费套餐（每月 $0.10 信用额度，无提供商费率加价）。

您可以将路由后缀附加到模型名称：`:fastest`（默认）、`:cheapest` 或 `:provider_name` 以强制使用特定后端。

基础 URL 可以通过 `HF_BASE_URL` 覆盖。

## 自定义和自托管 LLM 提供商

Hermes Agent 与**任何兼容 OpenAI 的 API 端点**一起工作。如果服务器实现 `/v1/chat/completions`，您可以将 Hermes 指向它。这意味着您可以使用本地模型、GPU 推理服务器、多提供商路由器或任何第三方 API。

### 一般设置

配置自定义端点的三种方法：

**交互式设置（推荐）：**
```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入：API 基础 URL、API 密钥、模型名称
```

**手动配置 (`config.yaml`)：**
```yaml
# 在 ~/.hermes/config.yaml
model:
  default: your-model-name
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: your-key-or-leave-empty-for-local
```

:::warning 遗留环境变量
`.env` 中的 `OPENAI_BASE_URL` 和 `LLM_MODEL` 已**移除**。Hermes 的任何部分都不会读取它们 — `config.yaml` 是模型和端点配置的唯一真实来源。如果您的 `.env` 中有过时的条目，它们会在下次 `hermes setup` 或配置迁移时自动清除。使用 `hermes model` 或直接编辑 `config.yaml`。
:::

两种方法都会持久化到 `config.yaml`，这是模型、提供商和基础 URL 的真实来源。

### 使用 `/model` 切换模型

:::warning hermes model vs /model
**`hermes model`**（从您的终端运行，在任何聊天会话之外）是**完整的提供商设置向导**。使用它来添加新提供商、运行 OAuth 流程、输入 API 密钥和配置自定义端点。

**`/model`**（在活动的 Hermes 聊天会话中键入）只能**在您已设置的提供商和模型之间切换**。它不能添加新提供商、运行 OAuth 或提示输入 API 密钥。如果您只配置了一个提供商（例如 OpenRouter），`/model` 将只显示该提供商的模型。

**要添加新提供商：** 退出会话（`Ctrl+C` 或 `/quit`），运行 `hermes model`，设置新提供商，然后开始新会话。
:::

一旦您配置了至少一个自定义端点，您可以在会话中切换模型：

```
/model custom:qwen-2.5          # 切换到自定义端点上的模型
/model custom                    # 从端点自动检测模型
/model openrouter:claude-sonnet-4 # 切换回云提供商
```

如果您配置了**命名的自定义提供商**（见下文），使用三重语法：

```
/model custom:local:qwen-2.5    # 使用 "local" 自定义提供商和模型 qwen-2.5
/model custom:work:llama3       # 使用 "work" 自定义提供商和 llama3
```

切换提供商时，Hermes 会将基础 URL 和提供商持久化到配置中，以便更改在重启后仍然有效。当从自定义端点切换到内置提供商时，过时的基础 URL 会自动清除。

:::tip
`/model custom`（裸命令，无模型名称）查询您端点的 `/models` API，如果只加载了一个模型，则自动选择该模型。对于运行单个模型的本地服务器很有用。
:::

以下所有内容都遵循相同的模式 — 只需更改 URL、密钥和模型名称。

---

### Ollama — 本地模型，零配置

[Ollama](https://ollama.com/) 使用一个命令在本地运行开放权重模型。最适合：快速本地实验、隐私敏感工作、离线使用。通过 OpenAI 兼容 API 支持工具调用。

```bash
# 安装并运行模型
ollama pull qwen2.5-coder:32b
ollama serve   # 在端口 11434 上启动
```

然后配置 Hermes：

```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入 URL: http://localhost:11434/v1
# 跳过 API 密钥（Ollama 不需要）
# 输入模型名称（例如 qwen2.5-coder:32b）
```

或直接配置 `config.yaml`：

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 32768   # 见下面的警告
```

:::caution Ollama 默认使用非常低的上下文长度
Ollama 默认**不**使用模型的完整上下文窗口。根据您的 VRAM，默认值为：

| 可用 VRAM | 默认上下文 |
|-----------|------------|
| 小于 24 GB | **4,096 令牌** |
| 24–48 GB | 32,768 令牌 |
| 48+ GB | 256,000 令牌 |

对于使用工具的代理，**您至少需要 16k–32k 上下文**。在 4k 时，系统提示 + 工具模式本身就可以填满窗口，没有对话空间。

**如何增加它**（选择一种）：

```bash
# 选项 1：通过环境变量设置服务器范围（推荐）
OLLAMA_CONTEXT_LENGTH=32768 ollama serve

# 选项 2：对于 systemd 管理的 Ollama
sudo systemctl edit ollama.service
# 添加：Environment="OLLAMA_CONTEXT_LENGTH=32768"
# 然后：sudo systemctl daemon-reload && sudo systemctl restart ollama

# 选项 3：将其烘焙到自定义模型中（每个模型持久）
echo -e "FROM qwen2.5-coder:32b\nPARAMETER num_ctx 32768" > Modelfile
ollama create qwen2.5-coder-32k -f Modelfile
```

**您不能通过 OpenAI 兼容 API 设置上下文长度** (`/v1/chat/completions`)。必须在服务器端或通过 Modelfile 配置。这是将 Ollama 与 Hermes 等工具集成时最常见的混淆源。
:::

**验证您的上下文是否正确设置：**

```bash
ollama ps
# 查看 CONTEXT 列 — 它应该显示您配置的值
```

:::tip
使用 `ollama list` 列出可用模型。使用 `ollama pull <model>` 从 [Ollama 库](https://ollama.com/library) 拉取任何模型。Ollama 自动处理 GPU 卸载 — 大多数设置不需要配置。
:::

---

### vLLM — 高性能 GPU 推理

[vLLM](https://docs.vllm.ai/) 是生产 LLM 服务的标准。最适合：GPU 硬件上的最大吞吐量、服务大型模型、连续批处理。

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --max-model-len 65536 \
  --tensor-parallel-size 2 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

然后配置 Hermes：

```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入 URL: http://localhost:8000/v1
# 跳过 API 密钥（或如果您使用 --api-key 配置了 vLLM，则输入一个）
# 输入模型名称: meta-llama/Llama-3.1-70B-Instruct
```

**上下文长度：** vLLM 默认读取模型的 `max_position_embeddings`。如果超过您的 GPU 内存，它会出错并要求您设置更低的 `--max-model-len`。您也可以使用 `--max-model-len auto` 自动找到适合的最大值。设置 `--gpu-memory-utilization 0.95`（默认 0.9）以在 VRAM 中压缩更多上下文。

**工具调用需要显式标志：**

| 标志 | 用途 |
|------|------|
| `--enable-auto-tool-choice` | `tool_choice: "auto"` 需要（Hermes 中的默认值）|
| `--tool-call-parser <name>` | 模型工具调用格式的解析器 |

支持的解析器：`hermes`（Qwen 2.5，Hermes 2/3）、`llama3_json`（Llama 3.x）、`mistral`、`deepseek_v3`、`deepseek_v31`、`xlam`、`pythonic`。没有这些标志，工具调用将不起作用 — 模型会将工具调用作为文本输出。

:::tip
vLLM 支持人类可读的大小：`--max-model-len 64k`（小写 k = 1000，大写 K = 1024）。
:::

---

### SGLang — 带有 RadixAttention 的快速服务

[SGLang](https://github.com/sgl-project/sglang) 是 vLLM 的替代方案，具有用于 KV 缓存重用的 RadixAttention。最适合：多轮对话（前缀缓存）、约束解码、结构化输出。

```bash
pip install "sglang[all]"
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 30000 \
  --context-length 65536 \
  --tp 2 \
  --tool-call-parser qwen
```

然后配置 Hermes：

```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入 URL: http://localhost:30000/v1
# 输入模型名称: meta-llama/Llama-3.1-70B-Instruct
```

**上下文长度：** SGLang 默认从模型的配置中读取。使用 `--context-length` 覆盖。如果需要超过模型声明的最大值，设置 `SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1`。

**工具调用：** 使用 `--tool-call-parser` 和适合您模型系列的解析器：`qwen`（Qwen 2.5）、`llama3`、`llama4`、`deepseekv3`、`mistral`、`glm`。没有此标志，工具调用会以纯文本形式返回。

:::caution SGLang 默认最大输出为 128 令牌
如果响应似乎被截断，在请求中添加 `max_tokens` 或在服务器上设置 `--default-max-tokens`。如果未在请求中指定，SGLang 的默认值仅为每个响应 128 令牌。
:::

---

### llama.cpp / llama-server — CPU 和 Metal 推理

[llama.cpp](https://github.com/ggml-org/llama.cpp) 在 CPU、Apple Silicon（Metal）和消费级 GPU 上运行量化模型。最适合：在没有数据中心 GPU 的情况下运行模型、Mac 用户、边缘部署。

```bash
# 构建并启动 llama-server
cmake -B build && cmake --build build --config Release
./build/bin/llama-server \
  --jinja -fa \
  -c 32768 \
  -ngl 99 \
  -m models/qwen2.5-coder-32b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0
```

**上下文长度 (`-c`)：** 最近的构建默认为 `0`，从 GGUF 元数据中读取模型的训练上下文。对于具有 128k+ 训练上下文的模型，这可能会在尝试分配完整 KV 缓存时 OOM。明确设置 `-c` 为您需要的值（32k–64k 是代理使用的良好范围）。如果使用并行槽 (`-np`)，总上下文会在槽之间分配 — 使用 `-c 32768 -np 4`，每个槽只会获得 8k。

然后配置 Hermes 指向它：

```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入 URL: http://localhost:8080/v1
# 跳过 API 密钥（本地服务器不需要）
# 输入模型名称 — 或留空以在只加载一个模型时自动检测
```

这会将端点保存到 `config.yaml`，以便在会话之间保持。

:::caution `--jinja` 是工具调用所必需的
没有 `--jinja`，llama-server 会完全忽略 `tools` 参数。模型会尝试通过在响应文本中编写 JSON 来调用工具，但 Hermes 不会将其识别为工具调用 — 您会看到原始 JSON 如 `{"name": "web_search", ...}` 作为消息打印，而不是实际搜索。

原生工具调用支持（最佳性能）：Llama 3.x、Qwen 2.5（包括 Coder）、Hermes 2/3、Mistral、DeepSeek、Functionary。所有其他模型使用通用处理程序，工作但可能效率较低。有关完整列表，请参阅 [llama.cpp 函数调用文档](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md)。

您可以通过检查 `http://localhost:8080/props` 来验证工具支持是否激活 — 应该存在 `chat_template` 字段。
:::

:::tip
从 [Hugging Face](https://huggingface.co/models?library=gguf) 下载 GGUF 模型。Q4_K_M 量化提供质量与内存使用的最佳平衡。
:::

---

### LM Studio — 带有本地模型的桌面应用

[LM Studio](https://lmstudio.ai/) 是一个用于运行本地模型的桌面应用，带有 GUI。最适合：喜欢视觉界面的用户、快速模型测试、macOS/Windows/Linux 上的开发人员。

从 LM Studio 应用启动服务器（开发者选项卡 → 启动服务器），或使用 CLI：

```bash
lms server start                        # 在端口 1234 上启动
lms load qwen2.5-coder --context-length 32768
```

然后配置 Hermes：

```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入 URL: http://localhost:1234/v1
# 跳过 API 密钥（LM Studio 不需要）
# 输入模型名称
```

:::caution 上下文长度通常默认为 2048
LM Studio 从模型的元数据中读取上下文长度，但许多 GGUF 模型报告低默认值（2048 或 4096）。**始终在 LM Studio 模型设置中明确设置上下文长度**：

1. 点击模型选择器旁边的齿轮图标
2. 将 "Context Length" 设置为至少 16384（最好是 32768）
3. 重新加载模型使更改生效

或者，使用 CLI：`lms load model-name --context-length 32768`

要设置每个模型的持久默认值：我的模型选项卡 → 模型上的齿轮图标 → 设置上下文大小。
:::

**工具调用：** 自 LM Studio 0.3.6 起支持。具有原生工具调用训练的模型（Qwen 2.5、Llama 3.x、Mistral、Hermes）会被自动检测并显示工具徽章。其他模型使用可能不太可靠的通用回退。

---

### WSL2 网络（Windows 用户）

由于 Hermes Agent 需要 Unix 环境，Windows 用户在 WSL2 内部运行它。如果您的模型服务器（Ollama、LM Studio 等）在**Windows 主机**上运行，您需要桥接网络间隙 — WSL2 使用具有自己子网的虚拟网络适配器，因此 WSL2 内部的 `localhost` 指的是 Linux VM，**不是** Windows 主机。

:::tip 两者都在 WSL2 中？没问题。
如果您的模型服务器也在 WSL2 内部运行（vLLM、SGLang 和 llama-server 的常见情况），`localhost` 按预期工作 — 它们共享相同的网络命名空间。跳过本节。
:::

#### 选项 1：镜像网络模式（推荐）

在 **Windows 11 22H2+** 上可用，镜像模式使 `localhost` 在 Windows 和 WSL2 之间双向工作 — 最简单的修复方法。

1. 创建或编辑 `%USERPROFILE%\.wslconfig`（例如，`C:\Users\YourName\.wslconfig`）：
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

2. 从 PowerShell 重启 WSL：
   ```powershell
   wsl --shutdown
   ```

3. 重新打开 WSL2 终端。`localhost` 现在可以访问 Windows 服务：
   ```bash
   curl http://localhost:11434/v1/models   # Windows 上的 Ollama — 工作
   ```

:::note Hyper-V 防火墙
在某些 Windows 11 构建中，Hyper-V 防火墙默认阻止镜像连接。如果在启用镜像模式后 `localhost` 仍然不起作用，在**管理员 PowerShell** 中运行：
```powershell
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
```
:::

#### 选项 2：使用 Windows 主机 IP（Windows 10 / 旧版本）

如果您不能使用镜像模式，从 WSL2 内部找到 Windows 主机 IP 并使用它而不是 `localhost`：

```bash
# 获取 Windows 主机 IP（WSL2 虚拟网络的默认网关）
ip route show | grep -i default | awk '{ print $3 }'
# 示例输出：172.29.192.1
```

在您的 Hermes 配置中使用该 IP：

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://172.29.192.1:11434/v1   # Windows 主机 IP，不是 localhost
```

:::tip 动态助手
主机 IP 在 WSL2 重启时可能会更改。您可以在 shell 中动态获取它：
```bash
export WSL_HOST=$(ip route show | grep -i default | awk '{ print $3 }')
echo "Windows host at: $WSL_HOST"
curl http://$WSL_HOST:11434/v1/models   # 测试 Ollama
```

或者使用您机器的 mDNS 名称（需要 WSL2 中的 `libnss-mdns`）：
```bash
sudo apt install libnss-mdns
curl http://$(hostname).local:11434/v1/models
```
:::

#### 服务器绑定地址（NAT 模式所需）

如果您使用**选项 2**（带有主机 IP 的 NAT 模式），Windows 上的模型服务器必须接受来自 `127.0.0.1` 外部的连接。默认情况下，大多数服务器只监听 localhost — NAT 模式下的 WSL2 连接来自不同的虚拟子网，将被拒绝。在镜像模式下，`localhost` 直接映射，因此默认的 `127.0.0.1` 绑定工作正常。

| 服务器 | 默认绑定 | 如何修复 |
|--------|----------|----------|
| **Ollama** | `127.0.0.1` | 在启动 Ollama 之前设置 `OLLAMA_HOST=0.0.0.0` 环境变量（Windows 上的系统设置 → 环境变量，或编辑 Ollama 服务）|
| **LM Studio** | `127.0.0.1` | 在开发者选项卡 → 服务器设置中启用 **"Serve on Network"** |
| **llama-server** | `127.0.0.1` | 在启动命令中添加 `--host 0.0.0.0` |
| **vLLM** | `0.0.0.0` | 已经默认绑定到所有接口 |
| **SGLang** | `127.0.0.1` | 在启动命令中添加 `--host 0.0.0.0` |

**Windows 上的 Ollama（详细）：** Ollama 作为 Windows 服务运行。要设置 `OLLAMA_HOST`：
1. 打开 **系统属性** → **环境变量**
2. 添加新的 **系统变量**：`OLLAMA_HOST` = `0.0.0.0`
3. 重启 Ollama 服务（或重启）

#### Windows 防火墙

Windows 防火墙将 WSL2 视为单独的网络（在 NAT 和镜像模式下）。如果上述步骤后连接仍然失败，为模型服务器的端口添加防火墙规则：

```powershell
# 在管理员 PowerShell 中运行 — 将 PORT 替换为服务器的端口
New-NetFirewallRule -DisplayName "Allow WSL2 to Model Server" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434
```

常见端口：Ollama `11434`、vLLM `8000`、SGLang `30000`、llama-server `8080`、LM Studio `1234`。

#### 快速验证

从 WSL2 内部测试您是否可以访问模型服务器：

```bash
# 替换 URL 为您的服务器地址和端口
curl http://localhost:11434/v1/models          # 镜像模式
curl http://172.29.192.1:11434/v1/models       # NAT 模式（使用您实际的主机 IP）
```

如果您得到列出模型的 JSON 响应，就可以了。在您的 Hermes 配置中使用相同的 URL 作为 `base_url`。

---

### 故障排除本地模型

这些问题影响与 Hermes 一起使用的**所有**本地推理服务器。

#### 从 WSL2 到 Windows 托管的模型服务器的 "Connection refused"

如果您在 WSL2 内部运行 Hermes 并在 Windows 主机上运行模型服务器，WSL2 默认 NAT 网络模式下的 `http://localhost:<port>` 不会工作。请参阅上面的 [WSL2 网络](#wsl2-networking-windows-users) 部分获取修复方法。

#### 工具调用显示为文本而不是执行

模型输出类似 `{"name": "web_search", "arguments": {...}}` 的内容作为消息，而不是实际调用工具。

**原因：** 您的服务器没有启用工具调用，或者模型不通过服务器的工具调用实现支持它。

| 服务器 | 修复 |
|--------|------|
| **llama.cpp** | 在启动命令中添加 `--jinja` |
| **vLLM** | 添加 `--enable-auto-tool-choice --tool-call-parser hermes` |
| **SGLang** | 添加 `--tool-call-parser qwen`（或适当的解析器）|
| **Ollama** | 工具调用默认启用 — 确保您的模型支持它（使用 `ollama show model-name` 检查）|
| **LM Studio** | 更新到 0.3.6+ 并使用具有原生工具支持的模型 |

#### 模型似乎忘记上下文或给出不连贯的响应

**原因：** 上下文窗口太小。当对话超过上下文限制时，大多数服务器会静默丢弃较旧的消息。Hermes 的系统提示 + 工具模式本身就可以使用 4k–8k 令牌。

**诊断：**

```bash
# 检查 Hermes 认为的上下文
# 查看启动行："Context limit: X tokens"

# 检查服务器的实际上下文
# Ollama: ollama ps（CONTEXT 列）
# llama.cpp: curl http://localhost:8080/props | jq '.default_generation_settings.n_ctx'
# vLLM: 检查启动参数中的 --max-model-len
```

**修复：** 将上下文设置为代理使用的至少 **32,768 令牌**。请参阅上面每个服务器部分的特定标志。

#### 启动时 "Context limit: 2048 tokens"

Hermes 从服务器的 `/v1/models` 端点自动检测上下文长度。如果服务器报告低值（或根本不报告），Hermes 使用模型的声明限制，这可能是错误的。

**修复：** 在 `config.yaml` 中明确设置它：

```yaml
model:
  default: your-model
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 32768
```

#### 响应在句子中间被截断

**可能的原因：**
1. **服务器上的低输出上限 (`max_tokens`)** — SGLang 默认每个响应 128 令牌。在服务器上设置 `--default-max-tokens` 或在 config.yaml 中配置 Hermes 的 `model.max_tokens`。注意：`max_tokens` 仅控制响应长度 — 与对话历史可以多长无关（那是 `context_length`）。
2. **上下文耗尽** — 模型填满了其上下文窗口。增加 `model.context_length` 或在 Hermes 中启用 [上下文压缩](/docs/user-guide/configuration#context-compression)。

---

### LiteLLM 代理 — 多提供商网关

[LiteLLM](https://docs.litellm.ai/) 是一个 OpenAI 兼容的代理，将 100+ LLM 提供商统一在单个 API 后面。最适合：无需配置更改即可在提供商之间切换、负载平衡、备用链、预算控制。

```bash
# 安装并启动
pip install "litellm[proxy]"
litellm --model anthropic/claude-sonnet-4 --port 4000

# 或者使用配置文件配置多个模型：
litellm --config litellm_config.yaml --port 4000
```

然后使用 `hermes model` → 自定义端点 → `http://localhost:4000/v1` 配置 Hermes。

带有备用的 `litellm_config.yaml` 示例：
```yaml
model_list:
  - model_name: "best"
    litellm_params:
      model: anthropic/claude-sonnet-4
      api_key: sk-ant-...
  - model_name: "best"
    litellm_params:
      model: openai/gpt-4o
      api_key: sk-...
router_settings:
  routing_strategy: "latency-based-routing"
```

---

### ClawRouter — 成本优化路由

BlockRunAI 的 [ClawRouter](https://github.com/BlockRunAI/ClawRouter) 是一个本地路由代理，根据查询复杂性自动选择模型。它在 14 个维度上对请求进行分类，并路由到能够处理任务的最便宜模型。支付通过 USDC 加密货币（无需 API 密钥）。

```bash
# 安装并启动
npx @blockrun/clawrouter    # 在端口 8402 上启动
```

然后使用 `hermes model` → 自定义端点 → `http://localhost:8402/v1` → 模型名称 `blockrun/auto` 配置 Hermes。

路由配置文件：
| 配置文件 | 策略 | 节省 |
|---------|------|------|
| `blockrun/auto` | 平衡质量/成本 | 74-100% |
| `blockrun/eco` | 尽可能便宜 | 95-100% |
| `blockrun/premium` | 最佳质量模型 | 0% |
| `blockrun/free` | 仅免费模型 | 100% |
| `blockrun/agentic` | 针对工具使用优化 | 变化 |

:::note
ClawRouter 需要在 Base 或 Solana 上有 USDC 资金的钱包进行支付。所有请求都通过 BlockRun 的后端 API 路由。运行 `npx @blockrun/clawrouter doctor` 检查钱包状态。
:::

---

### 其他兼容提供商

任何具有 OpenAI 兼容 API 的服务都可以工作。一些流行的选项：

| 提供商 | 基础 URL | 说明 |
|--------|----------|------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | 云托管的开放模型 |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | 超快速推理 |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | DeepSeek 模型 |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | 快速开放模型托管 |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | 晶圆级芯片推理 |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Mistral 模型 |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | 直接 OpenAI 访问 |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | 企业 OpenAI |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | 自托管，多模型 |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | 带有本地模型的桌面应用 |

使用 `hermes model` → 自定义端点或在 `config.yaml` 中配置其中任何一个：

```yaml
model:
  default: meta-llama/Llama-3.1-70B-Instruct-Turbo
  provider: custom
  base_url: https://api.together.xyz/v1
  api_key: your-together-key
```

---

### 上下文长度检测

:::note 两个设置，容易混淆
**`context_length`** 是**总上下文窗口** — 输入*和*输出令牌的组合预算（例如 Claude Opus 4.6 为 200,000）。Hermes 使用此值来决定何时压缩历史并验证 API 请求。

**`model.max_tokens`** 是**输出上限** — 模型在*单个响应*中可能生成的最大令牌数。它与您的对话历史可以多长无关。行业标准名称 `max_tokens` 是常见的混淆源；Anthropic 的原生 API 后来将其重命名为 `max_output_tokens` 以明确。

当自动检测获取窗口大小错误时设置 `context_length`。
只有当您需要限制单个响应的长度时才设置 `model.max_tokens`。
:::

Hermes 使用多源解析链来检测您的模型和提供商的正确上下文窗口：

1. **配置覆盖** — config.yaml 中的 `model.context_length`（最高优先级）
2. **自定义提供商按模型** — `custom_providers[].models.<id>.context_length`
3. **持久缓存** — 先前发现的值（在重启后存活）
4. **端点 `/models`** — 查询服务器的 API（本地/自定义端点）
5. **Anthropic `/v1/models`** — 查询 Anthropic 的 API 获取 `max_input_tokens`（仅 API 密钥用户）
6. **OpenRouter API** — 来自 OpenRouter 的实时模型元数据
7. **Nous Portal** — 将 Nous 模型 ID 与 OpenRouter 元数据后缀匹配
8. **[models.dev](https://models.dev)** — 社区维护的注册表，包含 100+ 提供商的 3800+ 模型的提供商特定上下文长度
9. **回退默认值** — 广泛的模型系列模式（128K 默认）

对于大多数设置，这开箱即用。系统是提供商感知的 — 同一模型根据谁提供它可能有不同的上下文限制（例如，`claude-opus-4.6` 在 Anthropic 直接上是 1M，但在 GitHub Copilot 上是 128K）。

要明确设置上下文长度，向模型配置添加 `context_length`：

```yaml
model:
  default: "qwen3.5:9b"
  base_url: "http://localhost:8080/v1"
  context_length: 131072  # 令牌
```

对于自定义端点，您还可以按模型设置上下文长度：

```yaml
custom_providers:
  - name: "My Local LLM"
    base_url: "http://localhost:11434/v1"
    models:
      qwen3.5:27b:
        context_length: 32768
      deepseek-r1:70b:
        context_length: 65536
```

配置自定义端点时，`hermes model` 会提示输入上下文长度。留空以进行自动检测。

:::tip 何时手动设置
- 您使用带有自定义 `num_ctx` 的 Ollama，该值低于模型的最大值
- 您想要将上下文限制在模型最大值以下（例如，在 128k 模型上使用 8k 以节省 VRAM）
- 您在不暴露 `/v1/models` 的代理后面运行
:::

---

### 命名的自定义提供商

如果您使用多个自定义端点（例如，本地开发服务器和远程 GPU 服务器），您可以在 `config.yaml` 中将它们定义为命名的自定义提供商：

```yaml
custom_providers:
  - name: local
    base_url: http://localhost:8080/v1
    # 省略 api_key — Hermes 对无密钥本地服务器使用 "no-key-required"
  - name: work
    base_url: https://gpu-server.internal.corp/v1
    api_key: corp-api-key
    api_mode: chat_completions   # 可选，从 URL 自动检测
  - name: anthropic-proxy
    base_url: https://proxy.example.com/anthropic
    api_key: proxy-key
    api_mode: anthropic_messages  # 用于兼容 Anthropic 的代理
```

使用三重语法在会话中切换它们：

```
/model custom:local:qwen-2.5       # 使用 "local" 端点和 qwen-2.5
/model custom:work:llama3-70b      # 使用 "work" 端点和 llama3-70b
/model custom:anthropic-proxy:claude-sonnet-4  # 使用代理
```

您还可以从交互式 `hermes model` 菜单中选择命名的自定义提供商。

---

### 选择正确的设置

| 使用场景 | 推荐 |
|----------|------|
| **只想让它工作** | OpenRouter（默认）或 Nous Portal |
| **本地模型，简单设置** | Ollama |
| **生产 GPU 服务** | vLLM 或 SGLang |
| **Mac / 无 GPU** | Ollama 或 llama.cpp |
| **多提供商路由** | LiteLLM 代理或 OpenRouter |
| **成本优化** | ClawRouter 或带有 `sort: "price"` 的 OpenRouter |
| **最大隐私** | Ollama、vLLM 或 llama.cpp（完全本地）|
| **企业 / Azure** | Azure OpenAI 与自定义端点 |
| **中国 AI 模型** | z.ai（GLM）、Kimi/Moonshot（`kimi-coding` 或 `kimi-coding-cn`）、MiniMax 或小米 MiMo（一流提供商）|

:::tip
您可以随时使用 `hermes model` 在提供商之间切换 — 无需重启。无论使用哪个提供商，您的对话历史、内存和技能都会保留。
:::

## 可选 API 密钥

| 功能 | 提供商 | 环境变量 |
|---------|----------|--------------|
| 网页抓取 | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY`, `FIRECRAWL_API_URL` |
| 浏览器自动化 | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| 图像生成 | [FAL](https://fal.ai/) | `FAL_KEY` |
| 高级 TTS 语音 | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| OpenAI TTS + 语音转录 | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| Mistral TTS + 语音转录 | [Mistral](https://console.mistral.ai/) | `MISTRAL_API_KEY` |
| RL 训练 | [Tinker](https://tinker-console.thinkingmachines.ai/) + [WandB](https://wandb.ai/) | `TINKER_API_KEY`, `WANDB_API_KEY` |
| 跨会话用户建模 | [Honcho](https://honcho.dev/) | `HONCHO_API_KEY` |
| 语义长期记忆 | [Supermemory](https://supermemory.ai) | `SUPERMEMORY_API_KEY` |

### 自托管 Firecrawl

默认情况下，Hermes 使用 [Firecrawl 云 API](https://firecrawl.dev/) 进行网络搜索和抓取。如果您更喜欢在本地运行 Firecrawl，可以将 Hermes 指向自托管实例。有关完整设置说明，请参阅 Firecrawl 的 [SELF_HOST.md](https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md)。

**您获得的：** 无需 API 密钥，无速率限制，无每页成本，完全数据主权。

**您失去的：** 云版本使用 Firecrawl 的专有"Fire-engine"进行高级反机器人绕过（Cloudflare、验证码、IP 轮换）。自托管使用基本 fetch + Playwright，因此一些受保护的站点可能会失败。搜索使用 DuckDuckGo 而不是 Google。

**设置：**

1. 克隆并启动 Firecrawl Docker 堆栈（5 个容器：API、Playwright、Redis、RabbitMQ、PostgreSQL — 需要 ~4-8 GB RAM）：
   ```bash
   git clone https://github.com/firecrawl/firecrawl
   cd firecrawl
   # 在 .env 中设置：USE_DB_AUTHENTICATION=false, HOST=0.0.0.0, PORT=3002
   docker compose up -d
   ```

2. 将 Hermes 指向您的实例（无需 API 密钥）：
   ```bash
   hermes config set FIRECRAWL_API_URL http://localhost:3002
   ```

如果您的自托管实例启用了身份验证，您也可以同时设置 `FIRECRAWL_API_KEY` 和 `FIRECRAWL_API_URL`。

## OpenRouter 提供商路由

使用 OpenRouter 时，您可以控制请求如何在提供商之间路由。在 `~/.hermes/config.yaml` 中添加 `provider_routing` 部分：

```yaml
provider_routing:
  sort: "throughput"          # "price"（默认）、"throughput" 或 "latency"
  # only: ["anthropic"]      # 仅使用这些提供商
  # ignore: ["deepinfra"]    # 跳过这些提供商
  # order: ["anthropic", "google"]  # 按此顺序尝试提供商
  # require_parameters: true  # 仅使用支持所有请求参数的提供商
  # data_collection: "deny"   # 排除可能存储/训练数据的提供商
```

**快捷方式：** 将 `:nitro` 附加到任何模型名称以进行吞吐量排序（例如，`anthropic/claude-sonnet-4:nitro`），或 `:floor` 进行价格排序。

## 备用模型

配置一个备份 provider:model，当您的主模型失败（速率限制、服务器错误、认证失败）时，Hermes 会自动切换到它：

```yaml
fallback_model:
  provider: openrouter                    # 必需
  model: anthropic/claude-sonnet-4        # 必需
  # base_url: http://localhost:8000/v1    # 可选，用于自定义端点
  # api_key_env: MY_CUSTOM_KEY           # 可选，自定义端点 API 密钥的环境变量名称
```

激活时，备用会在会话中切换模型和提供商，而不会丢失您的对话。它在**每个会话中最多触发一次**。

支持的提供商：`openrouter`、`nous`、`openai-codex`、`copilot`、`copilot-acp`、`anthropic`、`huggingface`、`zai`、`kimi-coding`、`kimi-coding-cn`、`minimax`、`minimax-cn`、`deepseek`、`ai-gateway`、`opencode-zen`、`opencode-go`、`kilocode`、`xiaomi`、`arcee`、`alibaba`、`custom`。

:::tip
备用完全通过 `config.yaml` 配置 — 没有用于它的环境变量。有关它何时触发、支持的提供商以及它如何与辅助任务和委托交互的完整详细信息，请参阅 [备用提供商](/docs/user-guide/features/fallback-providers)。
:::

## 智能模型路由

可选的廉价 vs 强大路由让 Hermes 保留您的主模型用于复杂工作，同时将非常短/简单的轮次发送到更便宜的模型。

```yaml
smart_model_routing:
  enabled: true
  max_simple_chars: 160
  max_simple_words: 28
  cheap_model:
    provider: openrouter
    model: google/gemini-2.5-flash
    # base_url: http://localhost:8000/v1  # 可选自定义端点
    # api_key_env: MY_CUSTOM_KEY          # 可选该端点的环境变量名称
```

工作原理：
- 如果轮次短、单行且看起来不包含大量代码/工具/调试内容，Hermes 可能会将其路由到 `cheap_model`
- 如果轮次看起来复杂，Hermes 会留在您的主模型/提供商上
- 如果廉价路由无法干净地解析，Hermes 会自动回退到主模型

这是有意保守的。它适用于快速、低风险的轮次，如：
- 简短的事实问题
- 快速重写
- 轻量级摘要

它会避免路由看起来像以下内容的提示：
- 编码/调试工作
- 工具密集型请求
- 长或多行分析请求