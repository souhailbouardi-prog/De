---
sidebar_position: 3
title: "内置工具参考"
description: "Hermes 内置工具的权威参考，按工具集分组"
---

# 内置工具参考

本页面记录了 Hermes 工具注册表中的所有 47 个内置工具，按工具集分组。可用性因平台、凭据和启用的工具集而异。

**快速计数：** 10 个浏览器工具，4 个文件工具，10 个 RL 工具，4 个 Home Assistant 工具，2 个终端工具，2 个网络工具，以及其他工具集中的 15 个独立工具。

:::tip MCP 工具
除了内置工具外，Hermes 还可以从 MCP 服务器动态加载工具。MCP 工具以服务器名称前缀显示（例如，`github` MCP 服务器的 `github_create_issue`）。有关配置，请参阅 [MCP 集成](/docs/user-guide/features/mcp)。
:::

## `browser` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `browser_back` | 在浏览器历史记录中导航回上一页。需要先调用 browser_navigate。 | — |
| `browser_click` | 点击由快照中的 ref ID 标识的元素（例如 '@e5'）。ref ID 在快照输出的方括号中显示。需要先调用 browser_navigate 和 browser_snapshot。 | — |
| `browser_console` | 获取当前页面的浏览器控制台输出和 JavaScript 错误。返回 console.log/warn/error/info 消息和未捕获的 JS 异常。使用此工具检测静默 JavaScript 错误、失败的 API 调用和应用程序警告。 | — |
| `browser_get_images` | 获取当前页面上所有图像的列表及其 URL 和替代文本。用于查找要使用视觉工具分析的图像。需要先调用 browser_navigate。 | — |
| `browser_navigate` | 在浏览器中导航到 URL。初始化会话并加载页面。必须在其他浏览器工具之前调用。对于简单的信息检索，首选 web_search 或 web_extract（更快、更便宜）。当您需要... 时使用浏览器工具 | — |
| `browser_press` | 按下键盘按键。用于提交表单（Enter）、导航（Tab）或键盘快捷键。需要先调用 browser_navigate。 | — |
| `browser_scroll` | 向某个方向滚动页面。用于显示当前视口下方或上方可能的更多内容。需要先调用 browser_navigate。 | — |
| `browser_snapshot` | 获取当前页面可访问性树的基于文本的快照。返回带有 ref ID（如 @e1、@e2）的交互式元素，用于 browser_click 和 browser_type。full=false（默认）：包含交互式元素的紧凑视图。full=true：完整... | — |
| `browser_type` | 在由其 ref ID 标识的输入字段中键入文本。首先清除字段，然后键入新文本。需要先调用 browser_navigate 和 browser_snapshot。 | — |
| `browser_vision` | 对当前页面进行截图并使用视觉 AI 分析。当您需要视觉理解页面上的内容时使用此工具 - 特别适用于 CAPTCHA、视觉验证挑战、复杂布局，或当文本快照... | — |

## `clarify` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `clarify` | 当您需要在继续之前澄清、反馈或决定时向用户提问。支持两种模式：1. **多项选择** — 提供最多 4 个选项。用户选择一个或通过第 5 个"其他"选项输入自己的答案。2.… | — |

## `code_execution` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `execute_code` | 运行可以以编程方式调用 Hermes 工具的 Python 脚本。当您需要 3+ 个工具调用并在它们之间进行处理逻辑、需要在大型工具输出进入上下文之前过滤/减少它们、需要条件分支（… | — |

## `cronjob` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `cronjob` | 统一的计划任务管理器。使用 `action="create"`、`"list"`、`"update"`、`"pause"`、`"resume"`、`"run"` 或 `"remove"` 来管理作业。支持带有一个或多个附加技能的技能支持作业，`skills=[]` 更新时清除附加技能。Cron 运行在没有当前聊天上下文的新会话中进行。 | — |

## `delegation` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `delegate_task` | 生成一个或多个子智能体在隔离的上下文中处理任务。每个子智能体获得自己的对话、终端会话和工具集。只返回最终摘要 — 中间工具结果永远不会进入您的上下文窗口。两… | — |

## `file` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `patch` | 文件中的定向查找和替换编辑。使用此工具代替终端中的 sed/awk。使用模糊匹配（9 种策略），因此轻微的空白/缩进差异不会破坏它。返回统一差异。编辑后自动运行语法检查… | — |
| `read_file` | 读取带有行号和分页的文本文件。使用此工具代替终端中的 cat/head/tail。输出格式：'LINE_NUM\|CONTENT'。如果未找到，建议类似的文件名。对大文件使用 offset 和 limit。注意：不能读取图像或… | — |
| `search_files` | 搜索文件内容或按名称查找文件。使用此工具代替终端中的 grep/rg/find/ls。基于 Ripgrep，比 shell 等效工具更快。内容搜索（target='content'）：在文件内进行正则表达式搜索。输出模式：带行… | — |
| `write_file` | 将内容写入文件，完全替换现有内容。使用此工具代替终端中的 echo/cat heredoc。自动创建父目录。**覆盖**整个文件 — 对定向编辑使用 'patch'。 | — |

## `homeassistant` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `ha_call_service` | 调用 Home Assistant 服务来控制设备。使用 ha_list_services 发现每个域的可用服务及其参数。 | — |
| `ha_get_state` | 获取单个 Home Assistant 实体的详细状态，包括所有属性（亮度、颜色、温度设定点、传感器读数等）。 | — |
| `ha_list_entities` | 列出 Home Assistant 实体。可选地按域（light、switch、climate、sensor、binary_sensor、cover、fan 等）或区域名称（客厅、厨房、卧室等）过滤。 | — |
| `ha_list_services` | 列出可用的 Home Assistant 服务（操作）用于设备控制。显示可以对每种设备类型执行的操作以及它们接受的参数。使用此工具发现如何控制通过 ha_list_entities 找到的设备。 | — |

:::note
**Honcho 工具**（`honcho_conclude`、`honcho_context`、`honcho_profile`、`honcho_search`）不再是内置的。它们可通过 `plugins/memory/honcho/` 处的 Honcho 内存提供程序插件获得。有关安装和使用，请参阅 [插件](../user-guide/features/plugins.md)。
:::

## `image_gen` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `image_generate` | 使用 FLUX 2 Pro 模型从文本提示生成高质量图像，具有自动 2 倍放大。创建详细、艺术化的图像，自动放大以获得高分辨率结果。返回单个放大的图像 URL。使用… 显示它 | FAL_KEY |

## `memory` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `memory` | 将重要信息保存到跨会话存在的持久内存中。您的内存在会话开始时出现在系统提示中 — 这是您在对话之间记住有关用户和环境的事情的方式。何时保存… | — |

## `messaging` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `send_message` | 向连接的消息传递平台发送消息，或列出可用目标。重要：当用户要求发送到特定频道或人员（不仅仅是裸平台名称）时，**首先**调用 send_message(action='list') 以查看可用目标… | — |

## `moa` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `mixture_of_agents` | 通过多个前沿 LLM 协作路由难题。使用最大推理努力进行 5 次 API 调用（4 个参考模型 + 1 个聚合器）— 仅在真正困难的问题上谨慎使用。最适合：复杂数学、高级算法… | OPENROUTER_API_KEY |
| `mixture_of_agents` | 通过多个前沿 LLM 协作路由难题。使用最大推理努力进行 5 次 API 调用（4 个参考模型 + 1 个聚合器）— 仅在真正困难的问题上谨慎使用。最适合：复杂数学、高级算法… | OPENROUTER_API_KEY |

## `rl` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `rl_check_status` | 获取训练运行的状态和指标。速率限制：对同一运行的检查之间强制 30 分钟最小值。返回 WandB 指标：step、state、reward_mean、loss、percent_correct。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_edit_config` | 更新配置字段。首先使用 rl_get_current_config() 查看所选环境的所有可用字段。每个环境都有不同的可配置选项。基础设施设置（tokenizer、URL、lora_rank、learning_rate… | TINKER_API_KEY, WANDB_API_KEY |
| `rl_get_current_config` | 获取当前环境配置。仅返回可修改的字段：group_size、max_token_length、total_steps、steps_per_eval、use_wandb、wandb_name、max_num_workers。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_get_results` | 获取已完成训练运行的最终结果和指标。返回最终指标和训练权重的路径。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_list_environments` | 列出所有可用的 RL 环境。返回环境名称、路径和描述。提示：使用文件工具读取 file_path 以了解每个环境如何工作（验证器、数据加载、奖励）。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_list_runs` | 列出所有训练运行（活动和已完成）及其状态。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_select_environment` | 选择 RL 环境进行训练。加载环境的默认配置。选择后，使用 rl_get_current_config() 查看设置并使用 rl_edit_config() 修改它们。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_start_training` | 使用当前环境和配置开始新的 RL 训练运行。大多数训练参数（lora_rank、learning_rate 等）是固定的。开始前使用 rl_edit_config() 设置 group_size、batch_size、wandb_project。警告：训练… | TINKER_API_KEY, WANDB_API_KEY |
| `rl_stop_training` | 停止运行中的训练作业。如果指标看起来不好、训练停滞或您想尝试不同的设置，请使用。 | TINKER_API_KEY, WANDB_API_KEY |
| `rl_test_inference` | 任何环境的快速推理测试。使用 OpenRouter 运行几步推理 + 评分。默认：3 步 x 16 个完成 = 每个模型 48 次滚动，测试 3 个模型 = 总计 144 次。测试环境加载、提示构建、in… | TINKER_API_KEY, WANDB_API_KEY |

## `session_search` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `session_search` | 搜索您过去对话的长期记忆。这是您的回忆 — 每个过去的会话都可搜索，此工具总结发生了什么。**主动使用**当：- 用户说'我们以前做过这个'、'记得什么时候'、'上次 ti… | — |

## `skills` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `skill_manage` | 管理技能（创建、更新、删除）。技能是您的程序记忆 — 用于重复任务类型的可重用方法。新技能进入 ~/.hermes/skills/；现有技能可以在它们所在的任何地方修改。操作：create（完整的 SKILL.m… | — |
| `skill_view` | 技能允许加载有关特定任务和工作流程的信息，以及脚本和模板。加载技能的完整内容或访问其链接文件（引用、模板、脚本）。第一次调用返回 SKILL.md 内容加上 a… | — |
| `skills_list` | 列出可用技能（名称 + 描述）。使用 skill_view(name) 加载完整内容。 | — |

## `terminal` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `process` | 管理使用 terminal(background=true) 启动的后台进程。操作：'list'（显示所有）、'poll'（检查状态 + 新输出）、'log'（带分页的完整输出）、'wait'（阻塞直到完成或超时）、'kill'（终止）、'write'（sen… | — |
| `terminal` | 在 Linux 环境上执行 shell 命令。文件系统在调用之间保持。为长时间运行的服务器设置 `background=true`。设置 `notify_on_complete=true`（带 `background=true`）以在进程完成时获得自动通知 — 无需轮询。**不要**使用 cat/head/tail — 使用 read_file。**不要**使用 grep/rg/find — 使用 search_files。 | — |

## `todo` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `todo` | 管理当前会话的任务列表。用于具有 3+ 步骤的复杂任务或当用户提供多个任务时。不带参数调用以读取当前列表。写入：- 提供 'todos' 数组以创建/更新项目 - merge=… | — |

## `vision` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `vision_analyze` | 使用 AI 视觉分析图像。提供全面的描述并回答有关图像内容的特定问题。 | — |

## `web` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `web_search` | 在网络上搜索有关任何主题的信息。返回最多 5 个相关结果，包括标题、URL 和描述。 | EXA_API_KEY 或 PARALLEL_API_KEY 或 FIRECRAWL_API_KEY 或 TAVILY_API_KEY |
| `web_extract` | 从网页 URL 提取内容。以 Markdown 格式返回页面内容。也适用于 PDF URL — 直接传递 PDF 链接，它会转换为 Markdown 文本。5000 字符以下的页面返回完整 Markdown；较大的页面由 LLM 总结。 | EXA_API_KEY 或 PARALLEL_API_KEY 或 FIRECRAWL_API_KEY 或 TAVILY_API_KEY |

## `tts` 工具集

| 工具 | 描述 | 需要环境 |
|------|-------------|----------------------|
| `text_to_speech` | 将文本转换为语音音频。返回平台作为语音消息传递的 MEDIA: 路径。在 Telegram 上以语音气泡形式播放，在 Discord/WhatsApp 上作为音频附件。在 CLI 模式下，保存到 ~/voice-memos/。语音和提供程序… | — |