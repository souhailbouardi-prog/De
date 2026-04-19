---
slug: /
sidebar_position: 0
title: "Hermes Agent 文档"
description: "由 Nous Research 构建的自学习 AI 智能体。内置学习循环，从经验中创建技能，在使用过程中改进它们，并在会话间记住知识。"
hide_table_of_contents: true
---

# Hermes Agent

由 [Nous Research](https://nousresearch.com) 构建的自学习 AI 智能体。唯一具有内置学习循环的智能体 — 它从经验中创建技能，在使用过程中改进它们，自我提醒保持知识持久性，并在会话间建立对您身份的深入模型。

<div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap'}}>
  <a href="/docs/zh-Hans/getting-started/installation" style={{display: 'inline-block', padding: '0.6rem 1.2rem', backgroundColor: '#FFD700', color: '#07070d', borderRadius: '8px', fontWeight: 600, textDecoration: 'none'}}>开始使用 →</a>
  <a href="https://github.com/NousResearch/hermes-agent" style={{display: 'inline-block', padding: '0.6rem 1.2rem', border: '1px solid rgba(255,215,0,0.2)', borderRadius: '8px', textDecoration: 'none'}}>在 GitHub 上查看</a>
</div>

## 什么是 Hermes Agent？

它不是绑定到 IDE 的编码辅助工具，也不是围绕单一 API 的聊天机器人包装器。它是一个**自主智能体**，运行时间越长，能力越强。它可以部署在任何地方 — 5 美元的 VPS、GPU 集群，或几乎在空闲时不花费任何成本的服务器基础设施（Daytona、Modal）。您可以通过 Telegram 与它对话，而它在您从未 SSH 进入的云 VM 上工作。它不绑定于您的笔记本电脑。

## 快速链接

| | |
|---|---|
| 🚀 **[安装指南](/docs/zh-Hans/getting-started/installation)** | 在 Linux、macOS 或 WSL2 上 60 秒内安装 |
| 📖 **[快速入门教程](/docs/zh-Hans/getting-started/quickstart)** | 您的第一次对话和要尝试的关键功能 |
| 🗺️ **[学习路径](/docs/zh-Hans/getting-started/learning-path)** | 根据您的经验水平找到合适的文档 |
| ⚙️ **[配置](/docs/zh-Hans/user-guide/configuration)** | 配置文件、提供商、模型和选项 |
| 💬 **[消息网关](/docs/zh-Hans/user-guide/messaging)** | 设置 Telegram、Discord、Slack 或 WhatsApp |
| 🔧 **[工具和工具集](/docs/zh-Hans/user-guide/features/tools)** | 47 个内置工具及其配置方法 |
| 🧠 **[记忆系统](/docs/zh-Hans/user-guide/features/memory)** | 在会话间增长的持久记忆 |
| 📚 **[技能系统](/docs/zh-Hans/user-guide/features/skills)** | 智能体创建和重用的程序性记忆 |
| 🔌 **[MCP 集成](/docs/zh-Hans/user-guide/features/mcp)** | 连接到 MCP 服务器，过滤它们的工具，安全地扩展 Hermes |
| 🧭 **[使用 MCP 与 Hermes](/docs/zh-Hans/guides/use-mcp-with-hermes)** | 实用的 MCP 设置模式、示例和教程 |
| 🎙️ **[语音模式](/docs/zh-Hans/user-guide/features/voice-mode)** | 在 CLI、Telegram、Discord 和 Discord VC 中的实时语音交互 |
| 🗣️ **[使用语音模式与 Hermes](/docs/zh-Hans/guides/use-voice-mode-with-hermes)** | Hermes 语音工作流程的实践设置和使用模式 |
| 🎭 **[个性和 SOUL.md](/docs/zh-Hans/user-guide/features/personality)** | 使用全局 SOUL.md 定义 Hermes 的默认声音 |
| 📄 **[上下文文件](/docs/zh-Hans/user-guide/features/context-files)** | 塑造每次对话的项目上下文文件 |
| 🔒 **[安全性](/docs/zh-Hans/user-guide/security)** | 命令批准、授权、容器隔离 |
| 💡 **[技巧和最佳实践](/docs/zh-Hans/guides/tips)** | 充分利用 Hermes 的快速技巧 |
| 🏗️ **[架构](/docs/zh-Hans/developer-guide/architecture)** | 底层工作原理 |
| ❓ **[常见问题与故障排除](/docs/zh-Hans/reference/faq)** | 常见问题和解决方案 |

## 关键特性

- **封闭式学习循环** — 智能体管理的记忆，定期提醒，自主技能创建，使用过程中技能自我改进，带有 LLM 摘要的 FTS5 跨会话召回，以及 [Honcho](https://github.com/plastic-labs/honcho) 辩证用户建模
- **随处运行，不限于您的笔记本电脑** — 6 种终端后端：本地、Docker、SSH、Daytona、Singularity、Modal。Daytona 和 Modal 提供服务器持久性 — 您的环境在空闲时休眠，几乎不花费任何成本
- **与您同在** — CLI、Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Mattermost、Email、SMS、钉钉、飞书、企业微信、BlueBubbles、Home Assistant — 一个网关支持 15+ 平台
- **由模型训练师构建** — 由 [Nous Research](https://nousresearch.com) 创建，该实验室是 Hermes、Nomos 和 Psyche 的背后团队。可与 [Nous Portal](https://portal.nousresearch.com)、[OpenRouter](https://openrouter.ai)、OpenAI 或任何端点配合使用
- **定时自动化** — 内置 cron，可交付到任何平台
- **委托和并行化** — 生成隔离的子智能体用于并行工作流。通过 `execute_code` 的程序化工具调用将多步骤管道压缩为单次推理调用
- **开放标准技能** — 兼容 [agentskills.io](https://agentskills.io)。技能是可移植、可共享的，并通过技能中心由社区贡献
- **完整的网络控制** — 搜索、提取、浏览、视觉、图像生成、TTS
- **MCP 支持** — 连接到任何 MCP 服务器以扩展工具能力
- **研究就绪** — 批处理、轨迹导出、使用 Atropos 的 RL 训练。由 [Nous Research](https://nousresearch.com) 构建 — 该实验室是 Hermes、Nomos 和 Psyche 模型的背后团队