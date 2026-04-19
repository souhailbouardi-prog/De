---
sidebar_position: 3
title: '学习路径'
description: '根据你的经验水平和目标，选择通过 Hermes Agent 文档的学习路径。'
---

# 学习路径

Hermes Agent 可以做很多事情 —— CLI 助手、Telegram/Discord 机器人、任务自动化、RL 训练等等。此页面帮助你根据你的经验水平和你想要完成的任务，弄清楚从哪里开始以及阅读什么。

:::tip 从这里开始
如果你还没有安装 Hermes Agent，请从 [安装指南](/docs/getting-started/installation) 开始，然后运行 [快速入门](/docs/getting-started/quickstart)。下面的所有内容都假设你有一个可用的安装。
:::

## 如何使用此页面

- **知道你的水平？** 跳转到 [按经验级别表格](#按经验级别) 并遵循你的级别的阅读顺序。
- **有特定目标？** 跳转到 [按用例](#按用例) 并找到匹配的场景。
- **只是浏览？** 查看 [主要功能概览](#主要功能概览) 表格，快速了解 Hermes Agent 可以做的所有事情。

## 按经验级别

| 级别 | 目标 | 推荐阅读 | 时间估计 |
|---|---|---|---|
| **初学者** | 启动并运行，进行基本对话，使用内置工具 | [安装](/docs/getting-started/installation) → [快速入门](/docs/getting-started/quickstart) → [CLI 使用](/docs/user-guide/cli) → [配置](/docs/user-guide/configuration) | ~1 小时 |
| **中级** | 设置消息机器人，使用高级功能，如记忆、定时任务和技能 | [会话](/docs/user-guide/sessions) → [消息](/docs/user-guide/messaging) → [工具](/docs/user-guide/features/tools) → [技能](/docs/user-guide/features/skills) → [记忆](/docs/user-guide/features/memory) → [定时任务](/docs/user-guide/features/cron) | ~2–3 小时 |
| **高级** | 构建自定义工具，创建技能，使用 RL 训练模型，为项目做贡献 | [架构](/docs/developer-guide/architecture) → [添加工具](/docs/developer-guide/adding-tools) → [创建技能](/docs/developer-guide/creating-skills) → [RL 训练](/docs/user-guide/features/rl-training) → [贡献](/docs/developer-guide/contributing) | ~4–6 小时 |

## 按用例

选择与你想要做的事情匹配的场景。每个场景都按照你应该阅读的顺序链接到相关文档。

### "我想要一个 CLI 编码助手"

使用 Hermes Agent 作为交互式终端助手来编写、审查和运行代码。

1. [安装](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [CLI 使用](/docs/user-guide/cli)
4. [代码执行](/docs/user-guide/features/code-execution)
5. [上下文文件](/docs/user-guide/features/context-files)
6. [提示与技巧](/docs/guides/tips)

:::tip
使用上下文文件将文件直接传递到你的对话中。Hermes Agent 可以读取、编辑和运行项目中的代码。
:::

### "我想要一个 Telegram/Discord 机器人"

在你喜欢的消息平台上部署 Hermes Agent 作为机器人。

1. [安装](/docs/getting-started/installation)
2. [配置](/docs/user-guide/configuration)
3. [消息概览](/docs/user-guide/messaging)
4. [Telegram 设置](/docs/user-guide/messaging/telegram)
5. [Discord 设置](/docs/user-guide/messaging/discord)
6. [语音模式](/docs/user-guide/features/voice-mode)
7. [在 Hermes 中使用语音模式](/docs/guides/use-voice-mode-with-hermes)
8. [安全](/docs/user-guide/security)

有关完整项目示例，请参阅：
- [每日简报机器人](/docs/guides/daily-briefing-bot)
- [团队 Telegram 助手](/docs/guides/team-telegram-assistant)

### "我想要自动化任务"

安排重复任务，运行批处理作业，或将代理操作链接在一起。

1. [快速入门](/docs/getting-started/quickstart)
2. [定时任务调度](/docs/user-guide/features/cron)
3. [批处理](/docs/user-guide/features/batch-processing)
4. [委托](/docs/user-guide/features/delegation)
5. [钩子](/docs/user-guide/features/hooks)

:::tip
定时任务让 Hermes Agent 可以按计划运行任务 —— 每日摘要、定期检查、自动化报告 —— 而无需你在场。
:::

### "我想要构建自定义工具/技能"

使用你自己的工具和可重用的技能包扩展 Hermes Agent。

1. [工具概览](/docs/user-guide/features/tools)
2. [技能概览](/docs/user-guide/features/skills)
3. [MCP（模型上下文协议）](/docs/user-guide/features/mcp)
4. [架构](/docs/developer-guide/architecture)
5. [添加工具](/docs/developer-guide/adding-tools)
6. [创建技能](/docs/developer-guide/creating-skills)

:::tip
工具是代理可以调用的单个函数。技能是打包在一起的工具、提示和配置包。从工具开始，然后升级到技能。
:::

### "我想要训练模型"

使用强化学习通过 Hermes Agent 的内置 RL 训练管道微调模型行为。

1. [快速入门](/docs/getting-started/quickstart)
2. [配置](/docs/user-guide/configuration)
3. [RL 训练](/docs/user-guide/features/rl-training)
4. [提供程序路由](/docs/user-guide/features/provider-routing)
5. [架构](/docs/developer-guide/architecture)

:::tip
当你已经了解 Hermes Agent 如何处理对话和工具调用的基础知识时，RL 训练效果最好。如果你是新手，请先运行初学者路径。
:::

### "我想要将其用作 Python 库"

以编程方式将 Hermes Agent 集成到你自己的 Python 应用程序中。

1. [安装](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [Python 库指南](/docs/guides/python-library)
4. [架构](/docs/developer-guide/architecture)
5. [工具](/docs/user-guide/features/tools)
6. [会话](/docs/user-guide/sessions)

## 主要功能概览

不确定有哪些可用？这里是主要功能的快速目录：

| 功能 | 它做什么 | 链接 |
|---|---|---|
| **工具** | 代理可以调用的内置工具（文件 I/O、搜索、shell 等） | [工具](/docs/user-guide/features/tools) |
| **技能** | 添加新功能的可安装插件包 | [技能](/docs/user-guide/features/skills) |
| **记忆** | 跨会话的持久记忆 | [记忆](/docs/user-guide/features/memory) |
| **上下文文件** | 将文件和目录馈送到对话中 | [上下文文件](/docs/user-guide/features/context-files) |
| **MCP** | 通过模型上下文协议连接到外部工具服务器 | [MCP](/docs/user-guide/features/mcp) |
| **定时任务** | 安排重复的代理任务 | [定时任务](/docs/user-guide/features/cron) |
| **委托** | 生成子代理以进行并行工作 | [委托](/docs/user-guide/features/delegation) |
| **代码执行** | 在沙箱环境中运行代码 | [代码执行](/docs/user-guide/features/code-execution) |
| **浏览器** | Web 浏览和抓取 | [浏览器](/docs/user-guide/features/browser) |
| **钩子** | 事件驱动的回调和中间件 | [钩子](/docs/user-guide/features/hooks) |
| **批处理** | 批量处理多个输入 | [批处理](/docs/user-guide/features/batch-processing) |
| **RL 训练** | 使用强化学习微调模型 | [RL 训练](/docs/user-guide/features/rl-training) |
| **提供程序路由** | 跨多个 LLM 提供程序路由请求 | [提供程序路由](/docs/user-guide/features/provider-routing) |

## 接下来读什么

根据你现在的位置：

- **刚完成安装？** → 前往 [快速入门](/docs/getting-started/quickstart) 运行你的第一次对话。
- **完成了快速入门？** → 阅读 [CLI 使用](/docs/user-guide/cli) 和 [配置](/docs/user-guide/configuration) 以自定义你的设置。
- **熟悉基础知识？** → 探索 [工具](/docs/user-guide/features/tools)、[技能](/docs/user-guide/features/skills) 和 [记忆](/docs/user-guide/features/memory) 以解锁代理的全部功能。
- **为团队设置？** → 阅读 [安全](/docs/user-guide/security) 和 [会话](/docs/user-guide/sessions) 以了解访问控制和对话管理。
- **准备好构建了？** → 跳转到 [开发者指南](/docs/developer-guide/architecture) 以了解内部结构并开始贡献。
- **想要实际示例？** → 查看 [指南](/docs/guides/tips) 部分以获取真实世界的项目和提示。

:::tip
你不需要阅读所有内容。选择与你的目标匹配的路径，按顺序跟随链接，你会很快就有生产力。你可以随时回到此页面找到你的下一步。
:::
