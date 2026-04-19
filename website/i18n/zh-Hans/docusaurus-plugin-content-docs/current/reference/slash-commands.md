---
sidebar_position: 2
title: "斜杠命令参考"
description: "交互式 CLI 和消息斜杠命令的完整参考"
---

# 斜杠命令参考

Hermes 有两个斜杠命令界面，都由 `hermes_cli/commands.py` 中的中央 `COMMAND_REGISTRY` 驱动：

- **交互式 CLI 斜杠命令** — 由 `cli.py` 分发，具有来自注册表的自动完成功能
- **消息斜杠命令** — 由 `gateway/run.py` 分发，具有从注册表生成的帮助文本和平台菜单

已安装的技能也作为动态斜杠命令暴露在两个界面上。这包括捆绑技能，如 `/plan`，它打开计划模式并将 markdown 计划保存在相对于活动工作区/后端工作目录的 `.hermes/plans/` 下。

## 交互式 CLI 斜杠命令

在 CLI 中输入 `/` 打开自动完成菜单。内置命令不区分大小写。

### 会话

| 命令 | 描述 |
|---------|-------------|
| `/new` (别名: `/reset`) | 开始新会话（新的会话 ID + 历史记录） |
| `/clear` | 清除屏幕并开始新会话 |
| `/history` | 显示对话历史 |
| `/save` | 保存当前对话 |
| `/retry` | 重试最后一条消息（重新发送给智能体） |
| `/undo` | 删除最后一个用户/助手交换 |
| `/title` | 为当前会话设置标题（用法：/title 我的会话名称） |
| `/compress [focus topic]` | 手动压缩对话上下文（刷新记忆 + 摘要）。可选焦点主题缩小摘要保留的内容。 |
| `/rollback` | 列出或恢复文件系统检查点（用法：/rollback [number]） |
| `/snapshot [create\|restore &lt;id&gt;\|prune]` (别名: `/snap`) | 创建或恢复 Hermes 配置/状态的状态快照。`create [label]` 保存快照，`restore &lt;id&gt;` 恢复到它，`prune [N]` 删除旧快照，或无参数列出所有快照。 |
| `/stop` | 终止所有正在运行的后台进程 |
| `/queue &lt;prompt&gt;` (别名: `/q`) | 为下一轮排队提示（不中断当前智能体响应）。**注意：** `/q` 被 `/queue` 和 `/quit` 同时声明；最后注册的获胜，因此 `/q` 在实践中解析为 `/quit`。请明确使用 `/queue`。 |
| `/resume [name]` | 恢复先前命名的会话 |
| `/status` | 显示会话信息 |
| `/snapshot` (别名: `/snap`) | 创建或恢复 Hermes 配置/状态的状态快照（用法：/snapshot [create\|restore &lt;id&gt;\|prune]） |
| `/background &lt;prompt&gt;` (别名: `/bg`) | 在单独的后台会话中运行提示。智能体独立处理您的提示 — 您的当前会话保持空闲用于其他工作。任务完成时结果显示为面板。参见 [CLI 后台会话](/docs/user-guide/cli#background-sessions)。 |
| `/btw &lt;question&gt;` | 使用会话上下文进行临时旁问题（无工具，不持久化）。用于快速澄清而不影响对话历史。 |
| `/plan [request]` | 加载捆绑的 `plan` 技能以编写 markdown 计划而不是执行工作。计划保存在相对于活动工作区/后端工作目录的 `.hermes/plans/` 下。 |
| `/branch [name]` (别名: `/fork`) | 分支当前会话（探索不同路径） |

### 配置

| 命令 | 描述 |
|---------|-------------|
| `/config` | 显示当前配置 |
| `/model [model-name]` | 显示或更改当前模型。支持：`/model claude-sonnet-4`，`/model provider:model`（切换提供商），`/model custom:model`（自定义端点），`/model custom:name:model`（命名自定义提供商），`/model custom`（从端点自动检测）。使用 `--global` 将更改持久化到 config.yaml。 |
| `/provider` | 显示可用提供商和当前提供商 |
| `/personality` | 设置预定义个性 |
| `/verbose` | 循环工具进度显示：关闭 → 新 → 所有 → 详细。可以通过配置为[消息启用](#notes)。 |
| `/fast` | 切换快速模式 — OpenAI 优先级处理 / Anthropic 快速模式（用法：/fast [normal\|fast\|status]） |
| `/reasoning` | 管理推理努力和显示（用法：/reasoning [level\|show\|hide]） |
| `/fast [normal\|fast\|status]` | 切换快速模式 — OpenAI 优先级处理 / Anthropic 快速模式。选项：`normal`，`fast`，`status`，`on`，`off`。 |
| `/skin` | 显示或更改显示皮肤/主题 |
| `/statusbar` (别名: `/sb`) | 切换上下文/模型状态栏的开关 |
| `/voice [on\|off\|tts\|status]` | 切换 CLI 语音模式和语音播放。录音使用 `voice.record_key`（默认：`Ctrl+B`）。 |
| `/yolo` | 切换 YOLO 模式 — 跳过所有危险命令批准提示。 |

### 工具与技能

| 命令 | 描述 |
|---------|-------------|
| `/tools [list\|disable\|enable] [name...]` | 管理工具：列出可用工具，或为当前会话禁用/启用特定工具。禁用工具会将其从智能体的工具集中移除并触发会话重置。 |
| `/toolsets` | 列出可用工具集 |
| `/browser [connect\|disconnect\|status]` | 管理本地 Chrome CDP 连接。`connect` 将浏览器工具附加到正在运行的 Chrome 实例（默认：`ws://localhost:9222`）。`disconnect` 分离。`status` 显示当前连接。如果未检测到调试器，则自动启动 Chrome。 |
| `/skills` | 从在线注册表搜索、安装、检查或管理技能 |
| `/cron` | 管理计划任务（列出、添加/创建、编辑、暂停、恢复、运行、删除） |
| `/reload-mcp` (别名: `/reload_mcp`) | 从 config.yaml 重新加载 MCP 服务器 |
| `/reload` | 重新加载 `.env` 变量到运行中的会话（获取新的 API 密钥而无需重启） |
| `/plugins` | 列出已安装的插件及其状态 |

### 信息

| 命令 | 描述 |
|---------|-------------|
| `/help` | 显示此帮助消息 |
| `/usage` | 显示令牌使用情况、成本细分和会话持续时间 |
| `/insights` | 显示使用洞察和分析（最近 30 天） |
| `/platforms` (别名: `/gateway`) | 显示网关/消息平台状态 |
| `/paste` | 检查剪贴板中的图像并附加它 |
| `/image <path>` | 为您的下一个提示附加本地图像文件。 |
| `/debug` | 上传调试报告（系统信息 + 日志）并获取可共享链接。在消息中也可用。 |
| `/profile` | 显示活动配置文件名称和主目录 |

### 退出

| 命令 | 描述 |
|---------|-------------|
| `/quit` | 退出 CLI（也可用：`/exit`）。请参阅上面 `/queue` 下的 `/q` 说明。 |

### 动态 CLI 斜杠命令

| 命令 | 描述 |
|---------|-------------|
| `/<skill-name>` | 将任何已安装的技能加载为按需命令。示例：`/gif-search`，`/github-pr-workflow`，`/excalidraw`。 |
| `/skills ...` | 从注册表和官方可选技能目录中搜索、浏览、检查、安装、审计、发布和配置技能。 |

### 快速命令

用户定义的快速命令将短别名映射到更长的提示。在 `~/.hermes/config.yaml` 中配置它们：

```yaml
quick_commands:
  review: "Review my latest git diff and suggest improvements"
  deploy: "Run the deployment script at scripts/deploy.sh and verify the output"
  morning: "Check my calendar, unread emails, and summarize today's priorities"
```

然后在 CLI 中键入 `/review`、`/deploy` 或 `/morning`。快速命令在调度时解析，不会显示在内置的自动完成/帮助表中。

### 别名解析

命令支持前缀匹配：键入 `/h` 解析为 `/help`，`/mod` 解析为 `/model`。当前缀不明确（匹配多个命令）时，注册表顺序中的第一个匹配项获胜。完整命令名称和注册的别名始终优先于前缀匹配。

## 消息斜杠命令

消息网关在 Telegram、Discord、Slack、WhatsApp、Signal、Email 和 Home Assistant 聊天中支持以下内置命令：

| 命令 | 描述 |
|---------|-------------|
| `/new` | 开始新对话。 |
| `/reset` | 重置对话历史。 |
| `/status` | 显示会话信息。 |
| `/stop` | 终止所有正在运行的后台进程并中断运行中的智能体。 |
| `/model [provider:model]` | 显示或更改模型。支持提供商切换（`/model zai:glm-5`）、自定义端点（`/model custom:model`）、命名自定义提供商（`/model custom:local:qwen`）和自动检测（`/model custom`）。使用 `--global` 将更改持久化到 config.yaml。 |
| `/provider` | 显示提供商可用性和身份验证状态。 |
| `/personality [name]` | 为会话设置个性覆盖。 |
| `/fast [normal\|fast\|status]` | 切换快速模式 — OpenAI 优先级处理 / Anthropic 快速模式。 |
| `/retry` | 重试最后一条消息。 |
| `/undo` | 删除最后一个交换。 |
| `/sethome` (别名: `/set-home`) | 将当前聊天标记为交付的平台主频道。 |
| `/compress [focus topic]` | 手动压缩对话上下文。可选焦点主题缩小摘要保留的内容。 |
| `/title [name]` | 设置或显示会话标题。 |
| `/resume [name]` | 恢复先前命名的会话。 |
| `/usage` | 显示令牌使用情况、估计成本细分（输入/输出）、上下文窗口状态和会话持续时间。 |
| `/insights [days]` | 显示使用分析。 |
| `/reasoning [level\|show\|hide]` | 更改推理努力或切换推理显示。 |
| `/voice [on\|off\|tts\|join\|channel\|leave\|status]` | 控制聊天中的语音回复。`join`/`channel`/`leave` 管理 Discord 语音频道模式。 |
| `/rollback [number]` | 列出或恢复文件系统检查点。 |
| `/snapshot [create\|restore <id>\|prune]` (别名: `/snap`) | 创建或恢复 Hermes 配置/状态的状态快照。 |
| `/background <prompt>` | 在单独的后台会话中运行提示。任务完成时结果将传递回同一聊天。参见 [消息后台会话](/docs/user-guide/messaging/#background-sessions)。 |
| `/plan [request]` | 加载捆绑的 `plan` 技能以编写 markdown 计划而不是执行工作。计划保存在相对于活动工作区/后端工作目录的 `.hermes/plans/` 下。 |
| `/reload-mcp` (别名: `/reload_mcp`) | 从配置重新加载 MCP 服务器。 |
| `/reload` | 将 `.env` 变量重新加载到运行中的会话。 |
| `/yolo` | 切换 YOLO 模式 — 跳过所有危险命令批准提示。 |
| `/commands [page]` | 浏览所有命令和技能（分页）。 |
| `/approve [session\|always]` | 批准并执行待处理的危险命令。`session` 仅为此会话批准；`always` 添加到永久允许列表。 |
| `/deny` | 拒绝待处理的危险命令。 |
| `/update` | 将 Hermes Agent 更新到最新版本。 |
| `/restart` | 在排空活动运行后优雅地重启网关。当网关重新上线时，它会向请求者的聊天/线程发送确认。 |
| `/fast [normal\|fast\|status]` | 切换快速模式 — OpenAI 优先级处理 / Anthropic 快速模式。 |
| `/debug` | 上传调试报告（系统信息 + 日志）并获取可共享链接。 |
| `/debug` | 上传调试报告（系统信息 + 日志）并获取可共享链接。 |
| `/help` | 显示消息帮助。 |
| `/<skill-name>` | 按名称调用任何已安装的技能。 |

## 注意事项

- `/skin`、`/tools`、`/toolsets`、`/browser`、`/config`、`/cron`、`/skills`、`/platforms`、`/paste`、`/image`、`/statusbar` 和 `/plugins` 是**仅 CLI** 命令。
- `/verbose` 默认是**仅 CLI**，但可以通过在 `config.yaml` 中设置 `display.tool_progress_command: true` 为消息平台启用。启用后，它会循环 `display.tool_progress` 模式并保存到配置。
- `/sethome`、`/update`、`/restart`、`/approve`、`/deny` 和 `/commands` 是**仅消息**命令。
- `/status`、`/background`、`/voice`、`/reload-mcp`、`/rollback`、`/snapshot`、`/debug`、`/fast` 和 `/yolo` 在**两者**中都有效：CLI 和消息网关。
- `/voice join`、`/voice channel` 和 `/voice leave` 仅在 Discord 上有意义。