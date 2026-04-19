---
sidebar_position: 4
title: "教程：团队 Telegram 助手"
description: "设置整个团队可以用于代码帮助、研究、系统管理等功能的 Telegram 机器人的分步指南"
---

# 设置团队 Telegram 助手

本教程将引导您设置一个由 Hermes Agent 驱动的 Telegram 机器人，多个团队成员可以使用。到最后，您的团队将拥有一个共享的 AI 助手，他们可以发送消息寻求代码、研究、系统管理等方面的帮助 — 通过每用户授权进行保护。

## 我们要构建什么

一个 Telegram 机器人，具有以下功能：

- **任何授权的团队成员**都可以通过私信寻求帮助 — 代码审查、研究、shell 命令、调试
- **在您的服务器上运行**，具有完整的工具访问权限 — 终端、文件编辑、网络搜索、代码执行
- **每用户会话** — 每个人都有自己的对话上下文
- **默认安全** — 只有批准的用户可以交互，有两种授权方法
- **定时任务** — 每日站会、健康检查和提醒发送到团队频道

---

## 先决条件

在开始之前，请确保您有：

- **Hermes Agent 已安装**在服务器或 VPS 上（不是您的笔记本电脑 — 机器人需要保持运行）。如果还没有安装，请遵循[安装指南](/docs/getting-started/installation)。
- **一个 Telegram 账户**为您自己（机器人所有者）
- **配置的 LLM 提供商** — 至少是 OpenAI、Anthropic 或其他受支持提供商的 API 密钥，位于 `~/.hermes/.env` 中

:::tip
每月 5 美元的 VPS 足以运行网关。Hermes 本身是轻量级的 — LLM API 调用是花钱的部分，而这些调用是远程进行的。
:::

---

## 步骤 1：创建 Telegram 机器人

每个 Telegram 机器人都从 **@BotFather** 开始 — Telegram 的官方机器人创建机器人。

1. **打开 Telegram** 并搜索 `@BotFather`，或转到 [t.me/BotFather](https://t.me/BotFather)

2. **发送 `/newbot`** — BotFather 将询问您两件事：
   - **显示名称** — 用户看到的内容（例如，`Team Hermes Assistant`）
   - **用户名** — 必须以 `bot` 结尾（例如，`myteam_hermes_bot`）

3. **复制机器人令牌** — BotFather 回复类似以下内容：
   ```
   Use this token to access the HTTP API:
   7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...
   ```
   保存此令牌 — 您将在下一步中需要它。

4. **设置描述**（可选但推荐）：
   ```
   /setdescription
   ```
   选择您的机器人，然后输入类似以下内容：
   ```
   Team AI assistant powered by Hermes Agent. DM me for help with code, research, debugging, and more.
   ```

5. **设置机器人命令**（可选 — 为用户提供命令菜单）：
   ```
   /setcommands
   ```
   选择您的机器人，然后粘贴：
   ```
   new - Start a fresh conversation
   model - Show or change the AI model
   status - Show session info
   help - Show available commands
   stop - Stop the current task
   ```

:::warning
保持您的机器人令牌秘密。任何拥有令牌的人都可以控制机器人。如果泄露，请在 BotFather 中使用 `/revoke` 生成新令牌。
:::

---

## 步骤 2：配置网关

您有两个选项：交互式设置向导（推荐）或手动配置。

### 选项 A：交互式设置（推荐）

```bash
hermes gateway setup
```

这将引导您完成所有操作，使用箭头键选择。选择 **Telegram**，粘贴您的机器人令牌，并在提示时输入您的用户 ID。

### 选项 B：手动配置

将这些行添加到 `~/.hermes/.env`：

```bash
# Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN=7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...

# Your Telegram user ID (numeric)
TELEGRAM_ALLOWED_USERS=123456789
```

### 查找您的用户 ID

您的 Telegram 用户 ID 是一个数字值（不是您的用户名）。要找到它：

1. 在 Telegram 上向 [@userinfobot](https://t.me/userinfobot) 发送消息
2. 它会立即回复您的数字用户 ID
3. 将该数字复制到 `TELEGRAM_ALLOWED_USERS`

:::info
Telegram 用户 ID 是永久数字，如 `123456789`。它们与您的 `@username` 不同，后者可以更改。始终使用数字 ID 作为允许列表。
:::

---

## 步骤 3：启动网关

### 快速测试

首先在前台运行网关以确保一切正常工作：

```bash
hermes gateway
```

您应该看到类似以下的输出：

```
[Gateway] Starting Hermes Gateway...
[Gateway] Telegram adapter connected
[Gateway] Cron scheduler started (tick every 60s)
```

打开 Telegram，找到您的机器人，向它发送消息。如果它回复，您就成功了。按 `Ctrl+C` 停止。

### 生产环境：安装为服务

对于可在重启后继续运行的持久部署：

```bash
hermes gateway install
sudo hermes gateway install --system   # Linux 仅：启动时系统服务
```

这会创建一个后台服务：默认情况下，Linux 上是用户级 **systemd** 服务，macOS 上是 **launchd** 服务，如果您传递 `--system`，则是启动时 Linux 系统服务。

```bash
# Linux — 管理默认用户服务
hermes gateway start
hermes gateway stop
hermes gateway status

# 查看实时日志
journalctl --user -u hermes-gateway -f

# SSH 登出后保持运行
sudo loginctl enable-linger $USER

# Linux 服务器 — 明确的系统服务命令
sudo hermes gateway start --system
sudo hermes gateway status --system
journalctl -u hermes-gateway -f
```

```bash
# macOS — 管理服务
hermes gateway start
hermes gateway stop
tail -f ~/.hermes/logs/gateway.log
```

:::tip macOS PATH
launchd plist 在安装时捕获您的 shell PATH，以便网关子进程可以找到 Node.js 和 ffmpeg 等工具。如果您后来安装了新工具，请重新运行 `hermes gateway install` 以更新 plist。
:::

### 验证它正在运行

```bash
hermes gateway status
```

然后向 Telegram 上的机器人发送测试消息。您应该在几秒钟内收到回复。

---

## 步骤 4：设置团队访问

现在让我们为您的团队成员提供访问权限。有两种方法。

### 方法 A：静态允许列表

收集每个团队成员的 Telegram 用户 ID（让他们向 [@userinfobot](https://t.me/userinfobot) 发送消息），并将它们添加为逗号分隔的列表：

```bash
# In ~/.hermes/.env
TELEGRAM_ALLOWED_USERS=123456789,987654321,555555555
```

更改后重启网关：

```bash
hermes gateway stop && hermes gateway start
```

### 方法 B：私信配对（团队推荐）

私信配对更加灵活 — 您不需要预先收集用户 ID。工作原理如下：

1. **团队成员向机器人发送私信** — 由于他们不在允许列表中，机器人会回复一次性配对代码：
   ```
   🔐 Pairing code: XKGH5N7P
   Send this code to the bot owner for approval.
   ```

2. **团队成员向您发送代码**（通过任何渠道 — Slack、电子邮件、面对面）

3. **您在服务器上批准它**：
   ```bash
   hermes pairing approve telegram XKGH5N7P
   ```

4. **他们就可以使用了** — 机器人立即开始回复他们的消息

**管理配对用户：**

```bash
# 查看所有待处理和已批准的用户
hermes pairing list

# 撤销某人的访问权限
hermes pairing revoke telegram 987654321

# 清除过期的待处理代码
hermes pairing clear-pending
```

:::tip
私信配对对于团队来说是理想的，因为添加新用户时不需要重启网关。批准立即生效。
:::

### 安全考虑

- **永远不要在具有终端访问权限的机器人上设置 `GATEWAY_ALLOW_ALL_USERS=true`** — 任何找到您的机器人的人都可以在您的服务器上运行命令
- 配对代码在 **1 小时**后过期，并使用加密随机性
- 速率限制防止暴力攻击：每用户每 10 分钟 1 个请求，每个平台最多 3 个待处理代码
- 5 次失败的批准尝试后，平台进入 1 小时锁定
- 所有配对数据都以 `chmod 0600` 权限存储

---

## 步骤 5：配置机器人

### 设置家庭频道

**家庭频道**是机器人传递定时任务结果和主动消息的地方。没有它，计划任务就没有地方发送输出。

**选项 1：** 在机器人作为成员的任何 Telegram 群组或聊天中使用 `/sethome` 命令。

**选项 2：** 在 `~/.hermes/.env` 中手动设置：

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="Team Updates"
```

要查找频道 ID，请将 [@userinfobot](https://t.me/userinfobot) 添加到群组 — 它会报告群组的聊天 ID。

### 配置工具进度显示

控制机器人使用工具时显示的详细程度。在 `~/.hermes/config.yaml` 中：

```yaml
display:
  tool_progress: new    # off | new | all | verbose
```

| 模式 | 您看到的内容 |
|------|-------------|
| `off` | 仅干净的响应 — 无工具活动 |
| `new` | 每个新工具调用的简短状态（推荐用于消息传递） |
| `all` | 每个工具调用的详细信息 |
| `verbose` | 完整的工具输出，包括命令结果 |

用户还可以在聊天中使用 `/verbose` 命令按会话更改此设置。

### 使用 SOUL.md 设置个性

通过编辑 `~/.hermes/SOUL.md` 自定义机器人的沟通方式：

有关完整指南，请参阅 [使用 SOUL.md 与 Hermes](/docs/guides/use-soul-with-hermes)。

```markdown
# Soul
You are a helpful team assistant. Be concise and technical.
Use code blocks for any code. Skip pleasantries — the team
values directness. When debugging, always ask for error logs
before guessing at solutions.
```

### 添加项目上下文

如果您的团队从事特定项目，请创建上下文文件，以便机器人了解您的技术栈：

```markdown
<!-- ~/.hermes/AGENTS.md -->
# Team Context
- We use Python 3.12 with FastAPI and SQLAlchemy
- Frontend is React with TypeScript
- CI/CD runs on GitHub Actions
- Production deploys to AWS ECS
- Always suggest writing tests for new code
```

:::info
上下文文件被注入到每个会话的系统提示中。保持简洁 — 每个字符都会计入您的令牌预算。
:::

---

## 步骤 6：设置定时任务

随着网关运行，您可以安排定期任务，将结果传递到团队频道。

### 每日站会摘要

在 Telegram 上向机器人发送消息：

```
Every weekday at 9am, check the GitHub repository at
github.com/myorg/myproject for:
1. Pull requests opened/merged in the last 24 hours
2. Issues created or closed
3. Any CI/CD failures on the main branch
Format as a brief standup-style summary.
```

智能体会自动创建一个 cron 作业，并将结果传递到您提问的聊天（或家庭频道）。

### 服务器健康检查

```
Every 6 hours, check disk usage with 'df -h', memory with 'free -h',
and Docker container status with 'docker ps'. Report anything unusual —
partitions above 80%, containers that have restarted, or high memory usage.
```

### 管理定时任务

```bash
# From the CLI
hermes cron list          # View all scheduled jobs
hermes cron status        # Check if scheduler is running

# From Telegram chat
/cron list                # View jobs
/cron remove <job_id>     # Remove a job
```

:::warning
Cron 作业提示在完全新鲜的会话中运行，没有对先前对话的记忆。确保每个提示包含**所有**智能体需要的上下文 — 文件路径、URL、服务器地址和明确的指令。
:::

---

## 生产提示

### 使用 Docker 确保安全

在共享团队机器人上，使用 Docker 作为终端后端，以便智能体命令在容器中运行而不是在您的主机上：

```bash
# In ~/.hermes/.env
TERMINAL_BACKEND=docker
TERMINAL_DOCKER_IMAGE=nikolaik/python-nodejs:python3.11-nodejs20
```

或在 `~/.hermes/config.yaml` 中：

```yaml
terminal:
  backend: docker
  container_cpu: 1
  container_memory: 5120
  container_persistent: true
```

这样，即使有人要求机器人运行破坏性的东西，您的主机系统也会受到保护。

### 监控网关

```bash
# Check if the gateway is running
hermes gateway status

# Watch live logs (Linux)
journalctl --user -u hermes-gateway -f

# Watch live logs (macOS)
tail -f ~/.hermes/logs/gateway.log
```

### 保持 Hermes 更新

从 Telegram 向机器人发送 `/update` — 它将拉取最新版本并重启。或从服务器：

```bash
hermes update
hermes gateway stop && hermes gateway start
```

### 日志位置

| 内容 | 位置 |
|------|----------|
| 网关日志 | `journalctl --user -u hermes-gateway`（Linux）或 `~/.hermes/logs/gateway.log`（macOS） |
| Cron 作业输出 | `~/.hermes/cron/output/{job_id}/{timestamp}.md` |
| Cron 作业定义 | `~/.hermes/cron/jobs.json` |
| 配对数据 | `~/.hermes/pairing/` |
| 会话历史 | `~/.hermes/sessions/` |

---

## 进一步发展

您已经有了一个工作的团队 Telegram 助手。以下是一些后续步骤：

- **[安全指南](/docs/user-guide/security)** — 深入了解授权、容器隔离和命令审批
- **[消息网关](/docs/user-guide/messaging)** — 网关架构、会话管理和聊天命令的完整参考
- **[Telegram 设置](/docs/user-guide/messaging/telegram)** — 平台特定详细信息，包括语音消息和 TTS
- **[定时任务](/docs/user-guide/features/cron)** — 具有传递选项和 cron 表达式的高级 cron 调度
- **[上下文文件](/docs/user-guide/features/context-files)** — AGENTS.md、SOUL.md 和用于项目知识的 .cursorrules
- **[个性](/docs/user-guide/features/personality)** — 内置个性预设和自定义角色定义
- **添加更多平台** — 同一个网关可以同时运行 [Discord](/docs/user-guide/messaging/discord)、[Slack](/docs/user-guide/messaging/slack) 和 [WhatsApp](/docs/user-guide/messaging/whatsapp)

---

*有问题或问题？在 GitHub 上打开一个问题 — 欢迎贡献。*