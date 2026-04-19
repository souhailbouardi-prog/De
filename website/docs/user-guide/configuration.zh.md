---
sidebar_position: 2
title: "配置"
description: "配置 Hermes Agent — config.yaml、提供商、模型、API 密钥等"
---

# 配置

所有设置都存储在 `~/.hermes/` 目录中，以便于访问。

## 目录结构

```text
~/.hermes/
├── config.yaml     # 设置（模型、终端、TTS、压缩等）
├── .env            # API 密钥和密钥
├── auth.json       # OAuth 提供商凭证（Nous Portal 等）
├── SOUL.md         # 主要代理身份（系统提示中的插槽 #1）
├── memories/       # 持久记忆（MEMORY.md、USER.md）
├── skills/         # 代理创建的技能（通过 skill_manage 工具管理）
├── cron/           # 计划任务
├── sessions/       # 网关会话
└── logs/           # 日志（errors.log、gateway.log — 密钥自动脱敏）
```

## 管理配置

```bash
hermes config              # 查看当前配置
hermes config edit         # 在编辑器中打开 config.yaml
hermes config set KEY VAL  # 设置特定值
hermes config check        # 检查缺失的选项（更新后）
hermes config migrate      # 交互式添加缺失的选项

# 示例：
hermes config set model anthropic/claude-opus-4
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...  # 保存到 .env
```

:::tip
`hermes config set` 命令会自动将值路由到正确的文件 — API 密钥保存到 `.env`，其他所有内容保存到 `config.yaml`。
:::

## 配置优先级

设置按以下顺序解析（优先级从高到低）：

1. **CLI 参数** — 例如，`hermes chat --model anthropic/claude-sonnet-4`（每次调用覆盖）
2. **`~/.hermes/config.yaml`** — 所有非密钥设置的主要配置文件
3. **`~/.hermes/.env`** — 环境变量的回退；**必需**用于密钥（API 密钥、令牌、密码）
4. **内置默认值** — 当没有其他设置时的硬编码安全默认值

:::info 经验法则
密钥（API 密钥、机器人令牌、密码）放在 `.env` 中。其他所有内容（模型、终端后端、压缩设置、内存限制、工具集）放在 `config.yaml` 中。当两者都设置时，`config.yaml` 对非密钥设置优先。
:::

## 环境变量替换

您可以在 `config.yaml` 中使用 `${VAR_NAME}` 语法引用环境变量：

```yaml
auxiliary:
  vision:
    api_key: ${GOOGLE_API_KEY}
    base_url: ${CUSTOM_VISION_URL}

delegation:
  api_key: ${DELEGATION_KEY}
```

单个值中的多个引用有效：`url: "${HOST}:${PORT}"`。如果引用的变量未设置，占位符将保持原样（`${UNDEFINED_VAR}` 保持不变）。仅支持 `${VAR}` 语法 — 不支持裸 `$VAR` 展开。

有关 AI 提供商设置（OpenRouter、Anthropic、Copilot、自定义端点、自托管 LLM、回退模型等），请参阅 [AI Providers](/docs/integrations/providers)。

## 终端后端配置

Hermes 支持六种终端后端。每种后端决定代理的 shell 命令实际执行的位置 — 您的本地机器、Docker 容器、通过 SSH 的远程服务器、Modal 云沙箱、Daytona 工作区或 Singularity/Apptainer 容器。

```yaml
terminal:
  backend: local    # local | docker | ssh | modal | daytona | singularity
  cwd: "."          # 工作目录（"。" = 本地当前目录，容器为 "/root"）
  timeout: 180      # 每个命令的超时时间（秒）
  env_passthrough: []  # 转发到沙盒执行的环境变量名称（终端 + execute_code）
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"  # Singularity 后端的容器镜像
  modal_image: "nikolaik/python-nodejs:python3.11-nodejs20"                 # Modal 后端的容器镜像
  daytona_image: "nikolaik/python-nodejs:python3.11-nodejs20"               # Daytona 后端的容器镜像
```

对于 Modal 和 Daytona 等云沙箱，`container_persistent: true` 意味着 Hermes 将尝试在沙箱重建过程中保留文件系统状态。它不保证相同的实时沙箱、PID 空间或后台进程稍后仍在运行。

### 后端概述

| 后端 | 命令运行位置 | 隔离性 | 最适合 |
|---------|-------------------|-----------|----------|
| **local** | 直接在您的机器上 | 无 | 开发、个人使用 |
| **docker** | Docker 容器 | 完全（命名空间、cap-drop） | 安全沙箱、CI/CD |
| **ssh** | 通过 SSH 的远程服务器 | 网络边界 | 远程开发、强大硬件 |
| **modal** | Modal 云沙箱 | 完全（云 VM） | 临时云计算、评估 |
| **daytona** | Daytona 工作区 | 完全（云容器） | 托管云开发环境 |
| **singularity** | Singularity/Apptainer 容器 | 命名空间（--containall） | HPC 集群、共享机器 |

### 本地后端

默认选项。命令直接在您的机器上运行，没有隔离。不需要特殊设置。

```yaml
terminal:
  backend: local
```

:::warning
代理拥有与您的用户账户相同的文件系统访问权限。使用 `hermes tools` 禁用您不需要的工具，或切换到 Docker 进行沙箱处理。
:::

### Docker 后端

在具有安全强化的 Docker 容器中运行命令（所有能力都被删除，无特权升级，PID 限制）。

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_mount_cwd_to_workspace: false  # 将启动目录挂载到 /workspace
  docker_forward_env:              # 转发到容器的环境变量
    - "GITHUB_TOKEN"
  docker_volumes:                  # 主机目录挂载
    - "/home/user/projects:/workspace/projects"
    - "/home/user/data:/data:ro"   # :ro 表示只读

  # 资源限制
  container_cpu: 1                 # CPU 核心（0 = 无限制）
  container_memory: 5120           # MB（0 = 无限制）
  container_disk: 51200            # MB（需要 XFS+pquota 上的 overlay2）
  container_persistent: true       # 在会话之间持久化 /workspace 和 /root
```

**要求：** 安装并运行 Docker Desktop 或 Docker Engine。Hermes 会探测 `$PATH` 加上常见的 macOS 安装位置（`/usr/local/bin/docker`、`/opt/homebrew/bin/docker`、Docker Desktop 应用程序包）。

**容器生命周期：** 每个会话启动一个长期运行的容器（`docker run -d ... sleep 2h`）。命令通过带有登录 shell 的 `docker exec` 运行。清理时，容器会被停止并移除。

**安全强化：**
- `--cap-drop ALL`，仅添加回 `DAC_OVERRIDE`、`CHOWN`、`FOWNER`
- `--security-opt no-new-privileges`
- `--pids-limit 256`
- 大小受限的 tmpfs 用于 `/tmp`（512MB）、`/var/tmp`（256MB）、`/run`（64MB）

**凭证转发：** `docker_forward_env` 中列出的环境变量首先从您的 shell 环境解析，然后从 `~/.hermes/.env` 回退。技能也可以声明 `required_environment_variables`，它们会被自动合并。

### SSH 后端

通过 SSH 在远程服务器上运行命令。使用 ControlMaster 进行连接重用（5 分钟空闲保活）。默认情况下启用持久 shell — 状态（cwd、环境变量）在命令之间保持。

```yaml
terminal:
  backend: ssh
  persistent_shell: true           # 保持长期运行的 bash 会话（默认：true）
```

**必需的环境变量：**

```bash
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=ubuntu
```

**可选：**

| 变量 | 默认值 | 描述 |
|----------|---------|-------------|
| `TERMINAL_SSH_PORT` | `22` | SSH 端口 |
| `TERMINAL_SSH_KEY` | （系统默认） | SSH 私钥路径 |
| `TERMINAL_SSH_PERSISTENT` | `true` | 启用持久 shell |

**工作原理：** 在初始化时使用 `BatchMode=yes` 和 `StrictHostKeyChecking=accept-new` 连接。持久 shell 在远程主机上保持一个 `bash -l` 进程，通过临时文件进行通信。需要 `stdin_data` 或 `sudo` 的命令会自动回退到一次性模式。

### Modal 后端

在 [Modal](https://modal.com) 云沙箱中运行命令。每个任务获得一个具有可配置 CPU、内存和磁盘的隔离 VM。文件系统可以在会话之间进行快照/恢复。

```yaml
terminal:
  backend: modal
  container_cpu: 1                 # CPU 核心
  container_memory: 5120           # MB（5GB）
  container_disk: 51200            # MB（50GB）
  container_persistent: true       # 快照/恢复文件系统
```

**必需：** 要么 `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` 环境变量，要么 `~/.modal.toml` 配置文件。

**持久性：** 启用后，沙箱文件系统在清理时被快照，并在下次会话时恢复。快照在 `~/.hermes/modal_snapshots.json` 中跟踪。这保留文件系统状态，而不是活动进程、PID 空间或后台作业。

**凭证文件：** 自动从 `~/.hermes/` 挂载（OAuth 令牌等）并在每个命令前同步。

### Daytona 后端

在 [Daytona](https://daytona.io) 托管工作区中运行命令。支持停止/恢复以实现持久性。

```yaml
terminal:
  backend: daytona
  container_cpu: 1                 # CPU 核心
  container_memory: 5120           # MB → 转换为 GiB
  container_disk: 10240            # MB → 转换为 GiB（最大 10 GiB）
  container_persistent: true       # 停止/恢复而不是删除
```

**必需：** `DAYTONA_API_KEY` 环境变量。

**持久性：** 启用后，沙箱在清理时停止（不删除），并在下次会话时恢复。沙箱名称遵循 `hermes-{task_id}` 模式。

**磁盘限制：** Daytona 强制最大 10 GiB。超过此限制的请求会被限制并发出警告。

### Singularity/Apptainer 后端

在 [Singularity/Apptainer](https://apptainer.org) 容器中运行命令。专为 HPC 集群和 Docker 不可用的共享机器设计。

```yaml
terminal:
  backend: singularity
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"
  container_cpu: 1                 # CPU 核心
  container_memory: 5120           # MB
  container_persistent: true       # 可写覆盖在会话之间持久化
```

**要求：** `apptainer` 或 `singularity` 二进制文件在 `$PATH` 中。

**镜像处理：** Docker URL（`docker://...`）会自动转换为 SIF 文件并缓存。现有 `.sif` 文件直接使用。

**临时目录：** 按顺序解析：`TERMINAL_SCRATCH_DIR` → `TERMINAL_SANDBOX_DIR/singularity` → `/scratch/$USER/hermes-agent`（HPC 约定）→ `~/.hermes/sandboxes/singularity`。

**隔离：** 使用 `--containall --no-home` 进行完全命名空间隔离，不挂载主机主目录。

### 常见终端后端问题

如果终端命令立即失败或终端工具被报告为禁用：

- **本地** — 无特殊要求。开始使用时最安全的默认选项。
- **Docker** — 运行 `docker version` 验证 Docker 是否工作。如果失败，修复 Docker 或 `hermes config set terminal.backend local`。
- **SSH** — `TERMINAL_SSH_HOST` 和 `TERMINAL_SSH_USER` 都必须设置。如果任一缺失，Hermes 会记录明确的错误。
- **Modal** — 需要 `MODAL_TOKEN_ID` 环境变量或 `~/.modal.toml`。运行 `hermes doctor` 检查。
- **Daytona** — 需要 `DAYTONA_API_KEY`。Daytona SDK 处理服务器 URL 配置。
- **Singularity** — 需要 `apptainer` 或 `singularity` 在 `$PATH` 中。在 HPC 集群上常见。

如有疑问，将 `terminal.backend` 改回 `local` 并首先验证命令在那里运行。

### Docker 卷挂载

使用 Docker 后端时，`docker_volumes` 允许您与容器共享主机目录。每个条目使用标准 Docker `-v` 语法：`host_path:container_path[:options]`。

```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/home/user/projects:/workspace/projects"   # 读写（默认）
    - "/home/user/datasets:/data:ro"              # 只读
    - "/home/user/outputs:/outputs"               # 代理写入，您读取
```

这对以下情况很有用：
- **提供文件** 给代理（数据集、配置、参考代码）
- **接收文件** 从代理（生成的代码、报告、导出）
- **共享工作区** 您和代理都访问相同的文件

也可以通过环境变量设置：`TERMINAL_DOCKER_VOLUMES='["/host:/container"]'`（JSON 数组）。

### Docker 凭证转发

默认情况下，Docker 终端会话不继承任意主机凭证。如果您需要容器内的特定令牌，请将其添加到 `terminal.docker_forward_env`。

```yaml
terminal:
  backend: docker
  docker_forward_env:
    - "GITHUB_TOKEN"
    - "NPM_TOKEN"
```

Hermes 首先从您当前的 shell 解析每个列出的变量，然后如果使用 `hermes config set` 保存，则从 `~/.hermes/.env` 回退。

:::warning
`docker_forward_env` 中列出的任何内容都会对容器内运行的命令可见。仅转发您愿意暴露给终端会话的凭证。
:::

### 可选：将启动目录挂载到 `/workspace`

Docker 沙箱默认保持隔离。除非您明确选择加入，否则 Hermes **不会** 将您当前的主机工作目录传递到容器中。

在 `config.yaml` 中启用它：

```yaml
terminal:
  backend: docker
  docker_mount_cwd_to_workspace: true
```

启用后：
- 如果您从 `~/projects/my-app` 启动 Hermes，该主机目录会被绑定挂载到 `/workspace`
- Docker 后端在 `/workspace` 中启动
- 文件工具和终端命令都看到相同的挂载项目

禁用时，`/workspace` 保持沙箱拥有，除非您通过 `docker_volumes` 明确挂载某些内容。

安全权衡：
- `false` 保留沙箱边界
- `true` 使沙箱直接访问您启动 Hermes 的目录

仅在您有意希望容器处理实时主机文件时使用此选项。

### 持久 shell

默认情况下，每个终端命令在其自己的子进程中运行 — 工作目录、环境变量和 shell 变量在命令之间重置。当启用**持久 shell** 时，单个长期运行的 bash 进程在 `execute()` 调用之间保持活动状态，因此状态在命令之间保持。

这对 **SSH 后端** 最有用，它还消除了每个命令的连接开销。持久 shell 对 SSH **默认启用**，对本地后端禁用。

```yaml
terminal:
  persistent_shell: true   # 默认 — 为 SSH 启用持久 shell
```

要禁用：

```bash
hermes config set terminal.persistent_shell false
```

**跨命令保持的内容：**
- 工作目录（`cd /tmp` 对下一个命令有效）
- 导出的环境变量（`export FOO=bar`）
- Shell 变量（`MY_VAR=hello`）

**优先级：**

| 级别 | 变量 | 默认值 |
|-------|----------|---------|
| 配置 | `terminal.persistent_shell` | `true` |
| SSH 覆盖 | `TERMINAL_SSH_PERSISTENT` | 遵循配置 |
| 本地覆盖 | `TERMINAL_LOCAL_PERSISTENT` | `false` |

每个后端的环境变量具有最高优先级。如果您也想在本地后端上使用持久 shell：

```bash
export TERMINAL_LOCAL_PERSISTENT=true
```

:::note
需要 `stdin_data` 或 sudo 的命令会自动回退到一次性模式，因为持久 shell 的 stdin 已经被 IPC 协议占用。
:::

有关每个后端的详细信息，请参阅 [Code Execution](features/code-execution.md) 和 [README 的 Terminal 部分](features/tools.md)。

## 技能设置

技能可以通过其 SKILL.md 前言声明自己的配置设置。这些是非密钥值（路径、首选项、域设置），存储在 `config.yaml` 中的 `skills.config` 命名空间下。

```yaml
skills:
  config:
    myplugin:
      path: ~/myplugin-data   # 示例 — 每个技能定义自己的键
```

**技能设置如何工作：**

- `hermes config migrate` 扫描所有启用的技能，查找未配置的设置，并提供提示
- `hermes config show` 在 "Skill Settings" 下显示所有技能设置及其所属的技能
- 当技能加载时，其解析的配置值会自动注入到技能上下文中

**手动设置值：**

```bash
hermes config set skills.config.myplugin.path ~/myplugin-data
```

有关在自己的技能中声明配置设置的详细信息，请参阅 [Creating Skills — Config Settings](/docs/developer-guide/creating-skills#config-settings-configyaml)。

## 内存配置

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 令牌
  user_char_limit: 1375     # ~500 令牌
```

## 文件读取安全

控制单个 `read_file` 调用可以返回的内容量。超过限制的读取会被拒绝并显示错误，告诉代理使用 `offset` 和 `limit` 来获取更小的范围。这可以防止单个读取缩小的 JS 包或大型数据文件淹没上下文窗口。

```yaml
file_read_max_chars: 100000  # 默认 — ~25-35K 令牌
```

如果您使用具有大上下文窗口的模型并经常读取大文件，请提高它。对于小上下文模型，降低它以保持读取效率：

```yaml
# 大上下文模型（200K+）
file_read_max_chars: 200000

# 小本地模型（16K 上下文）
file_read_max_chars: 30000
```

代理还会自动去重文件读取 — 如果相同的文件区域被读取两次且文件未更改，则返回轻量级存根而不是重新发送内容。这在上下文压缩时重置，以便代理可以在内容被汇总后重新读取文件。

## Git Worktree 隔离

启用隔离的 git worktree 以在同一仓库上并行运行多个代理：

```yaml
worktree: true    # 始终创建 worktree（与 hermes -w 相同）
# worktree: false # 默认 — 仅当传递 -w 标志时
```

启用后，每个 CLI 会话在 `.worktrees/` 下创建一个带有自己分支的新 worktree。代理可以编辑文件、提交、推送和创建 PR，而不会相互干扰。干净的 worktree 在退出时被移除；脏的 worktree 被保留以供手动恢复。

您还可以通过仓库根目录中的 `.worktreeinclude` 列出要复制到 worktree 的 gitignored 文件：

```
# .worktreeinclude
.env
.venv/
node_modules/
```

## 上下文压缩

Hermes 会自动压缩长对话以保持在模型的上下文窗口内。压缩汇总器是一个单独的 LLM 调用 — 您可以将其指向任何提供商或端点。

所有压缩设置都位于 `config.yaml` 中（无环境变量）。

### 完整参考

```yaml
compression:
  enabled: true                                     # 切换压缩开/关
  threshold: 0.50                                   # 在上下文限制的此百分比处压缩
  target_ratio: 0.20                                # 保留为最近尾部的阈值分数
  protect_last_n: 20                                # 保持未压缩的最小最近消息数

# 汇总模型/提供商在 auxiliary 下配置：
auxiliary:
  compression:
    model: "google/gemini-3-flash-preview"          # 用于汇总的模型
    provider: "auto"                                # 提供商："auto"、"openrouter"、"nous"、"codex"、"main" 等
    base_url: null                                  # 自定义 OpenAI 兼容端点（覆盖提供商）
```

:::info 旧配置迁移
具有 `compression.summary_model`、`compression.summary_provider` 和 `compression.summary_base_url` 的旧配置在首次加载时会自动迁移到 `auxiliary.compression.*`（配置版本 17）。无需手动操作。
:::

### 常见设置

**默认（自动检测）— 无需配置：**
```yaml
compression:
  enabled: true
  threshold: 0.50
```
使用第一个可用的提供商（OpenRouter → Nous → Codex）和 Gemini Flash。

**强制特定提供商**（基于 OAuth 或 API 密钥）：
```yaml
auxiliary:
  compression:
    provider: nous
    model: gemini-3-flash
```
适用于任何提供商：`nous`、`openrouter`、`codex`、`anthropic`、`main` 等。

**自定义端点**（自托管、Ollama、zai、DeepSeek 等）：
```yaml
auxiliary:
  compression:
    model: glm-4.7
    base_url: https://api.z.ai/api/coding/paas/v4
```
指向自定义 OpenAI 兼容端点。使用 `OPENAI_API_KEY` 进行身份验证。

### 三个旋钮如何交互

| `auxiliary.compression.provider` | `auxiliary.compression.base_url` | 结果 |
|---------------------|---------------------|--------|
| `auto`（默认） | 未设置 | 自动检测最佳可用提供商 |
| `nous` / `openrouter` / 等 | 未设置 | 强制该提供商，使用其身份验证 |
| 任何 | 已设置 | 直接使用自定义端点（提供商被忽略） |

:::warning 汇总模型上下文长度要求
汇总模型**必须**具有至少与您的主代理模型一样大的上下文窗口。压缩器将对话的完整中间部分发送到汇总模型 — 如果该模型的上下文窗口小于主模型的上下文窗口，汇总调用将因上下文长度错误而失败。发生这种情况时，中间回合会**无摘要地丢弃**，默默地失去对话上下文。如果您覆盖模型，请验证其上下文长度满足或超过您的主模型的上下文长度。
:::

## 上下文引擎

上下文引擎控制在接近模型的令牌限制时如何管理对话。内置的 `compressor` 引擎使用有损汇总（请参阅 [Context Compression](/docs/developer-guide/context-compression-and-caching)）。插件引擎可以用替代策略替换它。

```yaml
context:
  engine: "compressor"    # 默认 — 内置有损汇总
```

要使用插件引擎（例如，用于无损上下文管理的 LCM）：

```yaml
context:
  engine: "lcm"          # 必须匹配插件的名称
```

插件引擎**永远不会自动激活** — 您必须明确将 `context.engine` 设置为插件名称。可用的引擎可以通过 `hermes plugins` → Provider Plugins → Context Engine 浏览和选择。

有关内存插件的类似单选系统，请参阅 [Memory Providers](/docs/user-guide/features/memory-providers)。

## 迭代预算压力

当代理处理具有许多工具调用的复杂任务时，它可能会耗尽其迭代预算（默认：90 回合）而没有意识到它正在运行不足。预算压力会在接近限制时自动警告模型：

| 阈值 | 级别 | 模型看到的内容 |
|-----------|-------|---------------------|
| **70%** | 警告 | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | 警告 | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |

警告被注入到最后一个工具结果的 JSON 中（作为 `_budget_warning` 字段），而不是作为单独的消息 — 这保留了提示缓存并且不会中断对话结构。

```yaml
agent:
  max_turns: 90                # 每个对话回合的最大迭代次数（默认：90）
```

预算压力默认启用。代理自然地将警告视为工具结果的一部分，鼓励它在耗尽迭代之前巩固工作并提供响应。

当迭代预算完全耗尽时，CLI 向用户显示通知：`⚠ Iteration budget reached (90/90) — response may be incomplete`。如果预算在活动工作期间耗尽，代理会在停止前生成已完成工作的摘要。

### 流超时

LLM 流连接有两个超时层。两者都为本地提供商（localhost、LAN IP）自动调整 — 大多数设置不需要配置。

| 超时 | 默认值 | 本地提供商 | 环境变量 |
|---------|---------|----------------|---------|
| 套接字读取超时 | 120s | 自动提高到 1800s | `HERMES_STREAM_READ_TIMEOUT` |
| 陈旧流检测 | 180s | 自动禁用 | `HERMES_STREAM_STALE_TIMEOUT` |
| API 调用（非流式） | 1800s | 不变 | `HERMES_API_TIMEOUT` |

**套接字读取超时** 控制 httpx 等待来自提供商的下一个数据块的时间。本地 LLM 在产生第一个令牌之前可能需要几分钟进行预填充，因此 Hermes 在检测到本地端点时将此时间提高到 30 分钟。如果您明确设置 `HERMES_STREAM_READ_TIMEOUT`，无论端点检测如何，始终使用该值。

**陈旧流检测** 会终止接收 SSE 保活 ping 但没有实际内容的连接。这对于本地提供商完全禁用，因为它们在预填充期间不发送保活 ping。

## 上下文压力警告

与迭代预算压力分开，上下文压力跟踪对话接近**压缩阈值**的程度 — 上下文压缩触发以汇总旧消息的点。这有助于您和代理了解对话何时变得冗长。

| 进度 | 级别 | 发生的情况 |
|----------|-------|-------------|
| **≥ 60%** 到阈值 | 信息 | CLI 显示青色进度条；网关发送信息通知 |
| **≥ 85%** 到阈值 | 警告 | CLI 显示粗体黄色条；网关警告压缩即将发生 |

在 CLI 中，上下文压力以工具输出 feed 中的进度条形式出现：

```
  ◐ context ████████████░░░░░░░░ 62% to compaction  48k threshold (50%) · approaching compaction
```

在消息平台上，发送纯文本通知：

```
◐ Context: ████████████░░░░░░░░ 62% to compaction (threshold: 50% of window).
```

如果自动压缩被禁用，警告会告诉您上下文可能被截断。

上下文压力是自动的 — 无需配置。它纯粹作为面向用户的通知触发，不会修改消息流或向模型的上下文注入任何内容。

## 凭证池策略

当您为同一提供商有多个 API 密钥或 OAuth 令牌时，配置轮换策略：

```yaml
credential_pool_strategies:
  openrouter: round_robin    # 均匀循环密钥
  anthropic: least_used      # 始终选择使用最少的密钥
```

选项：`fill_first`（默认）、`round_robin`、`least_used`、`random`。有关完整文档，请参阅 [Credential Pools](/docs/user-guide/features/credential-pools)。

## 辅助模型

Hermes 使用轻量级"辅助"模型处理图像分析、网页摘要和浏览器屏幕截图分析等辅助任务。默认情况下，这些使用 **Gemini Flash** 通过自动检测 — 您不需要配置任何内容。

### 通用配置模式

Hermes 中的每个模型槽 — 辅助任务、压缩、回退 — 使用相同的三个旋钮：

| 键 | 作用 | 默认值 |
|-----|-------------|---------|
| `provider` | 使用哪个提供商进行身份验证和路由 | `"auto"` |
| `model` | 要请求的模型 | 提供商的默认值 |
| `base_url` | 自定义 OpenAI 兼容端点（覆盖提供商） | 未设置 |

当设置 `base_url` 时，Hermes 忽略提供商并直接调用该端点（使用 `api_key` 或 `OPENAI_API_KEY` 进行身份验证）。当仅设置 `provider` 时，Hermes 使用该提供商的内置身份验证和基础 URL。

辅助任务可用的提供商：`auto`、`openrouter`、`nous`、`codex`、`copilot`、`anthropic`、`main`、`zai`、`kimi-coding`、`kimi-coding-cn`、`arcee`、`minimax`、[提供商注册表](/docs/reference/environment-variables) 中注册的任何提供商，或来自您的 `custom_providers` 列表的任何命名自定义提供商（例如 `provider: "beans"`）。

:::warning `"main"` 仅用于辅助任务
`"main"` 提供商选项意味着"使用我的主代理使用的任何提供商" — 它仅在 `auxiliary:`、`compression:` 和 `fallback_model:` 配置中有效。它**不是**顶级 `model.provider` 设置的有效值。如果您使用自定义 OpenAI 兼容端点，请在 `model:` 部分设置 `provider: custom`。有关所有主模型提供商选项，请参阅 [AI Providers](/docs/integrations/providers)。
:::

### 完整辅助配置参考

```yaml
auxiliary:
  # 图像分析（vision_analyze 工具 + 浏览器屏幕截图）
  vision:
    provider: "auto"           # "auto"、"openrouter"、"nous"、"codex"、"main" 等
    model: ""                  # 例如 "openai/gpt-4o"、"google/gemini-2.5-flash"
    base_url: ""               # 自定义 OpenAI 兼容端点（覆盖提供商）
    api_key: ""                # base_url 的 API 密钥（回退到 OPENAI_API_KEY）
    timeout: 120               # 秒 — LLM API 调用超时；视觉有效负载需要慷慨的超时
    download_timeout: 30       # 秒 — 图像 HTTP 下载；为慢速连接增加

  # 网页摘要 + 浏览器页面文本提取
  web_extract:
    provider: "auto"
    model: ""                  # 例如 "google/gemini-2.5-flash"
    base_url: ""
    api_key: ""
    timeout: 360               # 秒（6 分钟）— 每次尝试 LLM 摘要

  # 危险命令批准分类器
  approval:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30                # 秒

  # 上下文压缩超时（与 compression.* 配置分开）
  compression:
    timeout: 120               # 秒 — 压缩汇总长对话，需要更多时间

  # 会话搜索 — 汇总过去的会话匹配
  session_search:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30

  # 技能中心 — 技能匹配和搜索
  skills_hub:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30

  # MCP 工具调度
  mcp:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30

  # 内存刷新 — 为持久记忆汇总对话
  flush_memories:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30
```

:::tip
每个辅助任务都有一个可配置的 `timeout`（以秒为单位）。默认值：视觉 120s，web_extract 360s，approval 30s，compression 120s。如果您为辅助任务使用慢速本地模型，请增加这些值。视觉还有一个单独的 `download_timeout`（默认 30s）用于 HTTP 图像下载 — 为慢速连接或自托管图像服务器增加此值。
:::

:::info
上下文压缩有自己的 `compression:` 块用于阈值，以及 `auxiliary.compression:` 块用于模型/提供商设置 — 请参阅上面的 [Context Compression](#context-compression)。回退模型使用 `fallback_model:` 块 — 请参阅 [Fallback Model](/docs/integrations/providers#fallback-model)。这三者都遵循相同的 provider/model/base_url 模式。
:::

### 更改视觉模型

要使用 GPT-4o 而不是 Gemini Flash 进行图像分析：

```yaml
auxiliary:
  vision:
    model: "openai/gpt-4o"
```

或通过环境变量（在 `~/.hermes/.env` 中）：

```bash
AUXILIARY_VISION_MODEL=openai/gpt-4o
```

### 提供商选项

这些选项适用于**辅助任务配置**（`auxiliary:`、`compression:`、`fallback_model:`），而不是您的主要 `model.provider` 设置。

| 提供商 | 描述 | 要求 |
|----------|-------------|-------------|
| `"auto"` | 最佳可用（默认）。视觉尝试 OpenRouter → Nous → Codex。 | — |
| `"openrouter"` | 强制 OpenRouter — 路由到任何模型（Gemini、GPT-4o、Claude 等） | `OPENROUTER_API_KEY` |
| `"nous"` | 强制 Nous Portal | `hermes auth` |
| `"codex"` | 强制 Codex OAuth（ChatGPT 账户）。支持视觉（gpt-5.3-codex）。 | `hermes model` → Codex |
| `"main"` | 使用您的活动自定义/主端点。这可以来自 `OPENAI_BASE_URL` + `OPENAI_API_KEY` 或通过 `hermes model` / `config.yaml` 保存的自定义端点。适用于 OpenAI、本地模型或任何 OpenAI 兼容 API。**仅辅助任务 — 对 `model.provider` 无效。** | 自定义端点凭证 + 基础 URL |

### 常见设置

**使用直接自定义端点**（对于本地/自托管 API 比 `provider: "main"` 更清晰）：
```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` 优先于 `provider`，因此这是将辅助任务路由到特定端点的最明确方式。对于直接端点覆盖，Hermes 使用配置的 `api_key` 或回退到 `OPENAI_API_KEY`；它不会为该自定义端点重用 `OPENROUTER_API_KEY`。

**使用 OpenAI API 密钥进行视觉：**
```yaml
# In ~/.hermes/.env:
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # 或 "gpt-4o-mini" 更便宜
```

**使用 OpenRouter 进行视觉**（路由到任何模型）：
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # 或 "google/gemini-2.5-flash" 等
```

**使用 Codex OAuth**（ChatGPT Pro/Plus 账户 — 无需 API 密钥）：
```yaml
auxiliary:
  vision:
    provider: "codex"     # 使用您的 ChatGPT OAuth 令牌
    # model 默认为 gpt-5.3-codex（支持视觉）
```

**使用本地/自托管模型：**
```yaml
auxiliary:
  vision:
    provider: "main"      # 使用您的活动自定义端点
    model: "my-local-model"
```

`provider: "main"` 使用 Hermes 用于正常聊天的任何提供商 — 无论是命名自定义提供商（例如 `beans`）、内置提供商如 `openrouter`，还是传统的 `OPENAI_BASE_URL` 端点。

:::tip
如果您使用 Codex OAuth 作为主模型提供商，视觉自动工作 — 无需额外配置。Codex 包含在视觉的自动检测链中。
:::

:::warning
**视觉需要多模态模型。** 如果您设置 `provider: "main"`，请确保您的端点支持多模态/视觉 — 否则图像分析将失败。
:::

### 环境变量（旧版）

辅助模型也可以通过环境变量配置。然而，`config.yaml` 是首选方法 — 它更易于管理，并支持所有选项，包括 `base_url` 和 `api_key`。

| 设置 | 环境变量 |
|---------|---------------------|
| 视觉提供商 | `AUXILIARY_VISION_PROVIDER` |
| 视觉模型 | `AUXILIARY_VISION_MODEL` |
| 视觉端点 | `AUXILIARY_VISION_BASE_URL` |
| 视觉 API 密钥 | `AUXILIARY_VISION_API_KEY` |
| Web 提取提供商 | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Web 提取模型 | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Web 提取端点 | `AUXILIARY_WEB_EXTRACT_BASE_URL` |
| Web 提取 API 密钥 | `AUXILIARY_WEB_EXTRACT_API_KEY` |

压缩和回退模型设置仅支持 config.yaml。

:::tip
运行 `hermes config` 查看当前辅助模型设置。仅当与默认值不同时才会显示覆盖。
:::

## 推理努力

控制模型在响应前进行多少"思考"：

```yaml
agent:
  reasoning_effort: ""   # 空 = 中等（默认）。选项：none、minimal、low、medium、high、xhigh（最大）
```

未设置时（默认），推理努力默认为"中等" — 对大多数任务都有效的平衡级别。设置值会覆盖它 — 更高的推理努力在复杂任务上产生更好的结果，但会增加令牌和延迟。

您还可以在运行时使用 `/reasoning` 命令更改推理努力：

```
/reasoning           # 显示当前努力级别和显示状态
/reasoning high      # 将推理努力设置为高
/reasoning none      # 禁用推理
/reasoning show      # 在每个响应上方显示模型思考
/reasoning hide      # 隐藏模型思考
```

## 工具使用强制

一些模型偶尔会将预期操作描述为文本而不是进行工具调用（"我会运行测试..."而不是实际调用终端）。工具使用强制注入系统提示指导，引导模型回到实际调用工具。

```yaml
agent:
  tool_use_enforcement: "auto"   # "auto" | true | false | ["model-substring", ...]
```

| 值 | 行为 |
|-------|----------|
| `"auto"`（默认） | 对匹配以下内容的模型启用：`gpt`、`codex`、`gemini`、`gemma`、`grok`。对所有其他模型（Claude、DeepSeek、Qwen 等）禁用。 |
| `true` | 始终启用，无论模型如何。如果您注意到当前模型描述动作而不是执行动作，这很有用。 |
| `false` | 始终禁用，无论模型如何。 |
| `["gpt", "codex", "qwen", "llama"]` | 仅当模型名称包含列出的子字符串之一时启用（不区分大小写）。 |

### 它注入什么

启用时，系统提示可能会添加三层指导：

1. **一般工具使用强制**（所有匹配的模型）— 指示模型立即进行工具调用而不是描述意图，继续工作直到任务完成，并且永远不要以未来行动的承诺结束回合。

2. **OpenAI 执行纪律**（仅 GPT 和 Codex 模型）— 额外指导解决 GPT 特定的失败模式：在部分结果上放弃工作、跳过前提查找、幻觉而不是使用工具，以及在没有验证的情况下声明"完成"。

3. **Google 操作指导**（仅 Gemini 和 Gemma 模型）— 简洁性、绝对路径、并行工具调用和编辑前验证模式。

这些对用户是透明的，只影响系统提示。已经可靠使用工具的模型（如 Claude）不需要此指导，这就是为什么 `"auto"` 排除它们的原因。

### 何时开启

如果您使用的模型不在默认自动列表中，并且注意到它经常描述它*会*做什么而不是实际做，设置 `tool_use_enforcement: true` 或将模型子字符串添加到列表中：

```yaml
agent:
  tool_use_enforcement: ["gpt", "codex", "gemini", "grok", "my-custom-model"]
```

## TTS 配置

```yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "neutts"
  speed: 1.0                    # 全局速度乘数（所有提供商的回退）
  edge:
    voice: "en-US-AriaNeural"   # 322 个声音，74 种语言
    speed: 1.0                  # 速度乘数（转换为速率百分比，例如 1.5 → +50%）
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    speed: 1.0                  # 速度乘数（API 限制为 0.25–4.0）
    base_url: "https://api.openai.com/v1"  # OpenAI 兼容 TTS 端点的覆盖
  minimax:
    speed: 1.0                  # 语音速度乘数
    # base_url: ""              # 可选：OpenAI 兼容 TTS 端点的覆盖
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

这控制 `text_to_speech` 工具和语音模式下的语音回复（CLI 或消息网关中的 `/voice tts`）。

**速度回退层次结构：** 提供商特定速度（例如 `tts.edge.speed`）→ 全局 `tts.speed` → `1.0` 默认值。设置全局 `tts.speed` 以在所有提供商中应用统一速度，或按提供商覆盖以进行细粒度控制。

## 显示设置

```yaml
display:
  tool_progress: all      # off | new | all | verbose
  tool_progress_command: false  # 在消息网关中启用 /verbose 斜杠命令
  tool_progress_overrides: {}  # 每个平台的覆盖（见下文）
  interim_assistant_messages: true  # 网关：将自然的中途助手更新作为单独消息发送
  skin: default           # 内置或自定义 CLI 皮肤（见 user-guide/features/skins）
  personality: "kawaii"  # 仍在某些摘要中显示的遗留装饰字段
  compact: false          # 紧凑输出模式（更少空白）
  resume_display: full    # full（在恢复时显示先前消息）| minimal（仅一行）
  bell_on_complete: false # 代理完成时播放终端铃声（对长任务很有用）
  show_reasoning: false   # 在每个响应上方显示模型推理/思考（使用 /reasoning show|hide 切换）
  streaming: false        # 实时将令牌流式传输到终端（实时输出）
  show_cost: false        # 在 CLI 状态栏中显示估计的 $ 成本
  tool_preview_length: 0  # 工具调用预览的最大字符数（0 = 无限制，显示完整路径/命令）
```

| 模式 | 您看到的内容 |
|------|-------------|
| `off` | 静默 — 只有最终响应 |
| `new` | 仅当工具更改时显示工具指示器 |
| `all` | 每个工具调用都有简短预览（默认） |
| `verbose` | 完整参数、结果和调试日志 |

在 CLI 中，使用 `/verbose` 循环这些模式。要在消息平台（Telegram、Discord、Slack 等）中使用 `/verbose`，在上面的 `display` 部分中设置 `tool_progress_command: true`。该命令将循环模式并保存到配置。

### 每个平台的进度覆盖

不同平台有不同的详细程度需求。例如，Signal 无法编辑消息，因此每个进度更新都会成为单独的消息 — 嘈杂。使用 `tool_progress_overrides` 设置每个平台的模式：

```yaml
display:
  tool_progress: all          # 全局默认值
  tool_progress_overrides:
    signal: 'off'             # 在 Signal 上静音进度
    telegram: verbose         # 在 Telegram 上详细进度
    slack: 'off'              # 在共享 Slack 工作区中保持安静
```

没有覆盖的平台回退到全局 `tool_progress` 值。有效的平台键：`telegram`、`discord`、`slack`、`signal`、`whatsapp`、`matrix`、`mattermost`、`email`、`sms`、`homeassistant`、`dingtalk`、`feishu`、`wecom`、`weixin`、`bluebubbles`、`qqbot`。

`interim_assistant_messages` 仅适用于网关。启用后，Hermes 将完成的中途助手更新作为单独的聊天消息发送。这独立于 `tool_progress`，不需要网关流式传输。

## 隐私

```yaml
privacy:
  redact_pii: false  # 从 LLM 上下文中删除 PII（仅网关）
```

当 `redact_pii` 为 `true` 时，网关在支持的平台上将个人身份信息从系统提示中删除，然后再将其发送到 LLM：

| 字段 | 处理方式 |
|-------|-----------|
| 电话号码（WhatsApp/Signal 上的用户 ID） | 哈希为 `user_<12-char-sha256>` |
| 用户 ID | 哈希为 `user_<12-char-sha256>` |
| 聊天 ID | 数字部分哈希，平台前缀保留（`telegram:<hash>`） |
| 家庭频道 ID | 数字部分哈希 |
| 用户名 / 用户名 | **不受影响**（用户选择，公开可见） |

**平台支持：** 编辑适用于 WhatsApp、Signal 和 Telegram。Discord 和 Slack 被排除，因为它们的提及系统（`<@user_id>`）需要 LLM 上下文中的真实 ID。

哈希是确定性的 — 同一用户始终映射到相同的哈希，因此模型仍然可以区分群聊中的用户。路由和传递在内部使用原始值。

## 语音转文本 (STT)

```yaml
stt:
  provider: "local"            # "local" | "groq" | "openai" | "mistral"
  local:
    model: "base"              # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"         # whisper-1 | gpt-4o-mini-transcribe | gpt-4o-transcribe
  # model: "whisper-1"         # 仍受尊重的遗留回退键
```

提供商行为：

- `local` 使用在您的机器上运行的 `faster-whisper`。使用 `pip install faster-whisper` 单独安装它。
- `groq` 使用 Groq 的 Whisper 兼容端点并读取 `GROQ_API_KEY`。
- `openai` 使用 OpenAI 语音 API 并读取 `VOICE_TOOLS_OPENAI_KEY`。

如果请求的提供商不可用，Hermes 会按以下顺序自动回退：`local` → `groq` → `openai`。

Groq 和 OpenAI 模型覆盖由环境驱动：

```bash
STT_GROQ_MODEL=whisper-large-v3-turbo
STT_OPENAI_MODEL=whisper-1
GROQ_BASE_URL=https://api.groq.com/openai/v1
STT_OPENAI_BASE_URL=https://api.openai.com/v1
```

## 语音模式 (CLI)

```yaml
voice:
  record_key: "ctrl+b"         # CLI 内的按键通话键
  max_recording_seconds: 120    # 长录音的硬停止
  auto_tts: false               # 启用 /voice on 时自动启用语音回复
  silence_threshold: 200        # 语音检测的 RMS 阈值
  silence_duration: 3.0         # 自动停止前的静音秒数
```

使用 CLI 中的 `/voice on` 启用麦克风模式，`record_key` 开始/停止录音，`/voice tts` 切换语音回复。有关端到端设置和平台特定行为，请参阅 [Voice Mode](/docs/user-guide/features/voice-mode)。

## 流式传输

将令牌实时流式传输到终端或消息平台，而不是等待完整响应。

### CLI 流式传输

```yaml
display:
  streaming: true         # 实时将令牌流式传输到终端
  show_reasoning: true    # 也流式传输推理/思考令牌（可选）
```

启用后，响应会在流式框内逐令牌出现。工具调用仍被静默捕获。如果提供商不支持流式传输，它会自动回退到正常显示。

### 网关流式传输 (Telegram, Discord, Slack)

```yaml
streaming:
  enabled: true           # 启用渐进式消息编辑
  transport: edit         # "edit"（渐进式消息编辑）或 "off"
  edit_interval: 0.3      # 消息编辑之间的秒数
  buffer_threshold: 40    # 强制编辑刷新之前的字符数
  cursor: " ▉"            # 流式传输期间显示的光标
```

启用后，机器人在第一个令牌上发送消息，然后随着更多令牌的到达逐渐编辑它。不支持消息编辑的平台（Signal、Email、Home Assistant）在第一次尝试时会被自动检测 — 流式传输会为该会话优雅地禁用，不会有消息泛滥。

要在没有渐进式令牌编辑的情况下单独发送自然的中途助手更新，请设置 `display.interim_assistant_messages: true`。

**溢出处理：** 如果流式文本超过平台的消息长度限制（~4096 字符），当前消息会被完成并自动开始新消息。

:::note
流式传输默认禁用。在 `~/.hermes/config.yaml` 中启用它以尝试流式传输 UX。
:::

## 群聊会话隔离

控制共享聊天是每个房间保持一个对话还是每个参与者保持一个对话：

```yaml
group_sessions_per_user: true  # true = 群组/频道中的每用户隔离，false = 每个聊天一个共享会话
```

- `true` 是默认和推荐设置。在 Discord 频道、Telegram 群组、Slack 频道和类似的共享上下文中，当平台提供用户 ID 时，每个发送者都会获得自己的会话。
- `false` 恢复到旧的共享房间行为。如果您明确希望 Hermes 将频道视为一个协作对话，这可能很有用，但这也意味着用户共享上下文、令牌成本和中断状态。
- 直接消息不受影响。Hermes 仍然像往常一样通过聊天/DM ID 为 DM 键。
- 无论哪种方式，线程都与父频道隔离；使用 `true`，每个参与者在线程内也会获得自己的会话。

有关行为详细信息和示例，请参阅 [Sessions](/docs/user-guide/sessions) 和 [Discord 指南](/docs/user-guide/messaging/discord)。

## 未授权 DM 行为

控制 Hermes 在未知用户发送直接消息时的行为：

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `pair` 是默认值。Hermes 拒绝访问，但在 DM 中回复一次性配对代码。
- `ignore` 静默丢弃未授权的 DM。
- 平台部分覆盖全局默认值，因此您可以广泛启用配对，同时使一个平台更安静。

## 快速命令

定义无需调用 LLM 即可运行 shell 命令的自定义命令 — 零令牌使用，即时执行。在消息平台（Telegram、Discord 等）上特别有用，用于快速服务器检查或实用脚本。

```yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  disk:
    type: exec
    command: df -h /
  update:
    type: exec
    command: cd ~/.hermes/hermes-agent && git pull && pip install -e .
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader
```

用法：在 CLI 或任何消息平台中输入 `/status`、`/disk`、`/update` 或 `/gpu`。命令在主机上本地运行并直接返回输出 — 无 LLM 调用，无令牌消耗。

- **30 秒超时** — 长时间运行的命令会被终止并显示错误消息
- **优先级** — 快速命令在技能命令之前检查，因此您可以覆盖技能名称
- **自动完成** — 快速命令在调度时解析，不会显示在内置斜杠命令自动完成表中
- **类型** — 仅支持 `exec`（运行 shell 命令）；其他类型显示错误
- **无处不在** — CLI、Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant

## 人类延迟

在消息平台中模拟人类般的响应节奏：

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 800                  # 最小延迟（自定义模式）
  max_ms: 2500                 # 最大延迟（自定义模式）
```

## 代码执行

配置沙盒 Python 代码执行工具：

```yaml
code_execution:
  timeout: 300                 # 最大执行时间（秒）
  max_tool_calls: 50           # 代码执行中的最大工具调用次数
```

## 网络搜索后端

`web_search`、`web_extract` 和 `web_crawl` 工具支持四个后端提供商。在 `config.yaml` 或通过 `hermes tools` 配置后端：

```yaml
web:
  backend: firecrawl    # firecrawl | parallel | tavily | exa
```

| 后端 | 环境变量 | 搜索 | 提取 | 爬取 |
|---------|---------|--------|---------|-------|
| **Firecrawl**（默认） | `FIRECRAWL_API_KEY` | ✔ | ✔ | ✔ |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | — |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | ✔ |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | — |

**后端选择：** 如果未设置 `web.backend`，后端会从可用的 API 密钥自动检测。如果仅设置了 `EXA_API_KEY`，则使用 Exa。如果仅设置了 `TAVILY_API_KEY`，则使用 Tavily。如果仅设置了 `PARALLEL_API_KEY`，则使用 Parallel。否则，Firecrawl 是默认值。

**自托管 Firecrawl：** 设置 `FIRECRAWL_API_URL` 指向您自己的实例。当设置了自定义 URL 时，API 密钥变为可选（在服务器上设置 `USE_DB_AUTHENTICATION=false` 以禁用身份验证）。

**Parallel 搜索模式：** 设置 `PARALLEL_SEARCH_MODE` 控制搜索行为 — `fast`、`one-shot` 或 `agentic`（默认：`agentic`）。

## 浏览器

配置浏览器自动化行为：

```yaml
browser:
  inactivity_timeout: 120        # 自动关闭空闲会话之前的秒数
  command_timeout: 30             # 浏览器命令的超时时间（秒）（屏幕截图、导航等）
  record_sessions: false         # 自动将会话记录为 WebM 视频到 ~/.hermes/browser_recordings/
  camofox:
    managed_persistence: false   # 当为 true 时，Camofox 会话在重启之间保持 cookie/登录
```