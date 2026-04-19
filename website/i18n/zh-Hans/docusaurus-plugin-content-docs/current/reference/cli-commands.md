---
sidebar_position: 1
title: "CLI 命令参考"
description: "Hermes 终端命令和命令族的权威参考"
---

# CLI 命令参考

本页面涵盖您从 shell 运行的**终端命令**。

有关聊天中的斜杠命令，请参阅[斜杠命令参考](./slash-commands.md)。

## 全局入口点

```bash
hermes [global-options] <command> [subcommand/options]
```

### 全局选项

| 选项 | 描述 |
|--------|-------------|
| `--version`, `-V` | 显示版本并退出。 |
| `--profile <name>`, `-p <name>` | 选择要用于此调用的 Hermes 配置文件。覆盖由 `hermes profile use` 设置的粘性默认值。 |
| `--resume <session>`, `-r <session>` | 按 ID 或标题恢复之前的会话。 |
| `--continue [name]`, `-c [name]` | 恢复最近的会话，或恢复最近匹配标题的会话。 |
| `--worktree`, `-w` | 在隔离的 git 工作树中启动，用于并行智能体工作流。 |
| `--yolo` | 绕过危险命令批准提示。 |
| `--pass-session-id` | 在智能体的系统提示中包含会话 ID。 |

## 顶级命令

| 命令 | 用途 |
|---------|---------|
| `hermes chat` | 与智能体进行交互式或一次性聊天。 |
| `hermes model` | 交互式选择默认提供商和模型。 |
| `hermes gateway` | 运行或管理消息网关服务。 |
| `hermes setup` | 所有或部分配置的交互式设置向导。 |
| `hermes whatsapp` | 配置和配对 WhatsApp 桥接。 |
| `hermes auth` | 管理凭据 — 添加、列出、删除、重置、设置策略。处理 Codex/Nous/Anthropic 的 OAuth 流程。 |
| `hermes login` / `logout` | **已弃用** — 改用 `hermes auth`。 |
| `hermes status` | 显示智能体、认证和平台状态。 |
| `hermes cron` | 检查并触发 cron 调度器。 |
| `hermes webhook` | 管理动态 webhook 订阅以进行事件驱动激活。 |
| `hermes doctor` | 诊断配置和依赖问题。 |
| `hermes dump` | 用于支持/调试的可复制粘贴设置摘要。 |
| `hermes debug` | 调试工具 — 上传日志和系统信息以支持。 |
| `hermes backup` | 将 Hermes 主目录备份到 zip 文件。 |
| `hermes import` | 从 zip 文件恢复 Hermes 备份。 |
| `hermes logs` | 查看、跟踪和过滤智能体/网关/错误日志文件。 |
| `hermes config` | 显示、编辑、迁移和查询配置文件。 |
| `hermes pairing` | 批准或撤销消息配对代码。 |
| `hermes skills` | 浏览、安装、发布、审计和配置技能。 |
| `hermes honcho` | 管理 Honcho 跨会话内存集成。 |
| `hermes memory` | 配置外部内存提供商。 |
| `hermes acp` | 运行 Hermes 作为 ACP 服务器进行编辑器集成。 |
| `hermes mcp` | 管理 MCP 服务器配置并运行 Hermes 作为 MCP 服务器。 |
| `hermes plugins` | 管理 Hermes Agent 插件（安装、启用、禁用、删除）。 |
| `hermes tools` | 按平台配置启用的工具。 |
| `hermes sessions` | 浏览、导出、修剪、重命名和删除会话。 |
| `hermes insights` | 显示令牌/成本/活动分析。 |
| `hermes claw` | OpenClaw 迁移助手。 |
| `hermes dashboard` | 启动 Web 仪表板，用于管理配置、API 密钥和会话。 |
| `hermes debug` | 调试工具 — 上传日志和系统信息以支持。 |
| `hermes backup` | 将 Hermes 主目录备份到 zip 文件。 |
| `hermes import` | 从 zip 文件恢复 Hermes 备份。 |
| `hermes profile` | 管理配置文件 — 多个隔离的 Hermes 实例。 |
| `hermes completion` | 打印 shell 补全脚本 (bash/zsh)。 |
| `hermes version` | 显示版本信息。 |
| `hermes update` | 拉取最新代码并重新安装依赖项。 |
| `hermes uninstall` | 从系统中移除 Hermes。 |

## `hermes chat`

```bash
hermes chat [options]
```

常用选项：

| 选项 | 描述 |
|--------|-------------|
| `-q`, `--query "..."` | 一次性、非交互式提示。 |
| `-m`, `--model <model>` | 覆盖此运行的模型。 |
| `-t`, `--toolsets <csv>` | 启用逗号分隔的工具集。 |
| `--provider <provider>` | 强制提供商：`auto`、`openrouter`、`nous`、`openai-codex`、`copilot-acp`、`copilot`、`anthropic`、`gemini`、`huggingface`、`zai`、`kimi-coding`、`minimax`、`minimax-cn`、`kilocode`、`xiaomi`、`arcee`。 |
| `-s`, `--skills <name>` | 为会话预加载一个或多个技能（可重复或逗号分隔）。 |
| `-v`, `--verbose` | 详细输出。 |
| `-Q`, `--quiet` | 编程模式：抑制横幅/旋转器/工具预览。 |
| `--image <path>` | 将本地图像附加到单个查询。 |
| `--resume <session>` / `--continue [name]` | 直接从 `chat` 恢复会话。 |
| `--worktree` | 为此运行创建隔离的 git 工作树。 |
| `--checkpoints` | 在破坏性文件更改之前启用文件系统检查点。 |
| `--yolo` | 跳过批准提示。 |
| `--pass-session-id` | 将会话 ID 传递到系统提示中。 |
| `--source <tag>` | 用于过滤的会话源标签（默认：`cli`）。对不应出现在用户会话列表中的第三方集成使用 `tool`。 |
| `--max-turns <N>` | 每个对话轮次的最大工具调用迭代次数（默认：90，或配置中的 `agent.max_turns`）。 |

示例：

```bash
hermes
hermes chat -q "Summarize the latest PRs"
hermes chat --provider openrouter --model anthropic/claude-sonnet-4.6
hermes chat --toolsets web,terminal,skills
hermes chat --quiet -q "Return only JSON"
hermes chat --worktree -q "Review this repo and open a PR"
```

## `hermes model`

交互式提供商 + 模型选择器。

```bash
hermes model
```

当您想：
- 切换默认提供商
- 在模型选择期间登录 OAuth 支持的提供商
- 从提供商特定的模型列表中选择
- 配置自定义/自托管端点
- 将新默认值保存到配置中

### 会话中的 `/model` 斜杠命令

无需离开会话即可切换模型：

```
/model                              # 显示当前模型和可用选项
/model claude-sonnet-4              # 切换模型（自动检测提供商）
/model zai:glm-5                    # 切换提供商和模型
/model custom:qwen-2.5              # 在自定义端点上使用模型
/model custom                       # 从自定义端点自动检测模型
/model custom:local:qwen-2.5        # 使用命名的自定义提供商
/model openrouter:anthropic/claude-sonnet-4  # 切换回云
```

提供商和基础 URL 更改会自动持久化到 `config.yaml`。当切换离开自定义端点时，过时的基础 URL 会被清除，以防止泄露到其他提供商。

## `hermes gateway`

```bash
hermes gateway <subcommand>
```

子命令：

| 子命令 | 描述 |
|------------|-------------|
| `run` | 在前台运行网关。推荐用于 WSL、Docker 和 Termux。 |
| `start` | 启动已安装的 systemd/launchd 后台服务。 |
| `stop` | 停止服务（或前台进程）。 |
| `restart` | 重启服务。 |
| `status` | 显示服务状态。 |
| `install` | 安装为 systemd（Linux）或 launchd（macOS）后台服务。 |
| `uninstall` | 删除已安装的服务。 |
| `setup` | 交互式消息平台设置。 |

:::tip WSL 用户
使用 `hermes gateway run` 而不是 `hermes gateway start` — WSL 的 systemd 支持不可靠。将其包装在 tmux 中以保持持久性：`tmux new -s hermes 'hermes gateway run'`。有关详细信息，请参阅 [WSL FAQ](/docs/reference/faq#wsl-gateway-keeps-disconnecting-or-hermes-gateway-start-fails)。
:::

## `hermes setup`

```bash
hermes setup [model|tts|terminal|gateway|tools|agent] [--non-interactive] [--reset]
```

使用完整向导或跳转到一个部分：

| 部分 | 描述 |
|---------|-------------|
| `model` | 提供商和模型设置。 |
| `terminal` | 终端后端和沙箱设置。 |
| `gateway` | 消息平台设置。 |
| `tools` | 按平台启用/禁用工具。 |
| `agent` | 智能体行为设置。 |

选项：

| 选项 | 描述 |
|--------|-------------|
| `--non-interactive` | 使用默认值/环境值而不提示。 |
| `--reset` | 在设置前将配置重置为默认值。 |

## `hermes whatsapp`

```bash
hermes whatsapp
```

运行 WhatsApp 配对/设置流程，包括模式选择和二维码配对。

## `hermes login` / `hermes logout` *(已弃用)*

:::caution
`hermes login` 已被移除。使用 `hermes auth` 管理 OAuth 凭据，`hermes model` 选择提供商，或 `hermes setup` 进行完整的交互式设置。
:::

## `hermes auth`

管理同一提供商密钥轮换的凭据池。有关完整文档，请参阅 [凭据池](/docs/user-guide/features/credential-pools)。

```bash
hermes auth                                              # 交互式向导
hermes auth list                                         # 显示所有池
hermes auth list openrouter                              # 显示特定提供商
hermes auth add openrouter --api-key sk-or-v1-xxx        # 添加 API 密钥
hermes auth add anthropic --type oauth                   # 添加 OAuth 凭据
hermes auth remove openrouter 2                          # 按索引删除
hermes auth reset openrouter                             # 清除冷却
```

子命令：`add`、`list`、`remove`、`reset`。当不带子命令调用时，启动交互式管理向导。

## `hermes status`

```bash
hermes status [--all] [--deep]
```

| 选项 | 描述 |
|--------|-------------|
| `--all` | 以可共享的编辑格式显示所有详细信息。 |
| `--deep` | 运行可能需要更长时间的更深层次检查。 |

## `hermes cron`

```bash
hermes cron <list|create|edit|pause|resume|run|remove|status|tick>
```

| 子命令 | 描述 |
|------------|-------------|
| `list` | 显示计划的作业。 |
| `create` / `add` | 从提示创建计划作业，可选择通过重复的 `--skill` 附加一个或多个技能。 |
| `edit` | 更新作业的调度、提示、名称、交付、重复计数或附加的技能。支持 `--clear-skills`、`--add-skill` 和 `--remove-skill`。 |
| `pause` | 暂停作业而不删除它。 |
| `resume` | 恢复暂停的作业并计算其下一次未来运行。 |
| `run` | 在下次调度器计时时触发作业。 |
| `remove` | 删除计划的作业。 |
| `status` | 检查 cron 调度器是否正在运行。 |
| `tick` | 运行到期的作业一次然后退出。 |

## `hermes webhook`

```bash
hermes webhook <subscribe|list|remove|test>
```

管理用于事件驱动智能体激活的动态 webhook 订阅。需要在配置中启用 webhook 平台 — 如果未配置，将打印设置说明。

| 子命令 | 描述 |
|------------|-------------|
| `subscribe` / `add` | 创建 webhook 路由。返回要在您的服务上配置的 URL 和 HMAC 密钥。 |
| `list` / `ls` | 显示所有智能体创建的订阅。 |
| `remove` / `rm` | 删除动态订阅。来自 config.yaml 的静态路由不受影响。 |
| `test` | 发送测试 POST 以验证订阅是否正常工作。 |

### `hermes webhook subscribe`

```bash
hermes webhook subscribe <name> [options]
```

| 选项 | 描述 |
|--------|-------------|
| `--prompt` | 带有 `{dot.notation}` 有效负载引用的提示模板。 |
| `--events` | 要接受的逗号分隔事件类型（例如 `issues,pull_request`）。空 = 全部。 |
| `--description` | 人类可读的描述。 |
| `--skills` | 为智能体运行加载的逗号分隔技能名称。 |
| `--deliver` | 交付目标：`log`（默认）、`telegram`、`discord`、`slack`、`github_comment`。 |
| `--deliver-chat-id` | 跨平台交付的目标聊天/频道 ID。 |
| `--secret` | 自定义 HMAC 密钥。如果省略则自动生成。 |

订阅持久化到 `~/.hermes/webhook_subscriptions.json`，并由 webhook 适配器热重载，无需重启网关。

## `hermes doctor`

```bash
hermes doctor [--fix]
```

| 选项 | 描述 |
|--------|-------------|
| `--fix` | 尝试在可能的情况下自动修复。 |

## `hermes dump`

```bash
hermes dump [--show-keys]
```

输出您整个 Hermes 设置的紧凑纯文本摘要。设计为在寻求支持时复制粘贴到 Discord、GitHub 问题或 Telegram 中 — 无 ANSI 颜色，无特殊格式，只有数据。

| 选项 | 描述 |
|--------|-------------|
| `--show-keys` | 显示编辑的 API 密钥前缀（前 4 个和后 4 个字符），而不仅仅是 `set`/`not set`。 |

### 包含内容

| 部分 | 详情 |
|---------|---------|
| **标题** | Hermes 版本、发布日期、git 提交哈希 |
| **环境** | OS、Python 版本、OpenAI SDK 版本 |
| **身份** | 活动配置文件名称、HERMES_HOME 路径 |
| **模型** | 配置的默认模型和提供商 |
| **终端** | 后端类型（本地、docker、ssh 等） |
| **API 密钥** | 所有 22 个提供商/工具 API 密钥的存在检查 |
| **功能** | 启用的工具集、MCP 服务器计数、内存提供商 |
| **服务** | 网关状态、配置的消息平台 |
| **工作负载** | Cron 作业计数、已安装技能计数 |
| **配置覆盖** | 与默认值不同的任何配置值 |

### 示例输出

```
--- hermes dump ---
version:          0.8.0 (2026.4.8) [af4abd2f]
os:               Linux 6.14.0-37-generic x86_64
python:           3.11.14
openai_sdk:       2.24.0
profile:          default
hermes_home:      ~/.hermes
model:            anthropic/claude-opus-4.6
provider:         openrouter
terminal:         local

api_keys:
  openrouter           set
  openai               not set
  anthropic            set
  nous                 not set
  firecrawl            set
  ...

features:
  toolsets:           all
  mcp_servers:        0
  memory_provider:    built-in
  gateway:            running (systemd)
  platforms:          telegram, discord
  cron_jobs:          3 active / 5 total
  skills:             42

config_overrides:
  agent.max_turns: 250
  compression.threshold: 0.85
  display.streaming: True
--- end dump ---
```

### 使用时机

- 在 GitHub 上报告 bug — 将转储粘贴到您的问题中
- 在 Discord 中寻求帮助 — 在代码块中分享
- 将您的设置与他人比较
- 当出现问题时进行快速检查

:::tip
`hermes dump` 专门设计用于共享。对于交互式诊断，使用 `hermes doctor`。对于可视化概览，使用 `hermes status`。
:::

## `hermes debug`

```bash
hermes debug share [options]
```

将调试报告（系统信息 + 最近的日志）上传到粘贴服务并获取可共享的 URL。对于快速支持请求很有用 — 包含帮助者诊断您问题所需的一切。

| 选项 | 描述 |
|--------|-------------|
| `--lines <N>` | 每个日志文件包含的日志行数（默认：200）。 |
| `--expire <days>` | 粘贴过期天数（默认：7）。 |
| `--local` | 在本地打印报告而不是上传。 |

报告包括系统信息（OS、Python 版本、Hermes 版本）、最近的智能体和网关日志（每个文件 512 KB 限制），以及编辑的 API 密钥状态。密钥始终被编辑 — 不上传任何秘密。

按顺序尝试的粘贴服务：paste.rs、dpaste.com。

### 示例

```bash
hermes debug share              # 上传调试报告，打印 URL
hermes debug share --lines 500  # 包含更多日志行
hermes debug share --expire 30  # 保留粘贴 30 天
hermes debug share --local      # 打印报告到终端（不上传）
```

## `hermes backup`

```bash
hermes backup [options]
```

创建 Hermes 配置、技能、会话和数据的 zip 存档。备份不包括 hermes-agent 代码库本身。

| 选项 | 描述 |
|--------|-------------|
| `-o`, `--output <path>` | zip 文件的输出路径（默认：`~/hermes-backup-<timestamp>.zip`）。 |
| `-q`, `--quick` | 快速快照：仅关键状态文件（config.yaml、state.db、.env、auth、cron 作业）。比完整备份快得多。 |
| `-l`, `--label <name>` | 快照标签（仅用于 `--quick`）。 |

备份使用 SQLite 的 `backup()` API 进行安全复制，因此即使 Hermes 正在运行（WAL 模式安全），它也能正确工作。

### 示例

```bash
hermes backup                           # 完整备份到 ~/hermes-backup-*.zip
hermes backup -o /tmp/hermes.zip        # 完整备份到特定路径
hermes backup --quick                   # 仅状态快速快照
hermes backup --quick --label "pre-upgrade"  # 带标签的快速快照
```

## `hermes import`

```bash
hermes import <zipfile> [options]
```

将先前创建的 Hermes 备份恢复到您的 Hermes 主目录。

| 选项 | 描述 |
|--------|-------------|
| `-f`, `--force` | 覆盖现有文件而不确认。 |

## `hermes logs`

```bash
hermes logs [log_name] [options]
```

查看、跟踪和过滤 Hermes 日志文件。所有日志都存储在 `~/.hermes/logs/` 中（或非默认配置文件的 `<profile>/logs/` 中）。

### 日志文件

| 名称 | 文件 | 捕获内容 |
|------|------|-----------------|
| `agent` (默认) | `agent.log` | 所有智能体活动 — API 调用、工具调度、会话生命周期（INFO 及以上） |
| `errors` | `errors.log` | 仅警告和错误 — agent.log 的过滤子集 |
| `gateway` | `gateway.log` | 消息网关活动 — 平台连接、消息调度、webhook 事件 |

### 选项

| 选项 | 描述 |
|--------|-------------|
| `log_name` | 要查看的日志：`agent`（默认）、`errors`、`gateway`，或 `list` 显示可用文件及其大小。 |
| `-n`, `--lines <N>` | 要显示的行数（默认：50）。 |
| `-f`, `--follow` | 实时跟踪日志，如 `tail -f`。按 Ctrl+C 停止。 |
| `--level <LEVEL>` | 要显示的最低日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`。 |
| `--session <ID>` | 过滤包含会话 ID 子字符串的行。 |
| `--since <TIME>` | 显示从相对时间前的行：`30m`、`1h`、`2d` 等。支持 `s`（秒）、`m`（分钟）、`h`（小时）、`d`（天）。 |
| `--component <NAME>` | 按组件过滤：`gateway`、`agent`、`tools`、`cli`、`cron`。 |

### 示例

```bash
# 查看 agent.log 的最后 50 行（默认）
hermes logs

# 实时跟踪 agent.log
hermes logs -f

# 查看 gateway.log 的最后 100 行
hermes logs gateway -n 100

# 显示过去 1 小时的警告和错误
hermes logs --level WARNING --since 1h

# 按特定会话过滤
hermes logs --session abc123

# 跟踪 errors.log，从 30 分钟前开始
hermes logs errors --since 30m -f

# 列出所有日志文件及其大小
hermes logs list
```

### 过滤

过滤器可以组合。当多个过滤器处于活动状态时，日志行必须**全部**通过才能显示：

```bash
# 过去 2 小时内包含会话 "tg-12345" 的 WARNING+ 行
hermes logs --level WARNING --since 2h --session tg-12345
```

当 `--since` 活动时，包含没有可解析时间戳的行（它们可能是多行日志条目的续行）。当 `--level` 活动时，包含没有可检测级别的行。

### 日志轮换

Hermes 使用 Python 的 `RotatingFileHandler`。旧日志会自动轮换 — 查找 `agent.log.1`、`agent.log.2` 等。`hermes logs list` 子命令显示所有日志文件，包括轮换的文件。

## `hermes config`

```bash
hermes config <subcommand>
```

子命令：

| 子命令 | 描述 |
|------------|-------------|
| `show` | 显示当前配置值。 |
| `edit` | 在编辑器中打开 `config.yaml`。 |
| `set <key> <value>` | 设置配置值。 |
| `path` | 打印配置文件路径。 |
| `env-path` | 打印 `.env` 文件路径。 |
| `check` | 检查缺失或过时的配置。 |
| `migrate` | 交互式添加新引入的选项。 |

## `hermes pairing`

```bash
hermes pairing <list|approve|revoke|clear-pending>
```

| 子命令 | 描述 |
|------------|-------------|
| `list` | 显示待处理和已批准的用户。 |
| `approve <platform> <code>` | 批准配对代码。 |
| `revoke <platform> <user-id>` | 撤销用户的访问权限。 |
| `clear-pending` | 清除待处理的配对代码。 |

## `hermes skills`

```bash
hermes skills <subcommand>
```

子命令：

| 子命令 | 描述 |
|------------|-------------|
| `browse` | 技能注册表的分页浏览器。 |
| `search` | 搜索技能注册表。 |
| `install` | 安装技能。 |
| `inspect` | 在不安装的情况下预览技能。 |
| `list` | 列出已安装的技能。 |
| `check` | 检查已安装的 hub 技能是否有上游更新。 |
| `update` | 当可用时，重新安装带有上游更改的 hub 技能。 |
| `audit` | 重新扫描已安装的 hub 技能。 |
| `uninstall` | 移除 hub 安装的技能。 |
| `publish` | 向注册表发布技能。 |
| `snapshot` | 导出/导入技能配置。 |
| `tap` | 管理自定义技能源。 |
| `config` | 按平台对技能进行交互式启用/禁用配置。 |

常见示例：

```bash
hermes skills browse
hermes skills browse --source official
hermes skills search react --source skills-sh
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect official/security/1password
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install official/migration/openclaw-migration
hermes skills install skills-sh/anthropics/skills/pdf --force
hermes skills check
hermes skills update
hermes skills config
```

注意：
- `--force` 可以覆盖第三方/社区技能的非危险策略块。
- `--force` 不会覆盖 `dangerous` 扫描 verdict。
- `--source skills-sh` 搜索公共 `skills.sh` 目录。
- `--source well-known` 允许您将 Hermes 指向公开 `/.well-known/skills/index.json` 的站点。

## `hermes honcho`

```bash
hermes honcho [--target-profile NAME] <subcommand>
```

管理 Honcho 跨会话内存集成。此命令由 Honcho 内存提供商插件提供，仅当配置中的 `memory.provider` 设置为 `honcho` 时可用。

`--target-profile` 标志允许您管理另一个配置文件的 Honcho 配置而无需切换到它。

子命令：

| 子命令 | 描述 |
|------------|-------------|
| `setup` | 重定向到 `hermes memory setup`（统一设置路径）。 |
| `status [--all]` | 显示当前 Honcho 配置和连接状态。`--all` 显示跨配置文件概览。 |
| `peers` | 显示所有配置文件中的对等身份。 |
| `sessions` | 列出已知的 Honcho 会话映射。 |
| `map [name]` | 将当前目录映射到 Honcho 会话名称。省略 `name` 以列出当前映射。 |
| `peer` | 显示或更新对等名称和辩证推理级别。选项：`--user NAME`、`--ai NAME`、`--reasoning LEVEL`。 |
| `mode [mode]` | 显示或设置召回模式：`hybrid`、`context` 或 `tools`。省略以显示当前。 |
| `tokens` | 显示或设置上下文和辩证的令牌预算。选项：`--context N`、`--dialectic N`。 |
| `identity [file] [--show]` | 种子或显示 AI 对等身份表示。 |
| `enable` | 为活动配置文件启用 Honcho。 |
| `disable` | 为活动配置文件禁用 Honcho。 |
| `sync` | 将 Honcho 配置同步到所有现有配置文件（创建缺失的主机块）。 |
| `migrate` | 从 openclaw-honcho 到 Hermes Honcho 的分步迁移指南。 |

## `hermes memory`

```bash
hermes memory <subcommand>
```

设置和管理外部内存提供商插件。可用提供商：honcho、openviking、mem0、hindsight、holographic、retaindb、byterover、supermemory。一次只能有一个外部提供商处于活动状态。内置内存 (MEMORY.md/USER.md) 始终处于活动状态。

子命令：

| 子命令 | 描述 |
|------------|-------------|
| `setup` | 交互式提供商选择和配置。 |
| `status` | 显示当前内存提供商配置。 |
| `off` | 禁用外部提供商（仅内置）。 |

## `hermes acp`

```bash
hermes acp
```

启动 Hermes 作为 ACP（智能体客户端协议）stdio 服务器，用于编辑器集成。

相关入口点：

```bash
hermes-acp
python -m acp_adapter
```

首先安装支持：

```bash
pip install -e '.[acp]'
```

请参阅 [ACP 编辑器集成](../user-guide/features/acp.md) 和 [ACP 内部](../developer-guide/acp-internals.md)。

## `hermes mcp`

```bash
hermes mcp <subcommand>
```

管理 MCP（模型上下文协议）服务器配置并运行 Hermes 作为 MCP 服务器。

| 子命令 | 描述 |
|------------|-------------|
| `serve [-v\|--verbose]` | 运行 Hermes 作为 MCP 服务器 — 向其他智能体公开对话。 |
| `add <name> [--url URL] [--command CMD] [--args ...] [--auth oauth\|header]` | 添加带有自动工具发现的 MCP 服务器。 |
| `remove <name>` (别名: `rm`) | 从配置中删除 MCP 服务器。 |
| `list` (别名: `ls`) | 列出配置的 MCP 服务器。 |
| `test <name>` | 测试与 MCP 服务器的连接。 |
| `configure <name>` (别名: `config`) | 切换服务器的工具选择。 |

请参阅 [MCP 配置参考](./mcp-config-reference.md)、[将 MCP 与 Hermes 一起使用](../guides/use-mcp-with-hermes.md) 和 [MCP 服务器模式](../user-guide/features/mcp.md#running-hermes-as-an-mcp-server)。

## `hermes plugins`

```bash
hermes plugins [subcommand]
```

统一插件管理 — 通用插件、内存提供商和上下文引擎在一个地方。运行不带子命令的 `hermes plugins` 会打开一个包含两个部分的复合交互式屏幕：

- **通用插件** — 多选复选框以启用/禁用已安装的插件
- **提供商插件** — 内存提供商和上下文引擎的单选配置。按 ENTER 进入类别以打开单选选择器。

| 子命令 | 描述 |
|------------|-------------|
| *(无)* | 复合交互式 UI — 通用插件切换 + 提供商插件配置。 |
| `install <identifier> [--force]` | 从 Git URL 或 `owner/repo` 安装插件。 |
| `update <name>` | 为已安装的插件拉取最新更改。 |
| `remove <name>` (别名: `rm`, `uninstall`) | 移除已安装的插件。 |
| `enable <name>` | 启用已禁用的插件。 |
| `disable <name>` | 禁用插件而不移除它。 |
| `list` (别名: `ls`) | 列出已安装的插件及其启用/禁用状态。 |

提供商插件选择保存到 `config.yaml`：
- `memory.provider` — 活动内存提供商（空 = 仅内置）
- `context.engine` — 活动上下文引擎（`"compressor"` = 内置默认值）

通用插件禁用列表存储在 `config.yaml` 下的 `plugins.disabled` 中。

请参阅 [插件](../user-guide/features/plugins.md) 和 [构建 Hermes 插件](../guides/build-a-hermes-plugin.md)。

## `hermes tools`

```bash
hermes tools [--summary]
```

| 选项 | 描述 |
|--------|-------------|
| `--summary` | 打印当前启用工具的摘要并退出。 |

没有 `--summary` 时，这会启动交互式按平台工具配置 UI。

## `hermes sessions`

```bash
hermes sessions <subcommand>
```

子命令：

| 子命令 | 描述 |
|------------|-------------|
| `list` | 列出最近的会话。 |
| `browse` | 带有搜索和恢复的交互式会话选择器。 |
| `export <output> [--session-id ID]` | 将会话导出到 JSONL。 |
| `delete <session-id>` | 删除一个会话。 |
| `prune` | 删除旧会话。 |
| `stats` | 显示会话存储统计信息。 |
| `rename <session-id> <title>` | 设置或更改会话标题。 |

## `hermes insights`

```bash
hermes insights [--days N] [--source platform]
```

| 选项 | 描述 |
|--------|-------------|
| `--days <n>` | 分析过去 `n` 天（默认：30）。 |
| `--source <platform>` | 按来源过滤，如 `cli`、`telegram` 或 `discord`。 |

## `hermes claw`

```bash
hermes claw migrate [options]
```

将您的 OpenClaw 设置迁移到 Hermes。从 `~/.openclaw`（或自定义路径）读取并写入 `~/.hermes`。自动检测旧目录名称（`~/.clawdbot`、`~/.moltbot`）和配置文件名（`clawdbot.json`、`moltbot.json`）。

| 选项 | 描述 |
|--------|-------------|
| `--dry-run` | 预览将迁移的内容而不写入任何内容。 |
| `--preset <name>` | 迁移预设：`full`（默认，包括秘密）或 `user-data`（不包括 API 密钥）。 |
| `--overwrite` | 在冲突时覆盖现有的 Hermes 文件（默认：跳过）。 |
| `--migrate-secrets` | 在迁移中包含 API 密钥（默认与 `--preset full` 一起启用）。 |
| `--source <path>` | 自定义 OpenClaw 目录（默认：`~/.openclaw`）。 |
| `--workspace-target <path>` | 工作区指令的目标目录（AGENTS.md）。 |
| `--skill-conflict <mode>` | 处理技能名称冲突：`skip`（默认）、`overwrite` 或 `rename`。 |
| `--yes` | 跳过确认提示。 |

### 迁移内容

迁移涵盖了角色、记忆、技能、模型提供商、消息平台、智能体行为、会话策略、MCP 服务器、TTS 等 30+ 类别。项目要么**直接导入**到 Hermes 等效项，要么**存档**以供手动审查。

**直接导入：** SOUL.md、MEMORY.md、USER.md、AGENTS.md、技能（4 个源目录）、默认模型、自定义提供商、MCP 服务器、消息平台令牌和允许列表（Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Mattermost）、智能体默认值（推理努力、压缩、人类延迟、时区、沙箱）、会话重置策略、批准规则、TTS 配置、浏览器设置、工具设置、执行超时、命令允许列表、网关配置，以及来自 3 个源的 API 密钥。

**存档以供手动审查：** Cron 作业、插件、钩子/webhook、内存后端（QMD）、技能注册表配置、UI/身份、日志记录、多智能体设置、频道绑定、IDENTITY.md、TOOLS.md、HEARTBEAT.md、BOOTSTRAP.md。

**API 密钥解析**按优先级顺序检查三个源：配置值 → `~/.openclaw/.env` → `auth-profiles.json`。所有令牌字段处理纯字符串、环境模板（`${VAR}`）和 SecretRef 对象。

有关完整的配置键映射、SecretRef 处理详细信息和迁移后清单，请参阅 **[完整迁移指南](../guides/migrate-from-openclaw.md)**。

### 示例

```bash
# 预览将迁移的内容
hermes claw migrate --dry-run

# 完整迁移包括 API 密钥
hermes claw migrate --preset full

# 仅迁移用户数据（无秘密），覆盖冲突
hermes claw migrate --preset user-data --overwrite

# 从自定义 OpenClaw 路径迁移
hermes claw migrate --source /home/user/old-openclaw
```

## `hermes dashboard`

```bash
hermes dashboard [options]
```

启动 Web 仪表板 — 基于浏览器的 UI，用于管理配置、API 密钥和监控会话。需要 `pip install hermes-agent[web]`（FastAPI + Uvicorn）。有关完整文档，请参阅 [Web 仪表板](/docs/user-guide/features/web-dashboard)。

| 选项 | 默认值 | 描述 |
|--------|---------|-------------|
| `--port` | `9119` | Web 服务器运行的端口 |
| `--host` | `127.0.0.1` | 绑定地址 |
| `--no-open` | — | 不自动打开浏览器 |

```bash
# 默认 — 打开浏览器到 http://127.0.0.1:9119
hermes dashboard

# 自定义端口，无浏览器
hermes dashboard --port 8080 --no-open
```

## `hermes profile`

```bash
hermes profile <subcommand>
```

管理配置文件 — 多个隔离的 Hermes 实例，每个都有自己的配置、会话、技能和主目录。

| 子命令 | 描述 |
|------------|-------------|
| `list` | 列出所有配置文件。 |
| `use <name>` | 设置粘性默认配置文件。 |
| `create <name> [--clone] [--clone-all] [--clone-from <source>] [--no-alias]` | 创建新配置文件。`--clone` 从活动配置文件复制配置、`.env` 和 `SOUL.md`。`--clone-all` 复制所有状态。`--clone-from` 指定源配置文件。 |
| `delete <name> [-y]` | 删除配置文件。 |
| `show <name>` | 显示配置文件详细信息（主目录、配置等）。 |
| `alias <name> [--remove] [--name NAME]` | 管理用于快速配置文件访问的包装脚本。 |
| `rename <old> <new>` | 重命名配置文件。 |
| `export <name> [-o FILE]` | 将配置文件导出到 `.tar.gz` 存档。 |
| `import <archive> [--name NAME]` | 从 `.tar.gz` 存档导入配置文件。 |

示例：

```bash
hermes profile list
hermes profile create work --clone
hermes profile use work
hermes profile alias work --name h-work
hermes profile export work -o work-backup.tar.gz
hermes profile import work-backup.tar.gz --name restored
hermes -p work chat -q "Hello from work profile"
```

## `hermes completion`

```bash
hermes completion [bash|zsh]
```

向 stdout 打印 shell 补全脚本。在 shell 配置文件中获取输出，以获得 Hermes 命令、子命令和配置文件名称的标签补全。

示例：

```bash
# Bash
hermes completion bash >> ~/.bashrc

# Zsh
hermes completion zsh >> ~/.zshrc
```

## 维护命令

| 命令 | 描述 |
|---------|-------------|
| `hermes version` | 打印版本信息。 |
| `hermes update` | 拉取最新更改并重新安装依赖项。 |
| `hermes uninstall [--full] [--yes]` | 移除 Hermes，可选删除所有配置/数据。 |

## 另请参阅

- [斜杠命令参考](./slash-commands.md)
- [CLI 界面](../user-guide/cli.md)
- [会话](../user-guide/sessions.md)
- [技能系统](../user-guide/features/skills.md)
- [皮肤和主题](../user-guide/features/skins.md)