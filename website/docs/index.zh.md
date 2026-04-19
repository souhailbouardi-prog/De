---
slug: /
sidebar_position: 0
title: "Hermes Agent 文档"
description: "由 Nous Research 构建的自改进 AI 代理。内置学习循环，从经验中创建技能，在使用过程中改进它们，并在会话之间保持记忆。"
hide_table_of_contents: true
displayed_sidebar: docs
---

# Hermes Agent

由 [Nous Research](https://nousresearch.com) 构建的自改进 AI 代理。唯一具有内置学习循环的代理 — 它从经验中创建技能，在使用过程中改进它们，促使自己持久化知识，并在会话之间建立关于你的深化模型。

<div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap'}}>
  <a href="/docs/getting-started/installation.zh" style={{display: 'inline-block', padding: '0.6rem 1.2rem', backgroundColor: '#FFD700', color: '#07070d', borderRadius: '8px', fontWeight: 600, textDecoration: 'none'}}>开始使用 →</a>
  <a href="https://github.com/NousResearch/hermes-agent" style={{display: 'inline-block', padding: '0.6rem 1.2rem', border: '1px solid rgba(255,215,0,0.2)', borderRadius: '8px', textDecoration: 'none'}}>在 GitHub 上查看</a>
</div>

## 什么是 Hermes Agent？

它不是一个绑定到 IDE 的编码副驾驶，也不是一个围绕单个 API 的聊天机器人包装器。它是一个**自主代理**，运行时间越长，能力越强。它可以在你放置的任何地方运行 — 一个 5 美元的 VPS、GPU 集群或无服务器基础设施（Daytona、Modal），空闲时几乎不花费任何成本。当它在你从未自己 SSH 进入的云 VM 上工作时，你可以通过 Telegram 与它交谈。它不绑定到你的笔记本电脑。

## 快速链接

| | |
|---|---|
| 🚀 **[安装](/docs/getting-started/installation.zh)** | 在 60 秒内在 Linux、macOS 或 WSL2 上安装 |
| 📖 **[快速入门教程](/docs/getting-started/quickstart.zh)** | 你的第一次对话和要尝试的关键功能 |
| 🗺️ **[学习路径](/docs/getting-started/learning-path.zh)** | 为你的经验水平找到合适的文档 |
| ⚙️ **[配置](/docs/user-guide/configuration.zh)** | 配置文件、提供商、模型和选项 |
| 💬 **[消息网关](/docs/user-guide/messaging/index.zh)** | 设置 Telegram、Discord、Slack 或 WhatsApp |
| 🔧 **[工具和工具集](/docs/user-guide/features/tools.zh)** | 47 个内置工具及其配置方法 |
| 🧠 **[记忆系统](/docs/user-guide/features/memory.zh)** | 跨会话增长的持久记忆 |
| 📚 **[技能系统](/docs/user-guide/features/skills.zh)** | 代理创建和重用的程序记忆 |
| 🔌 **[MCP 集成](/docs/user-guide/features/mcp.zh)** | 连接到 MCP 服务器，过滤其工具，安全扩展 Hermes |
| 🧭 **[在 Hermes 中使用 MCP](/docs/guides/use-mcp-with-hermes.zh)** | 实用的 MCP 设置模式、示例和教程 |
| 🎙️ **[语音模式](/docs/user-guide/features/voice-mode.zh)** | 在 CLI、Telegram、Discord 和 Discord VC 中的实时语音交互 |
| 🗣️ **[在 Hermes 中使用语音模式](/docs/guides/use-voice-mode-with-hermes.zh)** | Hermes 语音工作流的实际设置和使用模式 |
| 🎭 **[个性与 SOUL.md](/docs/user-guide/features/personality.zh)** | 使用全局 SOUL.md 定义 Hermes 的默认声音 |
| 📄 **[上下文文件](/docs/user-guide/features/context-files.zh)** | 塑造每次对话的项目上下文文件 |
| 🔒 **[安全](/docs/user-guide/security.zh)** | 命令批准、授权、容器隔离 |
| 💡 **[提示与最佳实践](/docs/guides/tips.zh)** | 充分利用 Hermes 的快速技巧 |
| 🏗️ **[架构](/docs/developer-guide/architecture.zh)** | 其底层工作原理 |
| ❓ **[常见问题与故障排除](/docs/reference/faq.zh)** | 常见问题和解决方案 |

## 主要功能

- **封闭学习循环** — 代理管理的记忆，定期提醒，自主技能创建，使用过程中的技能自我改进，带 LLM 摘要的 FTS5 跨会话回忆，以及 [Honcho](https://github.com/plastic-labs/honcho) 辩证用户建模
- **可在任何地方运行，不仅仅是你的笔记本电脑** — 6 个终端后端：本地、Docker、SSH、Daytona、Singularity、Modal。Daytona 和 Modal 提供无服务器持久性 — 你的环境在空闲时休眠，几乎不花费任何成本
- **在你所在的地方生活** — CLI、Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Mattermost、Email、SMS、钉钉、飞书、企业微信、BlueBubbles、Home Assistant — 一个网关支持 15+ 平台
- **由模型训练师构建** — 由 [Nous Research](https://nousresearch.com) 创建，该实验室背后有 Hermes、Nomos 和 Psyche。与 [Nous Portal](https://portal.nousresearch.com)、[OpenRouter](https://openrouter.ai)、OpenAI 或任何端点配合使用
- **计划自动化** — 内置 cron，可交付到任何平台
- **委派和并行化** — 为并行工作流生成隔离的子代理。通过 `execute_code` 进行编程工具调用，将多步管道折叠为单个推理调用
- **开放标准技能** — 与 [agentskills.io](https://agentskills.io) 兼容。技能可移植、可共享，并通过 Skills Hub 由社区贡献
- **完整的网络控制** — 搜索、提取、浏览、视觉、图像生成、TTS
- **MCP 支持** — 连接到任何 MCP 服务器以获得扩展的工具能力
- **研究就绪** — 批处理、轨迹导出、使用 Atropos 进行 RL 训练。由 [Nous Research](https://nousresearch.com) 构建 — 该实验室背后有 Hermes、Nomos 和 Psyche 模型