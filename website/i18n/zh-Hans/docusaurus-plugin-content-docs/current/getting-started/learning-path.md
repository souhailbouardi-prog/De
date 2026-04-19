---
sidebar_position: 3
title: '学习路径'
description: '根据您的经验水平和目标选择 Hermes Agent 文档的学习路径。'
---

# 学习路径

Hermes Agent 可以做很多事情 — CLI 助手、Telegram/Discord 机器人、任务自动化、RL 训练等等。本页面帮助您根据经验水平和想要实现的目标来确定从哪里开始以及阅读什么内容。

:::tip 从这里开始
如果您还没有安装 Hermes Agent，请从[安装指南](/docs/getting-started/installation)开始，然后运行[快速入门](/docs/getting-started/quickstart)。下面的所有内容都假设您有一个正常工作的安装。
:::

## 如何使用本页面

- **知道您的水平？** 跳转到[经验水平表格](#按经验水平)并按照您所在层级的阅读顺序。
- **有特定目标？** 跳到[按使用场景](#按使用场景)并找到匹配的场景。
- **只是浏览？** 查看[关键功能概览](#关键功能概览)表格，快速了解 Hermes Agent 的所有功能。

## 按经验水平

| 水平 | 目标 | 推荐阅读 | 时间估计 |
|---|---|---|---|
| **初学者** | 启动并运行，进行基本对话，使用内置工具 | [安装](/docs/getting-started/installation) → [快速入门](/docs/getting-started/quickstart) → [CLI 使用](/docs/user-guide/cli) → [配置](/docs/user-guide/configuration) | ~1 小时 |
| **中级** | 设置消息机器人，使用高级功能如记忆、cron 作业和技能 | [会话](/docs/user-guide/sessions) → [消息传递](/docs/user-guide/messaging) → [工具](/docs/user-guide/features/tools) → [技能](/docs/user-guide/features/skills) → [记忆](/docs/user-guide/features/memory) → [Cron](/docs/user-guide/features/cron) | ~2–3 小时 |
| **高级** | 构建自定义工具，创建技能，使用 RL 训练模型，为项目做贡献 | [架构](/docs/developer-guide/architecture) → [添加工具](/docs/developer-guide/adding-tools) → [创建技能](/docs/developer-guide/creating-skills) → [RL 训练](/docs/user-guide/features/rl-training) → [贡献](/docs/developer-guide/contributing) | ~4–6 小时 |

## 按使用场景

选择与您想要做的事情匹配的场景。每个场景都按照您应该阅读的顺序链接到相关文档。

### "我想要一个 CLI 编码助手"

使用 Hermes Agent 作为交互式终端助手来编写、审查和运行代码。

1. [安装](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [CLI 使用](/docs/user-guide/cli)
4. [代码执行](/docs/user-guide/features/code-execution)
5. [上下文文件](/docs/user-guide/features/context-files)
6. [技巧与窍门](/docs/guides/tips)

:::tip
通过上下文文件将文件直接传递到您的对话中。Hermes Agent 可以读取、编辑和运行您项目中的代码。
:::

### "我想要一个 Telegram/Discord 机器人"

在您喜欢的消息平台上部署 Hermes Agent 作为机器人。

1. [Installation](/docs/getting-started/installation)
2. [Configuration](/docs/user-guide/configuration)
3. [Messaging Overview](/docs/user-guide/messaging)
4. [Telegram Setup](/docs/user-guide/messaging/telegram)
5. [Discord Setup](/docs/user-guide/messaging/discord)
6. [Voice Mode](/docs/user-guide/features/voice-mode)
7. [Use Voice Mode with Hermes](/docs/guides/use-voice-mode-with-hermes)
8. [Security](/docs/user-guide/security)

For full project examples, see:
- [Daily Briefing Bot](/docs/guides/daily-briefing-bot)
- [Team Telegram Assistant](/docs/guides/team-telegram-assistant)

### "I want to automate tasks"

Schedule recurring tasks, run batch jobs, or chain agent actions together.

1. [Quickstart](/docs/getting-started/quickstart)
2. [Cron Scheduling](/docs/user-guide/features/cron)
3. [Batch Processing](/docs/user-guide/features/batch-processing)
4. [Delegation](/docs/user-guide/features/delegation)
5. [Hooks](/docs/user-guide/features/hooks)

:::tip
Cron jobs let Hermes Agent run tasks on a schedule — daily summaries, periodic checks, automated reports — without you being present.
:::

### "I want to build custom tools/skills"

Extend Hermes Agent with your own tools and reusable skill packages.

1. [Tools Overview](/docs/user-guide/features/tools)
2. [Skills Overview](/docs/user-guide/features/skills)
3. [MCP (Model Context Protocol)](/docs/user-guide/features/mcp)
4. [Architecture](/docs/developer-guide/architecture)
5. [Adding Tools](/docs/developer-guide/adding-tools)
6. [Creating Skills](/docs/developer-guide/creating-skills)

:::tip
Tools are individual functions the agent can call. Skills are bundles of tools, prompts, and configuration packaged together. Start with tools, graduate to skills.
:::

### "I want to train models"

Use reinforcement learning to fine-tune model behavior with Hermes Agent's built-in RL training pipeline.

1. [Quickstart](/docs/getting-started/quickstart)
2. [Configuration](/docs/user-guide/configuration)
3. [RL Training](/docs/user-guide/features/rl-training)
4. [Provider Routing](/docs/user-guide/features/provider-routing)
5. [Architecture](/docs/developer-guide/architecture)

:::tip
RL training works best when you already understand the basics of how Hermes Agent handles conversations and tool calls. Run through the Beginner path first if you're new.
:::

### "I want to use it as a Python library"

Integrate Hermes Agent into your own Python applications programmatically.

1. [Installation](/docs/getting-started/installation)
2. [Quickstart](/docs/getting-started/quickstart)
3. [Python Library Guide](/docs/guides/python-library)
4. [Architecture](/docs/developer-guide/architecture)
5. [Tools](/docs/user-guide/features/tools)
6. [Sessions](/docs/user-guide/sessions)

## Key Features at a Glance

Not sure what's available? Here's a quick directory of major features:

| Feature | What It Does | Link |
|---|---|---|
| **Tools** | Built-in tools the agent can call (file I/O, search, shell, etc.) | [Tools](/docs/user-guide/features/tools) |
| **Skills** | Installable plugin packages that add new capabilities | [Skills](/docs/user-guide/features/skills) |
| **Memory** | Persistent memory across sessions | [Memory](/docs/user-guide/features/memory) |
| **Context Files** | Feed files and directories into conversations | [Context Files](/docs/user-guide/features/context-files) |
| **MCP** | Connect to external tool servers via Model Context Protocol | [MCP](/docs/user-guide/features/mcp) |
| **Cron** | Schedule recurring agent tasks | [Cron](/docs/user-guide/features/cron) |
| **Delegation** | Spawn sub-agents for parallel work | [Delegation](/docs/user-guide/features/delegation) |
| **Code Execution** | Run code in sandboxed environments | [Code Execution](/docs/user-guide/features/code-execution) |
| **Browser** | Web browsing and scraping | [Browser](/docs/user-guide/features/browser) |
| **Hooks** | Event-driven callbacks and middleware | [Hooks](/docs/user-guide/features/hooks) |
| **Batch Processing** | Process multiple inputs in bulk | [Batch Processing](/docs/user-guide/features/batch-processing) |
| **RL Training** | Fine-tune models with reinforcement learning | [RL Training](/docs/user-guide/features/rl-training) |
| **Provider Routing** | Route requests across multiple LLM providers | [Provider Routing](/docs/user-guide/features/provider-routing) |

## What to Read Next

Based on where you are right now:

- **Just finished installing?** → Head to the [Quickstart](/docs/getting-started/quickstart) to run your first conversation.
- **Completed the Quickstart?** → Read [CLI Usage](/docs/user-guide/cli) and [Configuration](/docs/user-guide/configuration) to customize your setup.
- **Comfortable with the basics?** → Explore [Tools](/docs/user-guide/features/tools), [Skills](/docs/user-guide/features/skills), and [Memory](/docs/user-guide/features/memory) to unlock the full power of the agent.
- **Setting up for a team?** → Read [Security](/docs/user-guide/security) and [Sessions](/docs/user-guide/sessions) to understand access control and conversation management.
- **Ready to build?** → Jump into the [Developer Guide](/docs/developer-guide/architecture) to understand the internals and start contributing.
- **Want practical examples?** → Check out the [Guides](/docs/guides/tips) section for real-world projects and tips.

:::tip
You don't need to read everything. Pick the path that matches your goal, follow the links in order, and you'll be productive quickly. You can always come back to this page to find your next step.
:::