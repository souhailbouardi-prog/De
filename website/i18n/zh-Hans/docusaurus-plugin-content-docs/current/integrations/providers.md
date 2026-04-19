---
title: "AI 提供商"
sidebar_label: "AI 提供商"
sidebar_position: 1
---

# AI 提供商

本页面涵盖为 Hermes Agent 设置推理提供商 — 从像 OpenRouter 和 Anthropic 这样的云 API，到像 Ollama 和 vLLM 这样的自托管端点，再到高级路由和故障转移配置。您需要至少配置一个提供商才能使用 Hermes。

## 推理提供商

您需要至少一种连接到 LLM 的方式。使用 `hermes model` 交互式切换提供商和模型，或直接配置：

| 提供商 | 设置 |
|----------|-------|
| **Nous Portal** | `hermes model` (OAuth，基于订阅) |
| **OpenAI Codex** | `hermes model` (ChatGPT OAuth，使用 Codex 模型) |
| **GitHub Copilot** | `hermes model` (OAuth 设备代码流，`COPILOT_GITHUB_TOKEN`，`GH_TOKEN`，或 `gh auth token`) |
| **GitHub Copilot ACP** | `hermes model` (生成本地 `copilot --acp --stdio`) |
| **Anthropic** | `hermes model` (通过 Claude Code 认证的 Claude Pro/Max，Anthropic API 密钥，或手动设置令牌) |
| **OpenRouter** | `OPENROUTER_API_KEY` 在 `~/.hermes/.env` 中 |
| **AI Gateway** | `AI_GATEWAY_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `ai-gateway`) |
| **z.ai / GLM** | `GLM_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `zai`) |
| **Kimi / Moonshot** | `KIMI_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `kimi-coding`) |
| **Kimi / Moonshot (China)** | `KIMI_CN_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `kimi-coding-cn`; 别名: `kimi-cn`, `moonshot-cn`) |
| **Arcee AI** | `ARCEEAI_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `arcee`; 别名: `arcee-ai`, `arceeai`) |
| **MiniMax** | `MINIMAX_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `minimax`) |
| **MiniMax China** | `MINIMAX_CN_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `minimax-cn`) |
| **Alibaba Cloud** | `DASHSCOPE_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `alibaba`, 别名: `dashscope`, `qwen`) |
| **Kilo Code** | `KILOCODE_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `kilocode`) |
| **Xiaomi MiMo** | `XIAOMI_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `xiaomi`, 别名: `mimo`, `xiaomi-mimo`) |
| **OpenCode Zen** | `OPENCODE_ZEN_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `opencode-zen`) |
| **OpenCode Go** | `OPENCODE_GO_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `opencode-go`) |
| **DeepSeek** | `DEEPSEEK_API_KEY` 在 `~/.hermes/.env` 中 (提供商: `deepseek`) |
| **Hugging Face** | `HF_TOKEN` 在 `~/.hermes/.env` 中 (提供商: `huggingface`, 别名: `hf`) |
| **Google / Gemini** | `GOOGLE_API_KEY` (或 `GEMINI_API_KEY`) 在 `~/.hermes/.env` 中 (提供商: `gemini`) |
| **自定义端点** | `hermes model` → 选择"自定义端点" (保存在 `config.yaml` 中) |

:::tip 模型键别名
在 `model:` 配置部分，您可以使用 `default:` 或 `model:` 作为模型 ID 的键名。`model: { default: my-model }` 和 `model: { model: my-model }` 都同样有效。
:::

:::info Codex 说明
OpenAI Codex 提供商通过设备代码进行认证（打开 URL，输入代码）。Hermes 将生成的凭据存储在其自己的认证存储中，位于 `~/.hermes/auth.json`，并且可以在存在时从 `~/.codex/auth.json` 导入现有的 Codex CLI 凭据。不需要安装 Codex CLI。
:::

:::warning
即使使用 Nous Portal、Codex 或自定义端点，某些工具（视觉、网络摘要、MoA）使用单独的"辅助"模型 — 默认通过 OpenRouter 使用 Gemini Flash。`OPENROUTER_API_KEY` 会自动启用这些工具。您还可以配置这些工具使用哪个模型和提供商 — 参见[辅助模型](/docs/user-guide/configuration#auxiliary-models)。
:::"}

### Anthropic (Native)

Use Claude models directly through the Anthropic API — no OpenRouter proxy needed. Supports three auth methods:

```bash
# With an API key (pay-per-token)
export ANTHROPIC_API_KEY=***
hermes chat --provider anthropic --model claude-sonnet-4-6

# Preferred: authenticate through `hermes model`
# Hermes will use Claude Code's credential store directly when available
hermes model

# Manual override with a setup-token (fallback / legacy)
export ANTHROPIC_TOKEN=***  # setup-token or manual OAuth token
hermes chat --provider anthropic

# Auto-detect Claude Code credentials (if you already use Claude Code)
hermes chat --provider anthropic  # reads Claude Code credential files automatically
```

When you choose Anthropic OAuth through `hermes model`, Hermes prefers Claude Code's own credential store over copying the token into `~/.hermes/.env`. That keeps refreshable Claude credentials refreshable.

Or set it permanently:
```yaml
model:
  provider: "anthropic"
  default: "claude-sonnet-4-6"
```

:::tip Aliases
`--provider claude` and `--provider claude-code` also work as shorthand for `--provider anthropic`.
:::

### GitHub Copilot

Hermes supports GitHub Copilot as a first-class provider with two modes:

**`copilot` — Direct Copilot API** (recommended). Uses your GitHub Copilot subscription to access GPT-5.x, Claude, Gemini, and other models through the Copilot API.

```bash
hermes chat --provider copilot --model gpt-5.4
```

**Authentication options** (checked in this order):

1. `COPILOT_GITHUB_TOKEN` environment variable
2. `GH_TOKEN` environment variable
3. `GITHUB_TOKEN` environment variable
4. `gh auth token` CLI fallback

If no token is found, `hermes model` offers an **OAuth device code login** — the same flow used by the Copilot CLI and opencode.

:::warning Token types
The Copilot API does **not** support classic Personal Access Tokens (`ghp_*`). Supported token types:

| Type | Prefix | How to get |
|------|--------|------------|
| OAuth token | `gho_` | `hermes model` → GitHub Copilot → Login with GitHub |
| Fine-grained PAT | `github_pat_` | GitHub Settings → Developer settings → Fine-grained tokens (needs **Copilot Requests** permission) |
| GitHub App token | `ghu_` | Via GitHub App installation |

If your `gh auth token` returns a `ghp_*` token, use `hermes model` to authenticate via OAuth instead.
:::

**API routing**: GPT-5+ models (except `gpt-5-mini`) automatically use the Responses API. All other models (GPT-4o, Claude, Gemini, etc.) use Chat Completions. Models are auto-detected from the live Copilot catalog.

**`copilot-acp` — Copilot ACP agent backend**. Spawns the local Copilot CLI as a subprocess:

```bash
hermes chat --provider copilot-acp --model copilot-acp
# Requires the GitHub Copilot CLI in PATH and an existing `copilot login` session
```

**Permanent config:**
```yaml
model:
  provider: "copilot"
  default: "gpt-5.4"
```

| Environment variable | Description |
|---------------------|-------------|
| `COPILOT_GITHUB_TOKEN` | GitHub token for Copilot API (first priority) |
| `HERMES_COPILOT_ACP_COMMAND` | Override the Copilot CLI binary path (default: `copilot`) |
| `HERMES_COPILOT_ACP_ARGS` | Override ACP args (default: `--acp --stdio`) |

### First-Class Chinese AI Providers

These providers have built-in support with dedicated provider IDs. Set the API key and use `--provider` to select:

```bash
# z.ai / ZhipuAI GLM
hermes chat --provider zai --model glm-5
# Requires: GLM_API_KEY in ~/.hermes/.env

# Kimi / Moonshot AI (international: api.moonshot.ai)
hermes chat --provider kimi-coding --model kimi-for-coding
# Requires: KIMI_API_KEY in ~/.hermes/.env

# Kimi / Moonshot AI (China: api.moonshot.cn)
hermes chat --provider kimi-coding-cn --model kimi-k2.5
# Requires: KIMI_CN_API_KEY in ~/.hermes/.env

# MiniMax (global endpoint)
hermes chat --provider minimax --model MiniMax-M2.7
# Requires: MINIMAX_API_KEY in ~/.hermes/.env

# MiniMax (China endpoint)
hermes chat --provider minimax-cn --model MiniMax-M2.7
# Requires: MINIMAX_CN_API_KEY in ~/.hermes/.env

# Alibaba Cloud / DashScope (Qwen models)
hermes chat --provider alibaba --model qwen3.5-plus
# Requires: DASHSCOPE_API_KEY in ~/.hermes/.env

# Xiaomi MiMo
hermes chat --provider xiaomi --model mimo-v2-pro
# Requires: XIAOMI_API_KEY in ~/.hermes/.env

# Arcee AI (Trinity models)
hermes chat --provider arcee --model trinity-large-thinking
# Requires: ARCEEAI_API_KEY in ~/.hermes/.env
```

Or set the provider permanently in `config.yaml`:
```yaml
model:
  provider: "zai"       # or: kimi-coding, kimi-coding-cn, minimax, minimax-cn, alibaba, xiaomi, arcee
  default: "glm-5"
```

Base URLs can be overridden with `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, `MINIMAX_CN_BASE_URL`, `DASHSCOPE_BASE_URL`, or `XIAOMI_BASE_URL` environment variables.

:::note Z.AI Endpoint Auto-Detection
When using the Z.AI / GLM provider, Hermes automatically probes multiple endpoints (global, China, coding variants) to find one that accepts your API key. You don't need to set `GLM_BASE_URL` manually — the working endpoint is detected and cached automatically.
:::

### xAI (Grok) Prompt Caching

When using xAI as a provider (any base URL containing `x.ai`), Hermes automatically enables prompt caching by sending the `x-grok-conv-id` header with every API request. This routes requests to the same server within a conversation session, allowing xAI's infrastructure to reuse cached system prompts and conversation history.

No configuration is needed — caching activates automatically when an xAI endpoint is detected and a session ID is available. This reduces latency and cost for multi-turn conversations.

### Hugging Face Inference Providers

[Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers) routes to 20+ open models through a unified OpenAI-compatible endpoint (`router.huggingface.co/v1`). Requests are automatically routed to the fastest available backend (Groq, Together, SambaNova, etc.) with automatic failover.

```bash
# Use any available model
hermes chat --provider huggingface --model Qwen/Qwen3-235B-A22B-Thinking-2507
# Requires: HF_TOKEN in ~/.hermes/.env

# Short alias
hermes chat --provider hf --model deepseek-ai/DeepSeek-V3.2
```

Or set it permanently in `config.yaml`:
```yaml
model:
  provider: "huggingface"
  default: "Qwen/Qwen3-235B-A22B-Thinking-2507"
```

Get your token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — make sure to enable the "Make calls to Inference Providers" permission. Free tier included ($0.10/month credit, no markup on provider rates).

You can append routing suffixes to model names: `:fastest` (default), `:cheapest`, or `:provider_name` to force a specific backend.

The base URL can be overridden with `HF_BASE_URL`.

## 自定义和自托管 LLM 提供商

Hermes Agent 适用于**任何 OpenAI 兼容的 API 端点**。如果服务器实现了 `/v1/chat/completions`，您就可以指向它。这意味着您可以使用本地模型、GPU 推理服务器、多提供商路由或任何第三方 API。

### 常规设置

配置自定义端点的三种方式：

**交互式设置（推荐）：**
```bash
hermes model
# 选择 "Custom endpoint (self-hosted / VLLM / etc.)"
# 输入：API 基础 URL、API 密钥、模型名称
```

**手动配置（`config.yaml`）：**
```yaml
# 在 ~/.hermes/config.yaml 中
model:
  default: your-model-name
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: your-key-or-leave-empty-for-local
```

:::warning 旧环境变量
`.env` 中的 `OPENAI_BASE_URL` 和 `LLM_MODEL` 已被**移除**。Hermes 的任何部分都不会读取它们 — `config.yaml` 是模型和端点配置的单一真相来源。如果您 `.env` 中有过时的条目，它们会在下次 `hermes setup` 或配置迁移时自动清除。请直接使用 `hermes model` 或编辑 `config.yaml`。

两种方法都会持久化到 `config.yaml`，这是模型、提供商和基础 URL 的真相来源。

### 使用 `/model` 切换模型

配置自定义端点后，您可以中途切换模型：

```
/model custom:qwen-2.5          # 切换到自定义端点上的模型
/model custom                    # 自动从端点检测模型
/model openrouter:claude-sonnet-4 # 切换回云提供商
```

如果您配置了**命名自定义提供商**（见下文），请使用三语法：

```
/model custom:local:qwen-2.5    # 使用 "local" 自定义提供商和模型 qwen-2.5
/model custom:work:llama3       # 使用 "work" 自定义提供商和 llama3
```

When switching providers, Hermes persists the base URL and provider to config so the change survives restarts. When switching away from a custom endpoint to a built-in provider, the stale base URL is automatically cleared.

:::tip
`/model custom` (bare, no model name) queries your endpoint's `/models` API and auto-selects the model if exactly one is loaded. Useful for local servers running a single model.
:::

Everything below follows this same pattern — just change the URL, key, and model name.

---

### Ollama — Local Models, Zero Config

[Ollama](https://ollama.com/) runs open-weight models locally with one command. Best for: quick local experimentation, privacy-sensitive work, offline use. Supports tool calling via the OpenAI-compatible API.

```bash
# Install and run a model
ollama pull qwen2.5-coder:32b
ollama serve   # Starts on port 11434
```

Then configure Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:11434/v1
# Skip API key (Ollama doesn't need one)
# Enter model name (e.g. qwen2.5-coder:32b)
```

Or configure `config.yaml` directly:

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 32768   # See warning below
```

:::caution Ollama defaults to very low context lengths
Ollama does **not** use your model's full context window by default. Depending on your VRAM, the default is:

| Available VRAM | Default context |
|----------------|----------------|
| Less than 24 GB | **4,096 tokens** |
| 24–48 GB | 32,768 tokens |
| 48+ GB | 256,000 tokens |

For agent use with tools, **you need at least 16k–32k context**. At 4k, the system prompt + tool schemas alone can fill the window, leaving no room for conversation.

**How to increase it** (pick one):

```bash
# Option 1: Set server-wide via environment variable (recommended)
OLLAMA_CONTEXT_LENGTH=32768 ollama serve

# Option 2: For systemd-managed Ollama
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_CONTEXT_LENGTH=32768"
# Then: sudo systemctl daemon-reload && sudo systemctl restart ollama

# Option 3: Bake it into a custom model (persistent per-model)
echo -e "FROM qwen2.5-coder:32b\nPARAMETER num_ctx 32768" > Modelfile
ollama create qwen2.5-coder-32k -f Modelfile
```

**You cannot set context length through the OpenAI-compatible API** (`/v1/chat/completions`). It must be configured server-side or via a Modelfile. This is the #1 source of confusion when integrating Ollama with tools like Hermes.
:::

**Verify your context is set correctly:**

```bash
ollama ps
# Look at the CONTEXT column — it should show your configured value
```

:::tip
List available models with `ollama list`. Pull any model from the [Ollama library](https://ollama.com/library) with `ollama pull <model>`. Ollama handles GPU offloading automatically — no configuration needed for most setups.
:::

---

### vLLM — High-Performance GPU Inference

[vLLM](https://docs.vllm.ai/) is the standard for production LLM serving. Best for: maximum throughput on GPU hardware, serving large models, continuous batching.

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --max-model-len 65536 \
  --tensor-parallel-size 2 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Then configure Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:8000/v1
# Skip API key (or enter one if you configured vLLM with --api-key)
# Enter model name: meta-llama/Llama-3.1-70B-Instruct
```

**Context length:** vLLM reads the model's `max_position_embeddings` by default. If that exceeds your GPU memory, it errors and asks you to set `--max-model-len` lower. You can also use `--max-model-len auto` to automatically find the maximum that fits. Set `--gpu-memory-utilization 0.95` (default 0.9) to squeeze more context into VRAM.

**Tool calling requires explicit flags:**

| Flag | Purpose |
|------|---------|
| `--enable-auto-tool-choice` | Required for `tool_choice: "auto"` (the default in Hermes) |
| `--tool-call-parser <name>` | Parser for the model's tool call format |

Supported parsers: `hermes` (Qwen 2.5, Hermes 2/3), `llama3_json` (Llama 3.x), `mistral`, `deepseek_v3`, `deepseek_v31`, `xlam`, `pythonic`. Without these flags, tool calls won't work — the model will output tool calls as text.

:::tip
vLLM supports human-readable sizes: `--max-model-len 64k` (lowercase k = 1000, uppercase K = 1024).
:::

---

### SGLang — Fast Serving with RadixAttention

[SGLang](https://github.com/sgl-project/sglang) is an alternative to vLLM with RadixAttention for KV cache reuse. Best for: multi-turn conversations (prefix caching), constrained decoding, structured output.

```bash
pip install "sglang[all]"
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 30000 \
  --context-length 65536 \
  --tp 2 \
  --tool-call-parser qwen
```

Then configure Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:30000/v1
# Enter model name: meta-llama/Llama-3.1-70B-Instruct
```

**Context length:** SGLang reads from the model's config by default. Use `--context-length` to override. If you need to exceed the model's declared maximum, set `SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1`.

**Tool calling:** Use `--tool-call-parser` with the appropriate parser for your model family: `qwen` (Qwen 2.5), `llama3`, `llama4`, `deepseekv3`, `mistral`, `glm`. Without this flag, tool calls come back as plain text.

:::caution SGLang defaults to 128 max output tokens
If responses seem truncated, add `max_tokens` to your requests or set `--default-max-tokens` on the server. SGLang's default is only 128 tokens per response if not specified in the request.
:::

---

### llama.cpp / llama-server — CPU & Metal Inference

[llama.cpp](https://github.com/ggml-org/llama.cpp) runs quantized models on CPU, Apple Silicon (Metal), and consumer GPUs. Best for: running models without a datacenter GPU, Mac users, edge deployment.

```bash
# Build and start llama-server
cmake -B build && cmake --build build --config Release
./build/bin/llama-server \
  --jinja -fa \
  -c 32768 \
  -ngl 99 \
  -m models/qwen2.5-coder-32b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0
```

**Context length (`-c`):** Recent builds default to `0` which reads the model's training context from the GGUF metadata. For models with 128k+ training context, this can OOM trying to allocate the full KV cache. Set `-c` explicitly to what you need (32k–64k is a good range for agent use). If using parallel slots (`-np`), the total context is divided among slots — with `-c 32768 -np 4`, each slot only gets 8k.

Then configure Hermes to point at it:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:8080/v1
# Skip API key (local servers don't need one)
# Enter model name — or leave blank to auto-detect if only one model is loaded
```

This saves the endpoint to `config.yaml` so it persists across sessions.

:::caution `--jinja` is required for tool calling
Without `--jinja`, llama-server ignores the `tools` parameter entirely. The model will try to call tools by writing JSON in its response text, but Hermes won't recognize it as a tool call — you'll see raw JSON like `{"name": "web_search", ...}` printed as a message instead of an actual search.

Native tool calling support (best performance): Llama 3.x, Qwen 2.5 (including Coder), Hermes 2/3, Mistral, DeepSeek, Functionary. All other models use a generic handler that works but may be less efficient. See the [llama.cpp function calling docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md) for the full list.

You can verify tool support is active by checking `http://localhost:8080/props` — the `chat_template` field should be present.
:::

:::tip
Download GGUF models from [Hugging Face](https://huggingface.co/models?library=gguf). Q4_K_M quantization offers the best balance of quality vs. memory usage.
:::

---

### LM Studio — Desktop App with Local Models

[LM Studio](https://lmstudio.ai/) is a desktop app for running local models with a GUI. Best for: users who prefer a visual interface, quick model testing, developers on macOS/Windows/Linux.

Start the server from the LM Studio app (Developer tab → Start Server), or use the CLI:

```bash
lms server start                        # Starts on port 1234
lms load qwen2.5-coder --context-length 32768
```

Then configure Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:1234/v1
# Skip API key (LM Studio doesn't require one)
# Enter model name
```

:::caution Context length often defaults to 2048
LM Studio reads context length from the model's metadata, but many GGUF models report low defaults (2048 or 4096). **Always set context length explicitly** in the LM Studio model settings:

1. Click the gear icon next to the model picker
2. Set "Context Length" to at least 16384 (preferably 32768)
3. Reload the model for the change to take effect

Alternatively, use the CLI: `lms load model-name --context-length 32768`

To set persistent per-model defaults: My Models tab → gear icon on the model → set context size.
:::

**Tool calling:** Supported since LM Studio 0.3.6. Models with native tool-calling training (Qwen 2.5, Llama 3.x, Mistral, Hermes) are auto-detected and shown with a tool badge. Other models use a generic fallback that may be less reliable.

---

### WSL2 Networking (Windows Users)

Since Hermes Agent requires a Unix environment, Windows users run it inside WSL2. If your model server (Ollama, LM Studio, etc.) runs on the **Windows host**, you need to bridge the network gap — WSL2 uses a virtual network adapter with its own subnet, so `localhost` inside WSL2 refers to the Linux VM, **not** the Windows host.

:::tip Both in WSL2? No problem.
If your model server also runs inside WSL2 (common for vLLM, SGLang, and llama-server), `localhost` works as expected — they share the same network namespace. Skip this section.
:::

#### Option 1: Mirrored Networking Mode (Recommended)

Available on **Windows 11 22H2+**, mirrored mode makes `localhost` work bidirectionally between Windows and WSL2 — the simplest fix.

1. Create or edit `%USERPROFILE%\.wslconfig` (e.g., `C:\Users\YourName\.wslconfig`):
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

2. Restart WSL from PowerShell:
   ```powershell
   wsl --shutdown
   ```

3. Reopen your WSL2 terminal. `localhost` now reaches Windows services:
   ```bash
   curl http://localhost:11434/v1/models   # Ollama on Windows — works
   ```

:::note Hyper-V Firewall
On some Windows 11 builds, the Hyper-V firewall blocks mirrored connections by default. If `localhost` still doesn't work after enabling mirrored mode, run this in an **Admin PowerShell**:
```powershell
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
```
:::

#### Option 2: Use the Windows Host IP (Windows 10 / older builds)

If you can't use mirrored mode, find the Windows host IP from inside WSL2 and use that instead of `localhost`:

```bash
# Get the Windows host IP (the default gateway of WSL2's virtual network)
ip route show | grep -i default | awk '{ print $3 }'
# Example output: 172.29.192.1
```

Use that IP in your Hermes config:

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://172.29.192.1:11434/v1   # Windows host IP, not localhost
```

:::tip Dynamic helper
The host IP can change on WSL2 restart. You can grab it dynamically in your shell:
```bash
export WSL_HOST=$(ip route show | grep -i default | awk '{ print $3 }')
echo "Windows host at: $WSL_HOST"
curl http://$WSL_HOST:11434/v1/models   # Test Ollama
```

Or use your machine's mDNS name (requires `libnss-mdns` in WSL2):
```bash
sudo apt install libnss-mdns
curl http://$(hostname).local:11434/v1/models
```
:::

#### Server Bind Address (Required for NAT Mode)

If you're using **Option 2** (NAT mode with the host IP), the model server on Windows must accept connections from outside `127.0.0.1`. By default, most servers only listen on localhost — WSL2 connections in NAT mode come from a different virtual subnet and will be refused. In mirrored mode, `localhost` maps directly so the default `127.0.0.1` binding works fine.

| Server | Default bind | How to fix |
|--------|-------------|------------|
| **Ollama** | `127.0.0.1` | Set `OLLAMA_HOST=0.0.0.0` environment variable before starting Ollama (System Settings → Environment Variables on Windows, or edit the Ollama service) |
| **LM Studio** | `127.0.0.1` | Enable **"Serve on Network"** in the Developer tab → Server settings |
| **llama-server** | `127.0.0.1` | Add `--host 0.0.0.0` to the startup command |
| **vLLM** | `0.0.0.0` | Already binds to all interfaces by default |
| **SGLang** | `127.0.0.1` | Add `--host 0.0.0.0` to the startup command |

**Ollama on Windows (detailed):** Ollama runs as a Windows service. To set `OLLAMA_HOST`:
1. Open **System Properties** → **Environment Variables**
2. Add a new **System variable**: `OLLAMA_HOST` = `0.0.0.0`
3. Restart the Ollama service (or reboot)

#### Windows Firewall

Windows Firewall treats WSL2 as a separate network (in both NAT and mirrored mode). If connections still fail after the steps above, add a firewall rule for your model server's port:

```powershell
# Run in Admin PowerShell — replace PORT with your server's port
New-NetFirewallRule -DisplayName "Allow WSL2 to Model Server" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434
```

Common ports: Ollama `11434`, vLLM `8000`, SGLang `30000`, llama-server `8080`, LM Studio `1234`.

#### Quick Verification

From inside WSL2, test that you can reach your model server:

```bash
# Replace URL with your server's address and port
curl http://localhost:11434/v1/models          # Mirrored mode
curl http://172.29.192.1:11434/v1/models       # NAT mode (use your actual host IP)
```

If you get a JSON response listing your models, you're good. Use that same URL as the `base_url` in your Hermes config.

---

### Troubleshooting Local Models

These issues affect **all** local inference servers when used with Hermes.

#### "Connection refused" from WSL2 to a Windows-hosted model server

If you're running Hermes inside WSL2 and your model server on the Windows host, `http://localhost:<port>` won't work in WSL2's default NAT networking mode. See [WSL2 Networking](#wsl2-networking-windows-users) above for the fix.

#### Tool calls appear as text instead of executing

The model outputs something like `{"name": "web_search", "arguments": {...}}` as a message instead of actually calling the tool.

**Cause:** Your server doesn't have tool calling enabled, or the model doesn't support it through the server's tool calling implementation.

| Server | Fix |
|--------|-----|
| **llama.cpp** | Add `--jinja` to the startup command |
| **vLLM** | Add `--enable-auto-tool-choice --tool-call-parser hermes` |
| **SGLang** | Add `--tool-call-parser qwen` (or appropriate parser) |
| **Ollama** | Tool calling is enabled by default — make sure your model supports it (check with `ollama show model-name`) |
| **LM Studio** | Update to 0.3.6+ and use a model with native tool support |

#### Model seems to forget context or give incoherent responses

**Cause:** Context window is too small. When the conversation exceeds the context limit, most servers silently drop older messages. Hermes's system prompt + tool schemas alone can use 4k–8k tokens.

**Diagnosis:**

```bash
# Check what Hermes thinks the context is
# Look at startup line: "Context limit: X tokens"

# Check your server's actual context
# Ollama: ollama ps (CONTEXT column)
# llama.cpp: curl http://localhost:8080/props | jq '.default_generation_settings.n_ctx'
# vLLM: check --max-model-len in startup args
```

**Fix:** Set context to at least **32,768 tokens** for agent use. See each server's section above for the specific flag.

#### "Context limit: 2048 tokens" at startup

Hermes auto-detects context length from your server's `/v1/models` endpoint. If the server reports a low value (or doesn't report one at all), Hermes uses the model's declared limit which may be wrong.

**Fix:** Set it explicitly in `config.yaml`:

```yaml
model:
  default: your-model
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 32768
```

#### Responses get cut off mid-sentence

**Possible causes:**
1. **Low output cap (`max_tokens`) on the server** — SGLang defaults to 128 tokens per response. Set `--default-max-tokens` on the server or configure Hermes with `model.max_tokens` in config.yaml. Note: `max_tokens` controls response length only — it is unrelated to how long your conversation history can be (that is `context_length`).
2. **Context exhaustion** — The model filled its context window. Increase `model.context_length` or enable [context compression](/docs/user-guide/configuration#context-compression) in Hermes.

---

### LiteLLM Proxy — Multi-Provider Gateway

[LiteLLM](https://docs.litellm.ai/) is an OpenAI-compatible proxy that unifies 100+ LLM providers behind a single API. Best for: switching between providers without config changes, load balancing, fallback chains, budget controls.

```bash
# Install and start
pip install "litellm[proxy]"
litellm --model anthropic/claude-sonnet-4 --port 4000

# Or with a config file for multiple models:
litellm --config litellm_config.yaml --port 4000
```

Then configure Hermes with `hermes model` → Custom endpoint → `http://localhost:4000/v1`.

Example `litellm_config.yaml` with fallback:
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

### ClawRouter — Cost-Optimized Routing

[ClawRouter](https://github.com/BlockRunAI/ClawRouter) by BlockRunAI is a local routing proxy that auto-selects models based on query complexity. It classifies requests across 14 dimensions and routes to the cheapest model that can handle the task. Payment is via USDC cryptocurrency (no API keys).

```bash
# Install and start
npx @blockrun/clawrouter    # Starts on port 8402
```

Then configure Hermes with `hermes model` → Custom endpoint → `http://localhost:8402/v1` → model name `blockrun/auto`.

Routing profiles:
| Profile | Strategy | Savings |
|---------|----------|---------|
| `blockrun/auto` | Balanced quality/cost | 74-100% |
| `blockrun/eco` | Cheapest possible | 95-100% |
| `blockrun/premium` | Best quality models | 0% |
| `blockrun/free` | Free models only | 100% |
| `blockrun/agentic` | Optimized for tool use | varies |

:::note
ClawRouter requires a USDC-funded wallet on Base or Solana for payment. All requests route through BlockRun's backend API. Run `npx @blockrun/clawrouter doctor` to check wallet status.
:::

---

### Other Compatible Providers

Any service with an OpenAI-compatible API works. Some popular options:

| Provider | Base URL | Notes |
|----------|----------|-------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | Cloud-hosted open models |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | Ultra-fast inference |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | DeepSeek models |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | Fast open model hosting |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | Wafer-scale chip inference |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Mistral models |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | Direct OpenAI access |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | Enterprise OpenAI |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | Self-hosted, multi-model |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | Desktop app with local models |

Configure any of these with `hermes model` → Custom endpoint, or in `config.yaml`:

```yaml
model:
  default: meta-llama/Llama-3.1-70B-Instruct-Turbo
  provider: custom
  base_url: https://api.together.xyz/v1
  api_key: your-together-key
```

---

### Context Length Detection

:::note Two settings, easy to confuse
**`context_length`** is the **total context window** — the combined budget for input *and* output tokens (e.g. 200,000 for Claude Opus 4.6). Hermes uses this to decide when to compress history and to validate API requests.

**`model.max_tokens`** is the **output cap** — the maximum number of tokens the model may generate in a *single response*. It has nothing to do with how long your conversation history can be. The industry-standard name `max_tokens` is a common source of confusion; Anthropic's native API has since renamed it `max_output_tokens` for clarity.

Set `context_length` when auto-detection gets the window size wrong.
Set `model.max_tokens` only when you need to limit how long individual responses can be.
:::

Hermes uses a multi-source resolution chain to detect the correct context window for your model and provider:

1. **Config override** — `model.context_length` in config.yaml (highest priority)
2. **Custom provider per-model** — `custom_providers[].models.<id>.context_length`
3. **Persistent cache** — previously discovered values (survives restarts)
4. **Endpoint `/models`** — queries your server's API (local/custom endpoints)
5. **Anthropic `/v1/models`** — queries Anthropic's API for `max_input_tokens` (API-key users only)
6. **OpenRouter API** — live model metadata from OpenRouter
7. **Nous Portal** — suffix-matches Nous model IDs against OpenRouter metadata
8. **[models.dev](https://models.dev)** — community-maintained registry with provider-specific context lengths for 3800+ models across 100+ providers
9. **Fallback defaults** — broad model family patterns (128K default)

For most setups this works out of the box. The system is provider-aware — the same model can have different context limits depending on who serves it (e.g., `claude-opus-4.6` is 1M on Anthropic direct but 128K on GitHub Copilot).

To set the context length explicitly, add `context_length` to your model config:

```yaml
model:
  default: "qwen3.5:9b"
  base_url: "http://localhost:8080/v1"
  context_length: 131072  # tokens
```

For custom endpoints, you can also set context length per model:

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

`hermes model` will prompt for context length when configuring a custom endpoint. Leave it blank for auto-detection.

:::tip When to set this manually
- You're using Ollama with a custom `num_ctx` that's lower than the model's maximum
- You want to limit context below the model's maximum (e.g., 8k on a 128k model to save VRAM)
- You're running behind a proxy that doesn't expose `/v1/models`
:::

---

### Named Custom Providers

If you work with multiple custom endpoints (e.g., a local dev server and a remote GPU server), you can define them as named custom providers in `config.yaml`:

```yaml
custom_providers:
  - name: local
    base_url: http://localhost:8080/v1
    # api_key omitted — Hermes uses "no-key-required" for keyless local servers
  - name: work
    base_url: https://gpu-server.internal.corp/v1
    api_key: corp-api-key
    api_mode: chat_completions   # optional, auto-detected from URL
  - name: anthropic-proxy
    base_url: https://proxy.example.com/anthropic
    api_key: proxy-key
    api_mode: anthropic_messages  # for Anthropic-compatible proxies
```

Switch between them mid-session with the triple syntax:

```
/model custom:local:qwen-2.5       # Use the "local" endpoint with qwen-2.5
/model custom:work:llama3-70b      # Use the "work" endpoint with llama3-70b
/model custom:anthropic-proxy:claude-sonnet-4  # Use the proxy
```

You can also select named custom providers from the interactive `hermes model` menu.

---

### Choosing the Right Setup

| Use Case | Recommended |
|----------|-------------|
| **Just want it to work** | OpenRouter (default) or Nous Portal |
| **Local models, easy setup** | Ollama |
| **Production GPU serving** | vLLM or SGLang |
| **Mac / no GPU** | Ollama or llama.cpp |
| **Multi-provider routing** | LiteLLM Proxy or OpenRouter |
| **Cost optimization** | ClawRouter or OpenRouter with `sort: "price"` |
| **Maximum privacy** | Ollama, vLLM, or llama.cpp (fully local) |
| **Enterprise / Azure** | Azure OpenAI with custom endpoint |
| **Chinese AI models** | z.ai (GLM), Kimi/Moonshot (`kimi-coding` or `kimi-coding-cn`), MiniMax, or Xiaomi MiMo (first-class providers) |

:::tip
You can switch between providers at any time with `hermes model` — no restart required. Your conversation history, memory, and skills carry over regardless of which provider you use.
:::

## 可选 API 密钥

| 功能 | 提供商 | 环境变量 |
|---------|----------|--------------|
| 网页抓取 | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY`、`FIRECRAWL_API_URL` |
| 浏览器自动化 | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`、`BROWSERBASE_PROJECT_ID` |
| 图像生成 | [FAL](https://fal.ai/) | `FAL_KEY` |
| 高级 TTS 语音 | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| OpenAI TTS + 语音转录 | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| Mistral TTS + 语音转录 | [Mistral](https://console.mistral.ai/) | `MISTRAL_API_KEY` |
| RL 训练 | [Tinker](https://tinker-console.thinkingmachines.ai/) + [WandB](https://wandb.ai/) | `TINKER_API_KEY`、`WANDB_API_KEY` |
| 跨会话用户建模 | [Honcho](https://honcho.dev/) | `HONCO_API_KEY` |
| 语义长期记忆 | [Supermemory](https://supermemory.ai) | `SUPERMEMORY_API_KEY` |

### 自托管 Firecrawl

默认情况下，Hermes 使用 [Firecrawl 云 API](https://firecrawl.dev/) 进行网页搜索和抓取。如果您更喜欢在本地运行 Firecrawl，您可以改为指向自托管实例。请参阅 Firecrawl 的 [SELF_HOST.md](https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md) 获取完整的设置说明。

**您将获得：** 无需 API 密钥，无速率限制，无每页费用，完全数据主权。

**您将失去：** 云版本使用 Firecrawl 专有的 "Fire-engine" 进行高级反机器人绕过（Cloudflare、CAPTCHA、IP 轮换）。自托管使用基本 fetch + Playwright，因此一些受保护的站点可能会失败。搜索使用 DuckDuckGo 而不是 Google。

**设置：**

1. 克隆并启动 Firecrawl Docker 堆栈（5 个容器：API、Playwright、Redis、RabbitMQ、PostgreSQL — 需要约 4-8 GB RAM）：
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

当使用 OpenRouter 时，您可以控制请求在提供商之间的路由方式。在 `~/.hermes/config.yaml` 中添加 `provider_routing` 部分：

```yaml
provider_routing:
  sort: "throughput"          # "price"（默认）、"throughput" 或 "latency"
  # only: ["anthropic"]      # 只使用这些提供商
  # ignore: ["deepinfra"]    # 跳过这些提供商
  # order: ["anthropic", "google"]  # 按此顺序尝试提供商
  # require_parameters: true  # 只使用支持所有请求参数的提供商
  # data_collection: "deny"   # 排除可能存储/训练数据的提供商
```

**快捷方式：** 在任何模型名称后附加 `:nitro` 以进行吞吐量排序（例如 `anthropic/claude-sonnet-4:nitro`），或附加 `:floor` 进行价格排序。

## 备用模型

配置备份的 provider:model，当您的主模型失败时（速率限制、服务器错误、身份验证失败），Hermes 会自动切换到该模型：

```yaml
fallback_model:
  provider: openrouter                    # 必需
  model: anthropic/claude-sonnet-4        # 必需
  # base_url: http://localhost:8000/v1    # 可选，用于自定义端点
  # api_key_env: MY_CUSTOM_KEY           # 可选，自定义端点 API 密钥的环境变量名
```

激活后，备用模型会在会话中途切换模型和提供商，而不会丢失您的对话。它每个会话最多触发**一次**。

支持的提供商：`openrouter`、`nous`、`openai-codex`、`copilot`、`copilot-acp`、`anthropic`、`huggingface`、`zai`、`kimi-coding`、`kimi-coding-cn`、`minimax`、`minimax-cn`、`deepseek`、`ai-gateway`、`opencode-zen`、`opencode-go`、`kilocode`、`xiaomi`、`arcee`、`alibaba`、`custom`。

:::tip
备用模型仅通过 `config.yaml` 配置 — 没有环境变量用于它。有关其触发时机、支持的提供商以及如何与辅助任务和委托交互的完整详细信息，请参阅[备用提供商](/docs/user-guide/features/fallback-providers)。
:::

## 智能模型路由

可选的廉价与强路由让 Hermes 将您的主模型保留用于复杂工作，同时将非常短/简单的轮次发送到更便宜的模型。

```yaml
smart_model_routing:
  enabled: true
  max_simple_chars: 160
  max_simple_words: 28
  cheap_model:
    provider: openrouter
    model: google/gemini-2.5-flash
    # base_url: http://localhost:8000/v1  # 可选自定义端点
    # api_key_env: MY_CUSTOM_KEY          # 可选该端点 API 密钥的环境变量名
```

工作原理：
- 如果轮次很短、单行且看起来不像是代码/工具/调试密集型，Hermes 可能会将其路由到 `cheap_model`
- 如果轮次看起来复杂，Hermes 会保持在您的主模型/提供商上
- 如果廉价路由无法干净地解析，Hermes 会自动回退到主模型

这是有意保守的。它适用于快速、低风险的轮次，例如：
- 简短的事实问题
- 快速重写
- 轻量级摘要

它会避免路由看起来像以下内容的提示：
- 编码/调试工作
- 工具密集型请求
- 长的或多行的分析请求

当您想要更低的延迟或成本而不想完全更改默认模型时，请使用此功能。

---

## 另请参阅

- [配置](/docs/user-guide/configuration) — 常规配置（目录结构、配置优先级、终端后端、内存、压缩等）
- [环境变量](/docs/reference/environment-variables) — 所有环境变量的完整参考