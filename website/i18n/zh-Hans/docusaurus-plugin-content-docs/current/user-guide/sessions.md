---
sidebar_position: 7
title: "会话"
description: "会话持久化、恢复、搜索、管理和每个平台的会话跟踪"
---

# 会话

Hermes Agent 自动将每个对话保存为会话。会话支持对话恢复、跨会话搜索和完整的对话历史管理。

## 会话如何工作

每个对话 — 无论来自 CLI、Telegram、Discord、Slack、WhatsApp、Signal、Matrix 还是任何其他消息平台 — 都会作为具有完整消息历史的会话存储。会话通过两个互补系统进行跟踪：

1. **SQLite 数据库**（`~/.hermes/state.db`）— 具有 FTS5 全文搜索的结构化会话元数据
2. **JSONL 转录本**（`~/.hermes/sessions/`）— 包含工具调用的原始对话转录本（网关）

SQLite 数据库存储：
- 会话 ID、来源平台、用户 ID
- **会话标题**（唯一、可读的名称）
- 模型名称和配置
- 系统提示快照
- 完整消息历史（角色、内容、工具调用、工具结果）
- Token 计数（输入/输出）
- 时间戳（started_at、ended_at）
- 父会话 ID（用于压缩触发的会话拆分）

### 会话来源

每个会话都标记有其来源平台：

| 来源 | 描述 |
|--------|-------------|
| `cli` | 交互式 CLI（`hermes` 或 `hermes chat`） |
| `telegram` | Telegram 信使 |
| `discord` | Discord 服务器/DM |
| `slack` | Slack 工作区 |
| `whatsapp` | WhatsApp 信使 |
| `signal` | Signal 信使 |
| `matrix` | Matrix 房间和 DM |
| `mattermost` | Mattermost 频道 |
| `email` | 电子邮件（IMAP/SMTP） |
| `sms` | 通过 Twilio 的 SMS |
| `dingtalk` | 钉钉信使 |
| `feishu` | 飞书/钉钉信使 |
| `wecom` | 企业微信 |
| `weixin` | 个人微信 |
| `bluebubbles` | 通过 BlueBubbles macOS 服务器的 Apple iMessage |
| `qqbot` | 通过官方 API v2 的 QQ 机器人 |
| `homeassistant` | Home Assistant 对话 |
| `webhook` | 传入的 webhooks |
| `api-server` | API 服务器请求 |
| `acp` | ACP 编辑器集成 |
| `cron` | 定时 cron 任务 |
| `batch` | 批处理运行 |

## CLI 会话恢复

使用 `--continue` 或 `--resume` 从 CLI 恢复之前的对话：

### 继续最后一个会话

```bash
# 恢复最近的 CLI 会话
hermes --continue
hermes -c

# 或使用 chat 子命令
hermes chat --continue
hermes chat -c
```

这会从 SQLite 数据库中查找最近的 `cli` 会话并加载其完整对话历史。

### 按名称恢复

如果您为会话指定了标题（请参阅下面的[会话命名](#session-naming)），可以按名称恢复：

```bash
# 恢复命名的会话
hermes -c "my project"

# 如果有世系变体（my project, my project #2, my project #3），
# 这会自动恢复最近的一个
hermes -c "my project"   # → 恢复 "my project #3"
```

### 恢复特定会话

```bash
# 按 ID 恢复特定会话
hermes --resume 20250305_091523_a1b2c3d4
hermes -r 20250305_091523_a1b2c3d4

# 按标题恢复
hermes --resume "refactoring auth"

# 或使用 chat 子命令
hermes chat --resume 20250305_091523_a1b2c3d4
```

会话 ID 在您退出 CLI 会话时显示，可以通过 `hermes sessions list` 找到。

### 恢复时的对话回顾

恢复会话时，Hermes 会在输入提示之前显示一个紧凑的之前对话回顾面板：

<img className="docs-terminal-figure" src="/img/docs/session-recap.svg" alt="恢复 Hermes 会话时显示的之前对话回顾面板的样式化预览。" />
<p className="docs-figure-caption">恢复模式显示一个紧凑的回顾面板，其中包含最近的用户和助手回合，然后返回到实时提示。</p>

回顾内容：
- 显示**用户消息**（金色 `●`）和**助手响应**（绿色 `◆`）
- **截断**长消息（用户 300 字符，助手 200 字符/3 行）
- **折叠**工具调用为带工具名称的计数（例如，`[3 tool calls: terminal, web_search]`）
- **隐藏**系统消息、工具结果和内部推理
- **限制**为最近 10 次交换，并显示"... N earlier messages ..."指示器
- 使用**暗淡样式**以区别于活动对话

要禁用回顾并保持最小的一行行为，请在 `~/.hermes/config.yaml` 中设置：

```yaml
display:
  resume_display: minimal   # 默认: full
```

:::tip
会话 ID 遵循格式 `YYYYMMDD_HHMMSS_<8-char-hex>`，例如 `20250305_091523_a1b2c3d4`。您可以按 ID 或按标题恢复 — 两者都可以与 `-c` 和 `-r` 一起使用。
:::

## 会话命名

为会话指定可读的标题，以便您可以轻松找到和恢复它们。

### 自动生成的标题

Hermes 会在第一次交换后自动为每个会话生成一个简短的描述性标题（3-7 个词）。这使用快速辅助模型在后台线程中运行，因此不会增加延迟。您会在使用 `hermes sessions list` 或 `hermes sessions browse` 浏览会话时看到自动生成的标题。

自动标题每个会话只会触发一次，如果您已经手动设置了标题，则会跳过。

### 手动设置标题

在任何聊天会话（CLI 或网关）中使用 `/title` 斜杠命令：

```
/title 我的研究项目
```

标题会立即应用。如果会话尚未在数据库中创建（例如，您在发送第一条消息之前运行 `/title`），它会被排队并在会话启动后应用。

您也可以从命令行重命名现有会话：

```bash
hermes sessions rename 20250305_091523_a1b2c3d4 "refactoring auth module"
```

### 标题规则

- **唯一** — 没有两个会话可以共享相同的标题
- **最多 100 个字符** — 保持列表输出整洁
- **清理** — 控制字符、零宽字符和 RTL 覆盖会自动剥离
- **正常 Unicode 没问题** — 表情符号、CJK 字符、重音字符都可以使用

### 压缩时的自动世系

当会话的上下文被压缩时（手动通过 `/compress` 或自动），Hermes 会创建一个新的延续会话。如果原始会话有标题，新会话会自动获得编号标题：

```
"my project" → "my project #2" → "my project #3"
```

当您按名称恢复（`hermes -c "my project"`）时，它会自动选择世系中最新的会话。

### 消息平台中的 /title

`/title` 命令在所有网关平台（Telegram、Discord、Slack、WhatsApp）中都可用：

- `/title 我的研究` — 设置会话标题
- `/title` — 显示当前标题

## 会话管理命令

Hermes 通过 `hermes sessions` 提供完整的会话管理命令：

### 列出会话

```bash
# 列出最近的会话（默认：最近 20 个）
hermes sessions list

# 按平台过滤
hermes sessions list --source telegram

# 显示更多会话
hermes sessions list --limit 50
```

当会话有标题时，输出显示标题、预览和相对时间戳：

```
标题                      预览                                    最后活动    ID
────────────────────────────────────────────────────────────────────────────────────────────────
重构身份验证模块         请帮我重构身份验证模块                    2小时前      20250305_091523_a
my project #3          你能检查一下测试失败吗？                  昨天        20250304_143022_e
—                      拉斯维加斯的天气怎么样？                  3天前        20250303_101500_f
```

当没有会话有标题时，使用更简单的格式：

```
预览                                              最后活动    平台    ID
──────────────────────────────────────────────────────────────────────────────────────
请帮我重构身份验证模块                              2小时前      cli     20250305_091523_a
拉斯维加斯的天气怎么样？                            3天前        tele    20250303_101500_f
```

### 导出会话

```bash
# 将所有会话导出到 JSONL 文件
hermes sessions export backup.jsonl

# 导出特定平台的会话
hermes sessions export telegram-history.jsonl --source telegram

# 导出单个会话
hermes sessions export session.jsonl --session-id 20250305_091523_a1b2c3d4
```

导出的文件每行包含一个 JSON 对象，具有完整的会话元数据和所有消息。

### 删除会话

```bash
# 删除特定会话（带确认）
hermes sessions delete 20250305_091523_a1b2c3d4

# 无需确认直接删除
hermes sessions delete 20250305_091523_a1b2c3d4 --yes
```

### 重命名会话

```bash
# 设置或更改会话的标题
hermes sessions rename 20250305_091523_a1b2c3d4 "调试身份验证流程"

# 多词标题在 CLI 中不需要引号
hermes sessions rename 20250305_091523_a1b2c3d4 调试 身份验证 流程
```

如果标题已被另一个会话使用，则显示错误。

### 修剪旧会话

```bash
# 删除早于 90 天的已结束会话（默认）
hermes sessions prune

# 自定义时间阈值
hermes sessions prune --older-than 30

# 仅修剪特定平台的会话
hermes sessions prune --source telegram --older-than 60

# 跳过确认
hermes sessions prune --older-than 30 --yes
```

:::info
修剪仅删除**已结束**的会话（已明确结束或自动重置的会话）。活动会话永远不会被修剪。
:::

### 会话统计

```bash
hermes sessions stats
```

输出：

```
总会话数：142
总消息数：3847
  cli: 89 个会话
  telegram: 38 个会话
  discord: 15 个会话
数据库大小：12.4 MB
```

要进行更深入的分析 — token 使用情况、成本估算、工具分解和活动模式 — 请使用 [`hermes insights`](/docs/reference/cli-commands#hermes-insights)。

## 会话搜索工具

智能体有一个内置的 `session_search` 工具，使用 SQLite 的 FTS5 引擎对所有过去的对话进行全文搜索。

### 工作原理

1. FTS5 搜索按相关性排名的匹配消息
2. 按会话对结果进行分组，获取前 N 个唯一会话（默认 3 个）
3. 加载每个会话的对话，截断到以匹配为中心的大约 100K 字符
4. 发送到快速摘要模型以获得重点摘要
5. 返回每个会话的摘要以及元数据和周围上下文

### FTS5 查询语法

搜索支持标准 FTS5 查询语法：

- 简单关键词：`docker deployment`
- 短语：`"exact phrase"`
- 布尔值：`docker OR kubernetes`，`python NOT java`
- 前缀：`deploy*`

### 何时使用

智能体会自动提示使用会话搜索：

> *"当用户引用过去对话中的内容或您怀疑存在相关先前上下文时，使用 session_search 来回忆它，而不是要求他们重复。"*

## 每个平台的会话跟踪

### 网关会话

在消息平台上，会话由根据消息源构建的确定性会话键标识：

| 聊天类型 | 默认键格式 | 行为 |
|-----------|--------------------|----------|
| Telegram DM | `agent:main:telegram:dm:<chat_id>` | 每个 DM 聊天一个会话 |
| Discord DM | `agent:main:discord:dm:<chat_id>` | 每个 DM 聊天一个会话 |
| WhatsApp DM | `agent:main:whatsapp:dm:<chat_id>` | 每个 DM 聊天一个会话 |
| 群聊 | `agent:main:<platform>:group:<chat_id>:<user_id>` | 当平台暴露用户 ID 时，群内每个用户一个会话 |
| 群组话题/主题 | `agent:main:<platform>:group:<chat_id>:<thread_id>` | 所有话题参与者共享一个会话（默认）。使用 `thread_sessions_per_user: true` 则每个用户一个。 |
| 频道 | `agent:main:<platform>:channel:<chat_id>:<user_id>` | 当平台暴露用户 ID 时，频道内每个用户一个会话 |

当 Hermes 无法为共享聊天获取参与者标识符时，它会退回到该房间的一个共享会话。

### 共享与隔离的群组会话

默认情况下，Hermes 在 `config.yaml` 中使用 `group_sessions_per_user: true`。这意味着：

- Alice 和 Bob 可以在同一个 Discord 频道中与 Hermes 对话，而无需共享转录历史
- 一个用户的长时间工具密集型任务不会污染另一个用户的上下文窗口
- 中断处理也保持按用户进行，因为运行中的智能体键与隔离的会话键匹配

如果您想要一个共享的"房间大脑"，请设置：

```yaml
group_sessions_per_user: false
```

这会将群组/频道恢复为每个房间一个共享会话，这保留了共享对话上下文，但也共享 token 成本、中断状态和上下文增长。

### 会话重置策略

网关会话会根据可配置的策略自动重置：

- **idle** — 空闲 N 分钟后重置
- **daily** — 每天特定时间重置
- **both** — 无论哪个先发生（空闲或每天）都重置
- **none** — 永不自动重置

在会话自动重置之前，智能体会获得一个回合来保存任何重要的记忆或技能。

具有**活动后台进程**的会话永远不会被自动重置，无论策略如何。

## 存储位置

| 内容 | 路径 | 描述 |
|------|------|-------------|
| SQLite 数据库 | `~/.hermes/state.db` | 所有会话元数据 + 带 FTS5 的消息 |
| 网关转录本 | `~/.hermes/sessions/` | 每个会话的 JSONL 转录本 + sessions.json 索引 |
| 网关索引 | `~/.hermes/sessions/sessions.json` | 将会话键映射到活动会话 ID |

SQLite 数据库使用 WAL 模式进行并发读取和单个写入，这非常适合网关的多平台架构。

### 数据库模式

`state.db` 中的关键表：

- **sessions** — 会话元数据（id、source、user_id、model、title、时间戳、token 计数）。标题有唯一索引（允许 NULL 标题，只有非 NULL 必须唯一）。
- **messages** — 完整消息历史（role、content、tool_calls、tool_name、token_count）
- **messages_fts** — 用于消息内容全文搜索的 FTS5 虚拟表

## 会话过期和清理

### 自动清理

- 网关会话根据配置的重置策略自动重置
- 重置前，智能体会保存即将过期的会话中的记忆和技能
- 已结束的会话保留在数据库中直到被修剪

### 手动清理

```bash
# 修剪早于 90 天的会话
hermes sessions prune

# 删除特定会话
hermes sessions delete <session_id>

# 修剪前导出（备份）
hermes sessions export backup.jsonl
hermes sessions prune --older-than 30 --yes
```

:::tip
数据库增长缓慢（典型：数百个会话约 10-15 MB）。修剪主要用于删除您不再需要用于搜索回忆的旧对话。
:::