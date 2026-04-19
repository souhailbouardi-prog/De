---
sidebar_position: 2
---

# 配置文件：运行多个代理

在同一台机器上运行多个独立的 Hermes 代理 — 每个都有自己的配置、API 密钥、内存、会话、技能和网关。

## 什么是配置文件？

配置文件是一个完全隔离的 Hermes 环境。每个配置文件都有自己的目录，包含自己的 `config.yaml`、`.env`、`SOUL.md`、记忆、会话、技能、cron 作业和状态数据库。配置文件允许您为不同目的运行单独的代理 — 编码助手、个人机器人、研究代理 — 而不会有任何交叉污染。

当您创建配置文件时，它会自动成为自己的命令。创建一个名为 `coder` 的配置文件，您立即拥有 `coder chat`、`coder setup`、`coder gateway start` 等命令。

## 快速开始

```bash
hermes profile create coder       # 创建配置文件 + "coder" 命令别名
coder setup                       # 配置 API 密钥和模型
coder chat                        # 开始聊天
```

就是这样。`coder` 现在是一个完全独立的代理。它有自己的配置、自己的记忆、自己的一切。

## 创建配置文件

### 空白配置文件

```bash
hermes profile create mybot
```

创建一个带有内置技能的全新配置文件。运行 `mybot setup` 来配置 API 密钥、模型和网关令牌。

### 仅克隆配置 (`--clone`)

```bash
hermes profile create work --clone
```

将当前配置文件的 `config.yaml`、`.env` 和 `SOUL.md` 复制到新配置文件中。相同的 API 密钥和模型，但会话和记忆是全新的。编辑 `~/.hermes/profiles/work/.env` 获取不同的 API 密钥，或编辑 `~/.hermes/profiles/work/SOUL.md` 获取不同的个性。

### 克隆所有内容 (`--clone-all`)

```bash
hermes profile create backup --clone-all
```

复制**所有内容** — 配置、API 密钥、个性、所有记忆、完整会话历史、技能、cron 作业、插件。一个完整的快照。对备份或分叉已经有上下文的代理很有用。

### 从特定配置文件克隆

```bash
hermes profile create work --clone --clone-from coder
```

:::tip Honcho 记忆 + 配置文件
当 Honcho 启用时，`--clone` 会自动为新配置文件创建一个专用的 AI 对等体，同时共享相同的用户工作区。每个配置文件构建自己的观察和身份。有关详细信息，请参阅 [Honcho -- 多代理 / 配置文件](./features/memory-providers.md#honcho)。
:::

## 使用配置文件

### 命令别名

每个配置文件自动在 `~/.local/bin/<name>` 获取一个命令别名：

```bash
coder chat                    # 与 coder 代理聊天
coder setup                   # 配置 coder 的设置
coder gateway start           # 启动 coder 的网关
coder doctor                  # 检查 coder 的健康状况
coder skills list             # 列出 coder 的技能
coder config set model.model anthropic/claude-sonnet-4
```

别名适用于每个 hermes 子命令 — 它只是底层的 `hermes -p <name>`。

### `-p` 标志

您也可以使用任何命令显式定位配置文件：

```bash
hermes -p coder chat
hermes --profile=coder doctor
hermes chat -p coder -q "hello"    # 在任何位置都有效
```

### 粘性默认值 (`hermes profile use`)

```bash
hermes profile use coder
hermes chat                   # 现在目标是 coder
hermes tools                  # 配置 coder 的工具
hermes profile use default    # 切换回
```

设置默认值，以便普通 `hermes` 命令针对该配置文件。就像 `kubectl config use-context`。

### 知道你在哪里

CLI 总是显示哪个配置文件是活动的：

- **提示**：`coder ❯` 而不是 `❯`
- **横幅**：启动时显示 `Profile: coder`
- **`hermes profile`**：显示当前配置文件名称、路径、模型、网关状态

## 运行网关

每个配置文件都作为单独的进程运行自己的网关，使用自己的机器人令牌：

```bash
coder gateway start           # 启动 coder 的网关
assistant gateway start       # 启动 assistant 的网关（单独的进程）
```

### 不同的机器人令牌

每个配置文件都有自己的 `.env` 文件。在每个文件中配置不同的 Telegram/Discord/Slack 机器人令牌：

```bash
# 编辑 coder 的令牌
nano ~/.hermes/profiles/coder/.env

# 编辑 assistant 的令牌
nano ~/.hermes/profiles/assistant/.env
```

### 安全：令牌锁

如果两个配置文件意外使用相同的机器人令牌，第二个网关将被阻止，并显示一个明确的错误，指出冲突的配置文件。支持 Telegram、Discord、Slack、WhatsApp 和 Signal。

### 持久服务

```bash
coder gateway install         # 创建 hermes-gateway-coder systemd/launchd 服务
assistant gateway install     # 创建 hermes-gateway-assistant 服务
```

每个配置文件都有自己的服务名称。它们独立运行。

## 配置配置文件

每个配置文件都有自己的：

- **`config.yaml`** — 模型、提供者、工具集、所有设置
- **`.env`** — API 密钥、机器人令牌
- **`SOUL.md`** — 个性和指令

```bash
coder config set model.model anthropic/claude-sonnet-4
echo "You are a focused coding assistant." > ~/.hermes/profiles/coder/SOUL.md
```

## 更新

`hermes update` 拉取代码一次（共享）并自动将新的内置技能同步到**所有**配置文件：

```bash
hermes update
# → Code updated (12 commits)
# → Skills synced: default (up to date), coder (+2 new), assistant (+2 new)
```

用户修改的技能永远不会被覆盖。

## 管理配置文件

```bash
hermes profile list           # 显示所有配置文件及其状态
hermes profile show coder     # 一个配置文件的详细信息
hermes profile rename coder dev-bot   # 重命名（更新别名 + 服务）
hermes profile export coder   # 导出到 coder.tar.gz
hermes profile import coder.tar.gz   # 从存档导入
```

## 删除配置文件

```bash
hermes profile delete coder
```

这会停止网关，删除 systemd/launchd 服务，删除命令别名，并删除所有配置文件数据。您将被要求输入配置文件名称进行确认。

使用 `--yes` 跳过确认：`hermes profile delete coder --yes`

:::note
您不能删除默认配置文件 (`~/.hermes`)。要删除所有内容，请使用 `hermes uninstall`。
:::

## 标签补全

```bash
# Bash
eval "$(hermes completion bash)"

# Zsh
eval "$(hermes completion zsh)"
```

将该行添加到您的 `~/.bashrc` 或 `~/.zshrc` 以获得持久补全。在 `-p` 之后补全配置文件名称，配置文件子命令和顶级命令。

## 工作原理

配置文件使用 `HERMES_HOME` 环境变量。当您运行 `coder chat` 时，包装脚本在启动 hermes 之前设置 `HERMES_HOME=~/.hermes/profiles/coder`。由于代码库中的 119+ 文件通过 `get_hermes_home()` 解析路径，所有内容都会自动范围到配置文件的目录 — 配置、会话、内存、技能、状态数据库、网关 PID、日志和 cron 作业。

默认配置文件就是 `~/.hermes` 本身。无需迁移 — 现有安装的工作方式完全相同。