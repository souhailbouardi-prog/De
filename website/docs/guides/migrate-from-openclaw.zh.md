---
sidebar_position: 10
title: "从 OpenClaw 迁移"
description: "将 OpenClaw / Clawdbot 设置迁移到 Hermes Agent 的完整指南 — 迁移内容、配置映射以及迁移后的检查项"
---

# 从 OpenClaw 迁移

`hermes claw migrate` 会将您的 OpenClaw（或旧版 Clawdbot/Moldbot）设置导入到 Hermes。本指南详细介绍了迁移的具体内容、配置键映射以及迁移后需要验证的内容。

## 快速开始

```bash
# 预览然后迁移（总是先显示预览，然后请求确认）
hermes claw migrate

# 仅预览，不做更改
hermes claw migrate --dry-run

# 完整迁移包括 API 密钥，跳过确认
hermes claw migrate --preset full --yes
```

迁移总是在进行任何更改之前显示将导入的完整预览。查看列表，然后确认继续。

默认从 `~/.openclaw/` 读取。旧版 `~/.clawdbot/` 或 `~/.moltbot/` 目录会自动检测。旧版配置文件名（`clawdbot.json`、`moltbot.json`）也是如此。

## 选项

| 选项 | 描述 |
|--------|-------------|
| `--dry-run` | 仅预览 — 显示将迁移的内容后停止。 |
| `--preset <name>` | `full`（默认，包括密钥）或 `user-data`（排除 API 密钥）。 |
| `--overwrite` | 在冲突时覆盖现有的 Hermes 文件（默认：跳过）。 |
| `--migrate-secrets` | 包含 API 密钥（默认与 `--preset full` 一起启用）。 |
| `--source <path>` | 自定义 OpenClaw 目录。 |
| `--workspace-target <path>` | 放置 `AGENTS.md` 的位置。 |
| `--skill-conflict <mode>` | `skip`（默认）、`overwrite` 或 `rename`。 |
| `--yes` | 预览后跳过确认提示。 |

## 迁移内容

### 角色、记忆和指令

| 内容 | OpenClaw 来源 | Hermes 目标 | 说明 |
|------|----------------|-------------------|-------|
| 角色 | `workspace/SOUL.md` | `~/.hermes/SOUL.md` | 直接复制 |
| 工作区指令 | `workspace/AGENTS.md` | `--workspace-target` 中的 `AGENTS.md` | 需要 `--workspace-target` 标志 |
| 长期记忆 | `workspace/MEMORY.md` | `~/.hermes/memories/MEMORY.md` | 解析为条目，与现有条目合并，去重。使用 `§` 分隔符。 |
| 用户资料 | `workspace/USER.md` | `~/.hermes/memories/USER.md` | 与记忆相同的条目合并逻辑。 |
| 每日记忆文件 | `workspace/memory/*.md` | `~/.hermes/memories/MEMORY.md` | 所有每日文件合并到主记忆中。 |

工作区文件也会在 `workspace.default/` 和 `workspace-main/` 作为回退路径检查（OpenClaw 在最近版本中将 `workspace/` 重命名为 `workspace-main/`，并对多代理设置使用 `workspace-{agentId}`）。

### 技能（4 个来源）

| 来源 | OpenClaw 位置 | Hermes 目标 |
|--------|------------------|-------------------|
| 工作区技能 | `workspace/skills/` | `~/.hermes/skills/openclaw-imports/` |
| 管理/共享技能 | `~/.openclaw/skills/` | `~/.hermes/skills/openclaw-imports/` |
| 个人跨项目 | `~/.agents/skills/` | `~/.hermes/skills/openclaw-imports/` |
| 项目级共享 | `workspace/.agents/skills/` | `~/.hermes/skills/openclaw-imports/` |

技能冲突由 `--skill-conflict` 处理：`skip` 保留现有的 Hermes 技能，`overwrite` 替换它，`rename` 创建一个 `-imported` 副本。

### 模型和提供商配置

| 内容 | OpenClaw 配置路径 | Hermes 目标 | 说明 |
|------|---------------------|-------------------|-------|
| 默认模型 | `agents.defaults.model` | `config.yaml` → `model` | 可以是字符串或 `{primary, fallbacks}` 对象 |
| 自定义提供商 | `models.providers.*` | `config.yaml` → `custom_providers` | 映射 `baseUrl`、`apiType`/`api` — 处理短值（"openai"、"anthropic"）和连字符值（"openai-completions"、"anthropic-messages"、"google-generative-ai"） |
| 提供商 API 密钥 | `models.providers.*.apiKey` | `~/.hermes/.env` | 需要 `--migrate-secrets`。见下面的 [API 密钥解析](#api-密钥解析)。 |

### 代理行为

| 内容 | OpenClaw 配置路径 | Hermes 配置路径 | 映射 |
|------|---------------------|-------------------|---------|
| 最大轮次 | `agents.defaults.timeoutSeconds` | `agent.max_turns` | `timeoutSeconds / 10`，上限为 200 |
| 详细模式 | `agents.defaults.verboseDefault` | `agent.verbose` | "off" / "on" / "full" |
| 推理努力 | `agents.defaults.thinkingDefault` | `agent.reasoning_effort` | "always"/"high"/"xhigh" → "high"，"auto"/"medium"/"adaptive" → "medium"，"off"/"low"/"none"/"minimal" → "low" |
| 压缩 | `agents.defaults.compaction.mode` | `compression.enabled` | "off" → false，其他 → true |
| 压缩模型 | `agents.defaults.compaction.model` | `compression.summary_model` | 直接字符串复制 |
| 人类延迟 | `agents.defaults.humanDelay.mode` | `human_delay.mode` | "natural" / "custom" / "off" |
| 人类延迟时间 | `agents.defaults.humanDelay.minMs` / `.maxMs` | `human_delay.min_ms` / `.max_ms` | 直接复制 |
| 时区 | `agents.defaults.userTimezone` | `timezone` | 直接字符串复制 |
| 执行超时 | `tools.exec.timeoutSec` | `terminal.timeout` | 直接复制（字段是 `timeoutSec`，不是 `timeout`） |
| Docker 沙箱 | `agents.defaults.sandbox.backend` | `terminal.backend` | "docker" → "docker" |
| Docker 镜像 | `agents.defaults.sandbox.docker.image` | `terminal.docker_image` | 直接复制 |

### 会话重置策略

| OpenClaw 配置路径 | Hermes 配置路径 | 说明 |
|---------------------|-------------------|-------|
| `session.reset.mode` | `session_reset.mode` | "daily"、"idle" 或两者 |
| `session.reset.atHour` | `session_reset.at_hour` | 每日重置的小时（0–23） |
| `session.reset.idleMinutes` | `session_reset.idle_minutes` | 不活动分钟数 |

注意：OpenClaw 还有 `session.resetTriggers`（一个简单的字符串数组，如 `["daily", "idle"]`）。如果结构化的 `session.reset` 不存在，迁移会回退到从 `resetTriggers` 推断。

### MCP 服务器

| OpenClaw 字段 | Hermes 字段 | 说明 |
|----------------|-------------|-------|
| `mcp.servers.*.command` | `mcp_servers.*.command` | Stdio 传输 |
| `mcp.servers.*.args` | `mcp_servers.*.args` | |
| `mcp.servers.*.env` | `mcp_servers.*.env` | |
| `mcp.servers.*.cwd` | `mcp_servers.*.cwd` | |
| `mcp.servers.*.url` | `mcp_servers.*.url` | HTTP/SSE 传输 |
| `mcp.servers.*.tools.include` | `mcp_servers.*.tools.include` | 工具过滤 |
| `mcp.servers.*.tools.exclude` | `mcp_servers.*.tools.exclude` | |

### TTS（文本到语音）

TTS 设置从**两个** OpenClaw 配置位置读取，优先级如下：

1. `messages.tts.providers.{provider}.*`（规范位置）
2. 顶层 `talk.providers.{provider}.*`（回退）
3. 旧版扁平键 `messages.tts.{provider}.*`（最旧格式）

| 内容 | Hermes 目标 |
|------|-------------------|
| 提供商名称 | `config.yaml` → `tts.provider` |
| ElevenLabs 语音 ID | `config.yaml` → `tts.elevenlabs.voice_id` |
| ElevenLabs 模型 ID | `config.yaml` → `tts.elevenlabs.model_id` |
| OpenAI 模型 | `config.yaml` → `tts.openai.model` |
| OpenAI 语音 | `config.yaml` → `tts.openai.voice` |
| Edge TTS 语音 | `config.yaml` → `tts.edge.voice`（OpenClaw 将 "edge" 重命名为 "microsoft" — 两者都被识别） |
| TTS 资产 | `~/.hermes/tts/`（文件复制） |

### 消息平台

| 平台 | OpenClaw 配置路径 | Hermes `.env` 变量 | 说明 |
|----------|---------------------|----------------------|-------|
| Telegram | `channels.telegram.botToken` 或 `.accounts.default.botToken` | `TELEGRAM_BOT_TOKEN` | 令牌可以是字符串或 [SecretRef](#secretref-处理)。支持扁平布局和账户布局。 |
| Telegram | `credentials/telegram-default-allowFrom.json` | `TELEGRAM_ALLOWED_USERS` | 从 `allowFrom[]` 数组逗号连接 |
| Discord | `channels.discord.token` 或 `.accounts.default.token` | `DISCORD_BOT_TOKEN` | |
| Discord | `channels.discord.allowFrom` 或 `.accounts.default.allowFrom` | `DISCORD_ALLOWED_USERS` | |
| Slack | `channels.slack.botToken` 或 `.accounts.default.botToken` | `SLACK_BOT_TOKEN` | |
| Slack | `channels.slack.appToken` 或 `.accounts.default.appToken` | `SLACK_APP_TOKEN` | |
| Slack | `channels.slack.allowFrom` 或 `.accounts.default.allowFrom` | `SLACK_ALLOWED_USERS` | |
| WhatsApp | `channels.whatsapp.allowFrom` 或 `.accounts.default.allowFrom` | `WHATSAPP_ALLOWED_USERS` | 通过 Baileys QR 配对进行认证 — 迁移后需要重新配对 |
| Signal | `channels.signal.account` 或 `.accounts.default.account` | `SIGNAL_ACCOUNT` | |
| Signal | `channels.signal.httpUrl` 或 `.accounts.default.httpUrl` | `SIGNAL_HTTP_URL` | |
| Signal | `channels.signal.allowFrom` 或 `.accounts.default.allowFrom` | `SIGNAL_ALLOWED_USERS` | |
| Matrix | `channels.matrix.accessToken` 或 `.accounts.default.accessToken` | `MATRIX_ACCESS_TOKEN` | 使用 `accessToken`（不是 `botToken`） |
| Mattermost | `channels.mattermost.botToken` 或 `.accounts.default.botToken` | `MATTERMOST_BOT_TOKEN` | |

### 其他配置

| 内容 | OpenClaw 路径 | Hermes 路径 | 说明 |
|------|-------------|-------------|-------|
| 批准模式 | `approvals.exec.mode` | `config.yaml` → `approvals.mode` | "auto"→"off"，"always"→"manual"，"smart"→"smart" |
| 命令允许列表 | `exec-approvals.json` | `config.yaml` → `command_allowlist` | 模式合并和去重 |
| 浏览器 CDP URL | `browser.cdpUrl` | `config.yaml` → `browser.cdp_url` | |
| 浏览器无头模式 | `browser.headless` | `config.yaml` → `browser.headless` | |
| Brave 搜索键 | `tools.web.search.brave.apiKey` | `.env` → `BRAVE_API_KEY` | 需要 `--migrate-secrets` |
| 网关认证令牌 | `gateway.auth.token` | `.env` → `HERMES_GATEWAY_TOKEN` | 需要 `--migrate-secrets` |
| 工作目录 | `agents.defaults.workspace` | `.env` → `MESSAGING_CWD` | |

### 归档（无直接 Hermes 等效项）

这些被保存到 `~/.hermes/migration/openclaw/<timestamp>/archive/` 以供手动审查：

| 内容 | 归档文件 | 如何在 Hermes 中重建 |
|------|-------------|--------------------------|
| `IDENTITY.md` | `archive/workspace/IDENTITY.md` | 合并到 `SOUL.md` |
| `TOOLS.md` | `archive/workspace/TOOLS.md` | Hermes 有内置工具说明 |
| `HEARTBEAT.md` | `archive/workspace/HEARTBEAT.md` | 使用 cron 任务进行定期任务 |
| `BOOTSTRAP.md` | `archive/workspace/BOOTSTRAP.md` | 使用上下文文件或技能 |
| Cron 任务 | `archive/cron-config.json` | 使用 `hermes cron create` 重建 |
| 插件 | `archive/plugins-config.json` | 请参阅 [插件指南](/docs/user-guide/features/hooks) |
| 钩子/网络钩子 | `archive/hooks-config.json` | 使用 `hermes webhook` 或网关钩子 |
| 内存后端 | `archive/memory-backend-config.json` | 通过 `hermes honcho` 配置 |
| 技能注册表 | `archive/skills-registry-config.json` | 使用 `hermes skills config` |
| UI/身份 | `archive/ui-identity-config.json` | 使用 `/skin` 命令 |
| 日志记录 | `archive/logging-diagnostics-config.json` | 在 `config.yaml` 日志部分设置 |
| 多代理列表 | `archive/agents-list.json` | 使用 Hermes 配置文件 |
| 通道绑定 | `archive/bindings.json` | 每个平台手动设置 |
| 复杂通道 | `archive/channels-deep-config.json` | 手动平台配置 |

## API 密钥解析

启用 `--migrate-secrets` 时，API 密钥从**四个来源**按优先级顺序收集：

1. **配置值** — `models.providers.*.apiKey` 和 `openclaw.json` 中的 TTS 提供商密钥
2. **环境文件** — `~/.openclaw/.env`（如 `OPENROUTER_API_KEY`、`ANTHROPIC_API_KEY` 等键）
3. **配置环境子对象** — `openclaw.json` → `"env"` 或 `"env"."vars"`（某些设置在此存储键而不是单独的 `.env` 文件）
4. **认证配置文件** — `~/.openclaw/agents/main/agent/auth-profiles.json`（每个代理的凭证）

配置值优先。每个后续来源填充任何剩余的空白。

### 支持的密钥目标

`OPENROUTER_API_KEY`、`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`DEEPSEEK_API_KEY`、`GEMINI_API_KEY`、`ZAI_API_KEY`、`MINIMAX_API_KEY`、`ELEVENLABS_API_KEY`、`TELEGRAM_BOT_TOKEN`、`VOICE_TOOLS_OPENAI_KEY`

此允许列表中的密钥永远不会被复制。

## SecretRef 处理

OpenClaw 配置中令牌和 API 密钥的值可以采用三种格式：

```json
// 纯字符串
"channels": { "telegram": { "botToken": "123456:ABC-DEF..." } }

// 环境模板
"channels": { "telegram": { "botToken": "${TELEGRAM_BOT_TOKEN}" } }

// SecretRef 对象
"channels": { "telegram": { "botToken": { "source": "env", "id": "TELEGRAM_BOT_TOKEN" } } }
```

迁移解析所有三种格式。对于环境模板和具有 `source: "env"` 的 SecretRef 对象，它会在 `~/.openclaw/.env` 和 `openclaw.json` 环境子对象中查找值。具有 `source: "file"` 或 `source: "exec"` 的 SecretRef 对象无法自动解析 — 迁移会对此发出警告，这些值必须通过 `hermes config set` 手动添加到 Hermes。

## 迁移后

1. **检查迁移报告** — 完成时打印，包含迁移、跳过和冲突项目的计数。

2. **审查归档文件** — `~/.hermes/migration/openclaw/<timestamp>/archive/` 中的任何内容都需要手动关注。

3. **开始新会话** — 导入的技能和记忆条目在新会话中生效，而不是当前会话。

4. **验证 API 密钥** — 运行 `hermes status` 检查提供商认证。

5. **测试消息传递** — 如果您迁移了平台令牌，请重启网关：`systemctl --user restart hermes-gateway`

6. **检查会话策略** — 验证 `hermes config get session_reset` 符合您的预期。

7. **重新配对 WhatsApp** — WhatsApp 使用 QR 码配对（Baileys），而不是令牌迁移。运行 `hermes whatsapp` 进行配对。

8. **归档清理** — 确认一切正常后，运行 `hermes claw cleanup` 将剩余的 OpenClaw 目录重命名为 `.pre-migration/`（防止状态混淆）。

## 故障排除

### "OpenClaw 目录未找到"

迁移检查 `~/.openclaw/`，然后是 `~/.clawdbot/`，然后是 `~/.moltbot/`。如果您的安装在其他位置，请使用 `--source /path/to/your/openclaw`。

### "未找到提供商 API 密钥"

根据您的 OpenClaw 版本，密钥可能存储在多个位置：内联在 `openclaw.json` 中的 `models.providers.*.apiKey`、在 `~/.openclaw/.env`、在 `openclaw.json` 的 `"env"` 子对象中，或在 `agents/main/agent/auth-profiles.json` 中。迁移检查所有四个位置。如果密钥使用 `source: "file"` 或 `source: "exec"` SecretRefs，它们无法自动解析 — 通过 `hermes config set` 添加它们。

### 迁移后技能不显示

导入的技能位于 `~/.hermes/skills/openclaw-imports/`。开始新会话以使其生效，或运行 `/skills` 验证它们已加载。

### TTS 语音未迁移

OpenClaw 将 TTS 设置存储在两个位置：`messages.tts.providers.*` 和顶层 `talk` 配置。迁移检查两者。如果您的语音 ID 是通过 OpenClaw UI 设置的（存储在不同路径），您可能需要手动设置：`hermes config set tts.elevenlabs.voice_id YOUR_VOICE_ID`。