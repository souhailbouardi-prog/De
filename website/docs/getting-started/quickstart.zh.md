---
sidebar_position: 1
title: "快速开始"
description: "与Hermes Agent的第一次对话 — 从安装到聊天只需2分钟"
---

# 快速开始

本指南将引导您安装Hermes Agent、设置提供商并进行第一次对话。完成后，您将了解其关键功能并知道如何进一步探索。

## 1. 安装Hermes Agent

运行单行安装程序：

```bash
# Linux / macOS / WSL2 / Android (Termux)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

:::tip Android / Termux
如果您在手机上安装，请参阅专门的[Termux指南](./termux.zh.md)了解经过测试的手动安装路径、支持的附加功能以及当前Android特定的限制。
:::

:::tip Windows用户
请先安装[WSL2](https://learn.microsoft.com/zh-cn/windows/wsl/install)，然后在WSL2终端中运行上述命令。
:::

安装完成后，重新加载您的shell：

```bash
source ~/.bashrc   # 或 source ~/.zshrc
```

## 2. 设置提供商

安装程序会自动配置您的LLM提供商。稍后要更改它，请使用以下命令之一：

```bash
hermes model       # 选择您的LLM提供商和模型
hermes tools       # 配置启用哪些工具
hermes setup       # 或一次性配置所有内容
```

`hermes model`会引导您选择推理提供商：

| 提供商 | 说明 | 如何设置 |
|----------|-----------|---------------|
| **Nous Portal** | 基于订阅，零配置 | 通过`hermes model`进行OAuth登录 |
| **OpenAI Codex** | ChatGPT OAuth，使用Codex模型 | 通过`hermes model`进行设备代码认证 |
| **Anthropic** | 直接使用Claude模型（Pro/Max或API密钥） | 使用Claude Code认证或Anthropic API密钥运行`hermes model` |
| **OpenRouter** | 跨多个模型的多提供商路由 | 输入您的API密钥 |
| **Z.AI** | GLM / 智谱托管的模型 | 设置`GLM_API_KEY` / `ZAI_API_KEY` |
| **Kimi / Moonshot** | Moonshot托管的编码和聊天模型 | 设置`KIMI_API_KEY` |
| **Kimi / Moonshot China** | 中国区域的Moonshot端点 | 设置`KIMI_CN_API_KEY` |
| **Arcee AI** | Trinity模型 | 设置`ARCEEAI_API_KEY` |
| **MiniMax** | 国际MiniMax端点 | 设置`MINIMAX_API_KEY` |
| **MiniMax China** | 中国区域的MiniMax端点 | 设置`MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | 通过DashScope的Qwen模型 | 设置`DASHSCOPE_API_KEY` |
| **Hugging Face** | 通过统一路由器的20+开放模型（Qwen、DeepSeek、Kimi等） | 设置`HF_TOKEN` |
| **Kilo Code** | KiloCode托管的模型 | 设置`KILOCODE_API_KEY` |
| **OpenCode Zen** | 按使用付费访问精选模型 | 设置`OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | $10/月订阅开放模型 | 设置`OPENCODE_GO_API_KEY` |
| **DeepSeek** | 直接访问DeepSeek API | 设置`DEEPSEEK_API_KEY` |
| **NVIDIA NIM** | 通过build.nvidia.com或本地NIM的Nemotron模型 | 设置`NVIDIA_API_KEY`（可选：`NVIDIA_BASE_URL`） |
| **Ollama Cloud** | 无需本地GPU的托管Ollama目录 | 设置`OLLAMA_API_KEY`（或在`hermes model`中选择**Ollama Cloud**） |
| **Google Gemini (OAuth)** | 通过Cloud Code Assist的Gemini — 免费和付费层级 | 通过`hermes model`进行OAuth（可选：`HERMES_GEMINI_PROJECT_ID`用于付费层级） |
| **xAI (Grok)** | 通过Responses API + 提示缓存的Grok 4模型 | 设置`XAI_API_KEY`（别名：`grok`） |
| **GitHub Copilot** | GitHub Copilot订阅（GPT-5.x、Claude、Gemini等） | 通过`hermes model`进行OAuth，或设置`COPILOT_GITHUB_TOKEN` / `GH_TOKEN` |
| **GitHub Copilot ACP** | Copilot ACP代理后端（生成本地`copilot` CLI） | `hermes model`（需要`copilot` CLI + `copilot login`） |
| **Vercel AI Gateway** | Vercel AI Gateway路由 | 设置`AI_GATEWAY_API_KEY` |
| **Custom Endpoint** | VLLM、SGLang、Ollama或任何OpenAI兼容的API | 设置基础URL + API密钥 |

:::caution 最小上下文：64K tokens
Hermes Agent需要至少**64,000 tokens**上下文的模型。上下文窗口较小的模型无法为多步骤工具调用工作流保持足够的工作内存，会在启动时被拒绝。大多数托管模型（Claude、GPT、Gemini、Qwen、DeepSeek）都轻松满足此要求。如果您运行本地模型，请将其上下文大小设置为至少64K（例如，对于llama.cpp使用`--ctx-size 65536`，对于Ollama使用`-c 65536`）。
:::

:::tip
您可以随时使用`hermes model`切换提供商 — 无需代码更改，无锁定。配置自定义端点时，Hermes会提示输入上下文窗口大小，并在可能时自动检测。有关详细信息，请参阅[上下文长度检测](../integrations/providers.md#context-length-detection)。
:::

## 3. 开始聊天

```bash
hermes            # 经典CLI
hermes --tui      # 现代TUI（推荐）
```

就是这样！您会看到一个欢迎横幅，显示您的模型、可用工具和技能。输入消息并按Enter键。

:::tip 选择您的界面
Hermes提供两个终端界面：经典的`prompt_toolkit` CLI和较新的[TUI](../user-guide/tui.zh.md)，后者具有模态覆盖、鼠标选择和非阻塞输入。两者共享相同的会话、斜杠命令和配置 — 尝试使用`hermes` vs `hermes --tui`。
:::

```
❯ 您能帮我做什么？
```

该代理可以使用网络搜索、文件操作、终端命令等工具 — 全部开箱即用。

## 4. 尝试关键功能

### 让它使用终端

```
❯ 我的磁盘使用情况如何？显示前5个最大的目录。
```

代理将代表您运行终端命令并显示结果。

### 使用斜杠命令

输入`/`查看所有命令的自动完成下拉菜单：

| 命令 | 功能 |
|---------|-------------|
| `/help` | 显示所有可用命令 |
| `/tools` | 列出可用工具 |
| `/model` | 交互式切换模型 |
| `/personality pirate` | 尝试有趣的个性 |
| `/save` | 保存对话 |

### 多行输入

按`Alt+Enter`或`Ctrl+J`添加新行。非常适合粘贴代码或编写详细提示。

### 中断代理

如果代理花费时间太长，只需输入新消息并按Enter键 — 它会中断当前任务并切换到您的新指令。`Ctrl+C`也有效。

### 恢复会话

当您退出时，hermes会打印恢复命令：

```bash
hermes --continue    # 恢复最近的会话
hermes -c            # 简短形式
```

## 5. 进一步探索

以下是接下来可以尝试的一些事情：

### 设置沙盒终端

为安全起见，在Docker容器或远程服务器中运行代理：

```bash
hermes config set terminal.backend docker    # Docker隔离
hermes config set terminal.backend ssh       # 远程服务器
```

### 连接消息平台

通过Telegram、Discord、Slack、WhatsApp、Signal、Email或Home Assistant从您的手机或其他设备与Hermes聊天：

```bash
hermes gateway setup    # 交互式平台配置
```

### 添加语音模式

想在CLI中使用麦克风输入或在消息传递中使用语音回复？

```bash
pip install "hermes-agent[voice]"
# 包含用于免费本地语音转文本的faster-whisper
```

然后启动Hermes并在CLI中启用它：

```text
/voice on
```

按`Ctrl+B`录制，或使用`/voice tts`让Hermes说出其回复。有关CLI、Telegram、Discord和Discord语音频道的完整设置，请参阅[语音模式](../user-guide/features/voice-mode.md)。

### 安排自动任务

```
❯ 每天早上9点，检查Hacker News的AI新闻并通过Telegram向我发送摘要。
```

代理将设置一个通过网关自动运行的cron作业。

### 浏览和安装技能

```bash
hermes skills search kubernetes
hermes skills search react --source skills-sh
hermes skills search https://mintlify.com/docs --source well-known
hermes skills install openai/skills/k8s
hermes skills install official/security/1password
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
```

提示：
- 使用`--source skills-sh`搜索公共`skills.sh`目录。
- 使用`--source well-known`和文档/站点URL从`/.well-known/skills/index.json`发现技能。
- 仅在审核第三方技能后使用`--force`。它可以覆盖非危险的策略阻止，但不能覆盖`dangerous`扫描 verdict。

或者在聊天中使用`/skills`斜杠命令。

### 通过ACP在编辑器中使用Hermes

Hermes还可以作为ACP服务器运行，用于VS Code、Zed和JetBrains等ACP兼容编辑器：

```bash
pip install -e '.[acp]'
hermes acp
```

有关设置详细信息，请参阅[ACP编辑器集成](../user-guide/features/acp.md)。

### 尝试MCP服务器

通过模型上下文协议连接到外部工具：

```yaml
# 添加到 ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

---

## 快速参考

| 命令 | 描述 |
|---------|-------------|
| `hermes` | 开始聊天 |
| `hermes model` | 选择您的LLM提供商和模型 |
| `hermes tools` | 配置每个平台启用哪些工具 |
| `hermes setup` | 完整设置向导（一次性配置所有内容） |
| `hermes doctor` | 诊断问题 |
| `hermes update` | 更新到最新版本 |
| `hermes gateway` | 启动消息网关 |
| `hermes --continue` | 恢复上次会话 |

## 后续步骤

- **[CLI指南](../user-guide/cli.zh.md)** — 掌握终端界面
- **[配置](../user-guide/configuration.zh.md)** — 自定义您的设置
- **[消息网关](../user-guide/messaging/index.md)** — 连接Telegram、Discord、Slack、WhatsApp、Signal、Email或Home Assistant
- **[工具和工具集](../user-guide/features/tools.zh.md)** — 探索可用功能