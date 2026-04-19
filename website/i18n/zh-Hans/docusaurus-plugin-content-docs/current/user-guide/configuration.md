---
sidebar_position: 2
title: "配置"
description: "配置 Hermes Agent — config.yaml、提供商、模型、API 密钥等"
---

# 配置

所有设置都存储在 `~/.hermes/` 目录中，便于访问。

## 目录结构

```text
~/.hermes/
├── config.yaml     # 设置（模型、终端、TTS、压缩等）
├── .env            # API 密钥和机密信息
├── auth.json       # OAuth 提供商凭据（Nous Portal 等）
├── SOUL.md         # 主要智能体身份（系统提示中的插槽 #1）
├── memories/       # 持久化内存（MEMORY.md、USER.md）
├── skills/         # 智能体创建的技能（通过 skill_manage 工具管理）
├── cron/           # 定时任务
├── sessions/       # 网关会话
└── logs/           # 日志（errors.log、gateway.log — 机密信息自动脱敏）
```

## 管理配置

```bash
hermes config              # 查看当前配置
hermes config edit         # 在编辑器中打开 config.yaml
hermes config set KEY VAL  # 设置特定值
hermes config check        # 检查缺失选项（更新后）
hermes config migrate      # 交互式添加缺失选项

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
2. **`~/.hermes/config.yaml`** — 所有非机密设置的主要配置文件
3. **`~/.hermes/.env`** — 环境变量的后备；**必需**用于机密信息（API 密钥、令牌、密码）
4. **内置默认值** — 当没有设置其他内容时的硬编码安全默认值

:::info 经验法则
机密信息（API 密钥、机器人令牌、密码）放在 `.env` 中。其他所有内容（模型、终端后端、压缩设置、内存限制、工具集）放在 `config.yaml` 中。当两者都设置时，`config.yaml` 对非机密设置具有优先权。
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

单个值中的多个引用有效：`url: "${HOST}:${PORT}"`。如果引用的变量未设置，占位符将保持原样（`${UNDEFINED_VAR}` 保持不变）。仅支持 `${VAR}` 语法 — 裸 `$VAR` 不会被展开。

有关 AI 提供商设置（OpenRouter、Anthropic、Copilot、自定义端点、自托管 LLM、备用模型等），请参阅 [AI 提供商](/docs/integrations/providers)。

## 终端后端配置

Hermes 支持六种终端后端。每种决定了智能体的 shell 命令实际执行的位置 — 您的本地机器、Docker 容器、通过 SSH 的远程服务器、Modal 云沙盒、Daytona 工作区或 Singularity/Apptainer 容器。

```yaml
terminal:
  backend: local    # local | docker | ssh | modal | daytona | singularity
  cwd: "."          # 工作目录（"." = 本地当前目录，容器为 "/root"）
  timeout: 180      # 每个命令的超时时间（秒）
  env_passthrough: []  # 要转发到沙盒化执行的环境变量名称（终端 + execute_code）
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"  # Singularity 后端的容器镜像
  modal_image: "nikolaik/python-nodejs:python3.11-nodejs20"                 # Modal 后端的容器镜像
  daytona_image: "nikolaik/python-nodejs:python3.11-nodejs20"               # Daytona 后端的容器镜像
```

对于云沙盒（如 Modal 和 Daytona），`container_persistent: true` 意味着 Hermes 将尝试在沙盒重新创建时保留文件系统状态。它不保证相同的实时沙盒、PID 空间或后台进程稍后仍在运行。

### 后端概览

| 后端 | 命令运行位置 | 隔离性 | 最适合 |
|---------|-------------------|-----------|----------|
| **local** | 直接在您的机器上 | 无 | 开发、个人使用 |
| **docker** | Docker 容器 | 完整（命名空间、cap-drop） | 安全沙盒化、CI/CD |
| **ssh** | 通过 SSH 的远程服务器 | 网络边界 | 远程开发、强大硬件 |
| **modal** | Modal 云沙盒 | 完整（云虚拟机） | 临时云计算、评估 |
| **daytona** | Daytona 工作区 | 完整（云容器） | 托管云开发环境 |
| **singularity** | Singularity/Apptainer 容器 | 命名空间（--containall） | HPC 集群、共享机器 |

### 本地后端

默认设置。命令直接在您的机器上运行，没有隔离。无需特殊设置。

```yaml
terminal:
  backend: local
```

:::warning
智能体具有与您的用户帐户相同的文件系统访问权限。使用 `hermes tools` 禁用您不想要的工具，或切换到 Docker 进行沙盒化。
:::

### Docker 后端

在具有安全加固的 Docker 容器内运行命令（所有能力被丢弃、无权限提升、PID 限制）。

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_mount_cwd_to_workspace: false  # 将启动目录挂载到 /workspace
  docker_forward_env:              # 要转发到容器的环境变量名称
    - "GITHUB_TOKEN"
  docker_volumes:                  # 主机目录挂载
    - "/home/user/projects:/workspace/projects"
    - "/home/user/data:/data:ro"   # :ro 表示只读

  # 资源限制
  container_cpu: 1                 # CPU 核心数（0 = 无限制）
  container_memory: 5120           # MB（0 = 无限制）
  container_disk: 51200            # MB（需要在 XFS+pquota 上使用 overlay2）
  container_persistent: true       # 跨会话持久化 /workspace 和 /root
```

**要求：** Docker Desktop 或 Docker Engine 已安装并运行。Hermes 探测 `$PATH` 加上常见的 macOS 安装位置（`/usr/local/bin/docker`、`/opt/homebrew/bin/docker`、Docker Desktop 应用程序包）。

**容器生命周期：** 每个会话启动一个长期存在的容器（`docker run -d ... sleep 2h`）。命令通过 `docker exec` 使用登录 shell 运行。清理时，容器被停止并移除。

**安全加固：**
- `--cap-drop ALL`，仅添加回 `DAC_OVERRIDE`、`CHOWN`、`FOWNER`
- `--security-opt no-new-privileges`
- `--pids-limit 256`
- 大小受限的 tmpfs：`/tmp`（512MB）、`/var/tmp`（256MB）、`/run`（64MB）

**凭据转发：** 列在 `docker_forward_env` 中的环境变量首先从您的 shell 环境解析，然后从 `~/.hermes/.env` 解析。技能也可以声明 `required_environment_variables`，这些变量会自动合并。

### SSH 后端

通过 SSH 在远程服务器上运行命令。使用 ControlMaster 进行连接复用（5 分钟空闲保持）。默认启用持久 shell — 状态（cwd、环境变量）在命令间保持。

```yaml
terminal:
  backend: ssh
  persistent_shell: true           # 保持长期存在的 bash 会话（默认：true）
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

**工作原理：** 在初始化时使用 `BatchMode=yes` 和 `StrictHostKeyChecking=accept-new` 连接。持久 shell 在远程主机上保持单个 `bash -l` 进程存活，通过临时文件通信。需要 `stdin_data` 或 `sudo` 的命令自动回退到一次性模式。

### Modal 后端

在 [Modal](https://modal.com) 云沙盒中运行命令。每个任务获得一个具有可配置 CPU、内存和磁盘的隔离 VM。文件系统可以在会话间快照/恢复。

```yaml
terminal:
  backend: modal
  container_cpu: 1                 # CPU 核心数
  container_memory: 5120           # MB（5GB）
  container_disk: 51200            # MB（50GB）
  container_persistent: true       # 快照/恢复文件系统
```

**必需：** 要么是 `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` 环境变量，要么是 `~/.modal.toml` 配置文件。

**持久性：** 启用后，沙盒文件系统在清理时进行快照，并在下次会话时恢复。快照在 `~/.hermes/modal_snapshots.json` 中跟踪。这保留了文件系统状态，而不是实时进程、PID 空间或后台作业。

**凭据文件：** 自动从 `~/.hermes/`（OAuth 令牌等）挂载，并在每个命令前同步。

### Daytona 后端

在 [Daytona](https://daytona.io) 托管的工作区中运行命令。支持停止/恢复以实现持久性。

```yaml
terminal:
  backend: daytona
  container_cpu: 1                 # CPU 核心数
  container_memory: 5120           # MB → 转换为 GiB
  container_disk: 10240            # MB → 转换为 GiB（最大 10 GiB）
  container_persistent: true       # 停止/恢复而不是删除
```

**必需：** `DAYTONA_API_KEY` 环境变量。

**持久性：** 启用后，沙盒在清理时被停止（不删除），并在下次会话时恢复。沙盒名称遵循模式 `hermes-{task_id}`。

**磁盘限制：** Daytona 强制执行 10 GiB 的最大值。超过此值的请求会被限制并发出警告。

### Singularity/Apptainer 后端

在 [Singularity/Apptainer](https://apptainer.org) 容器中运行命令。专为 HPC 集群和共享机器设计，这些地方 Docker 不可用。

```yaml
terminal:
  backend: singularity
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"
  container_cpu: 1                 # CPU 核心数
  container_memory: 5120           # MB
  container_persistent: true       # 可写覆盖层在会话间持久化
```

**要求：** `apptainer` 或 `singularity` 二进制文件在 `$PATH` 中。

**镜像处理：** Docker URL（`docker://...`）自动转换为 SIF 文件并缓存。现有的 `.sif` 文件直接使用。

**临时目录：** 按顺序解析：`TERMINAL_SCRATCH_DIR` → `TERMINAL_SANDBOX_DIR/singularity` → `/scratch/$USER/hermes-agent`（HPC 约定）→ `~/.hermes/sandboxes/singularity`。

**隔离：** 使用 `--containall --no-home` 实现完整的命名空间隔离，不挂载主机主目录。

### 常见终端后端问题

如果终端命令立即失败或终端工具报告为禁用：

- **Local** — 无特殊要求。开始使用时的最安全默认值。
- **Docker** — 运行 `docker version` 验证 Docker 是否正常工作。如果失败，修复 Docker 或 `hermes config set terminal.backend local`。
- **SSH** — `TERMINAL_SSH_HOST` 和 `TERMINAL_SSH_USER` 都必须设置。如果缺少任一，Hermes 会记录清晰的错误。
- **Modal** — 需要 `MODAL_TOKEN_ID` 环境变量或 `~/.modal.toml`。运行 `hermes doctor` 检查。
- **Daytona** — 需要 `DAYTONA_API_KEY`。Daytona SDK 处理服务器 URL 配置。
- **Singularity** — 需要 `apptainer` 或 `singularity` 在 `$PATH` 中。在 HPC 集群上常见。

有疑问时，将 `terminal.backend` 设置回 `local` 并首先验证命令在那里运行。

### Docker 卷挂载

使用 Docker 后端时，`docker_volumes` 允许您与容器共享主机目录。每个条目使用标准 Docker `-v` 语法：`host_path:container_path[:options]`。

```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/home/user/projects:/workspace/projects"   # 读写（默认）
    - "/home/user/datasets:/data:ro"              # 只读
    - "/home/user/outputs:/outputs"               # 智能体写入，您读取
```

这适用于：
- **向智能体提供文件**（数据集、配置、参考代码）
- **从智能体接收文件**（生成的代码、报告、导出）
- **共享工作区**，您和智能体都可以访问相同的文件

也可以通过环境变量设置：`TERMINAL_DOCKER_VOLUMES='["/host:/container"]'`（JSON 数组）。

### Docker 凭据转发

默认情况下，Docker 终端会话不继承任意主机凭据。如果您需要在容器内使用特定令牌，请将其添加到 `terminal.docker_forward_env`。

```yaml
terminal:
  backend: docker
  docker_forward_env:
    - "GITHUB_TOKEN"
    - "NPM_TOKEN"
```

Hermes 首先从您当前的 shell 解析每个列出的变量，然后如果使用 `hermes config set` 保存，则回退到 `~/.hermes/.env`。

:::warning
列在 `docker_forward_env` 中的任何内容都会对容器内运行的命令可见。仅转发您愿意暴露给终端会话的凭据。
:::

### 可选：将启动目录挂载到 `/workspace`

默认情况下，Docker 沙盒保持隔离。除非您明确选择加入，否则 Hermes **不会**将您当前的主机工作目录传递到容器中。

在 `config.yaml` 中启用：

```yaml
terminal:
  backend: docker
  docker_mount_cwd_to_workspace: true
```

启用时：
- 如果您从 `~/projects/my-app` 启动 Hermes，该主机目录将绑定挂载到 `/workspace`
- Docker 后端在 `/workspace` 中启动
- 文件工具和终端命令都看到相同的挂载项目

禁用时，`/workspace` 保持沙盒所有，除非您通过 `docker_volumes` 显式挂载某些内容。

安全权衡：
- `false` 保留沙盒边界
- `true` 让沙盒直接访问您启动 Hermes 的目录

仅在您有意希望容器处理实时主机文件时使用选择加入。

### 持久 Shell

默认情况下，每个终端命令在自己的子进程中运行 — 工作目录、环境变量和 shell 变量在命令间重置。当启用**持久 shell**时，单个长期存在的 bash 进程在 `execute()` 调用间保持存活，以便状态在命令间保持。

这对于**SSH 后端**最有用，它还消除了每个命令的连接开销。持久 shell **默认对 SSH 启用**，对本地后端禁用。

```yaml
terminal:
  persistent_shell: true   # 默认 — 为 SSH 启用持久 shell
```

要禁用：

```bash
hermes config set terminal.persistent_shell false
```

**在命令间保持的内容：**
- 工作目录（`cd /tmp` 对下一个命令保持）
- 导出的环境变量（`export FOO=bar`）
- Shell 变量（`MY_VAR=hello`）

**优先级：**

| 级别 | 变量 | 默认值 |
|-------|----------|---------|
| 配置 | `terminal.persistent_shell` | `true` |
| SSH 覆盖 | `TERMINAL_SSH_PERSISTENT` | 遵循配置 |
| 本地覆盖 | `TERMINAL_LOCAL_PERSISTENT` | `false` |

每个后端的环境变量具有最高优先级。如果您也想在本地后端启用持久 shell：

```bash
export TERMINAL_LOCAL_PERSISTENT=true
```

:::note
需要 `stdin_data` 或 sudo 的命令自动回退到一次性模式，因为持久 shell 的 stdin 已被 IPC 协议占用。
:::

有关每个后端的详细信息，请参阅[代码执行](features/code-execution.md)和 README 的[终端部分](features/tools.md)。

## 技能设置

技能可以通过其 SKILL.md 前置声明自己的配置设置。这些是非机密值（路径、偏好、域设置），存储在 `config.yaml` 中的 `skills.config` 命名空间下。

```yaml
skills:
  config:
    wiki:
      path: ~/wiki          # 由 llm-wiki 技能使用
```

**技能设置工作原理：**

- `hermes config migrate` 扫描所有启用的技能，找到未配置的设置，并提供提示您
- `hermes config show` 在"技能设置"下显示所有技能设置及其所属技能
- 当技能加载时，其解析的配置值会自动注入到技能上下文中

**手动设置值：**

```bash
hermes config set skills.config.wiki.path ~/my-research-wiki
```

有关在您自己的技能中声明配置设置的详细信息，请参阅[创建技能 — 配置设置](/docs/developer-guide/creating-skills#config-settings-configyaml)。

## 内存配置

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```

## 文件读取安全

控制单个 `read_file` 调用可以返回多少内容。超过限制的读取会被拒绝，并提示智能体使用 `offset` 和 `limit` 获取较小范围。这可以防止单个读取压缩的 JS 包或大型数据文件淹没上下文窗口。

```yaml
file_read_max_chars: 100000  # 默认 — ~25-35K tokens
```

如果您使用具有大上下文窗口的模型并经常读取大文件，请提高此值。对于小上下文模型，降低此值以保持读取效率：

```yaml
# 大上下文模型（200K+）
file_read_max_chars: 200000

# 小本地模型（16K 上下文）
file_read_max_chars: 30000
```

智能体还会自动去重文件读取 — 如果同一文件区域被读取两次且文件未更改，则返回轻量级存根而不是重新发送内容。这在上下文压缩时重置，因此智能体可以在其内容被摘要后重新读取文件。

## Git 工作树隔离

启用隔离的 git 工作树，以便在同一仓库上并行运行多个智能体：

```yaml
worktree: true    # 始终创建工作树（与 hermes -w 相同）
# worktree: false # 默认 — 仅在传递 -w 标志时
```

启用后，每个 CLI 会话会在 `.worktrees/` 下创建一个具有自己分支的新工作树。智能体可以编辑文件、提交、推送和创建 PR，而不会相互干扰。干净的工作树在退出时被移除；脏的工作树保留用于手动恢复。

您还可以通过仓库根目录中的 `.worktreeinclude` 列出要复制到工作树中的 gitignored 文件：

```
# .worktreeinclude
.env
.venv/
node_modules/
```

## 上下文压缩

Hermes 自动压缩长对话以保持在您模型的上下文窗口内。压缩摘要器是一个单独的 LLM 调用 — 您可以将其指向任何提供商或端点。

所有压缩设置都在 `config.yaml` 中（无环境变量）。

### 完整参考

```yaml
compression:
  enabled: true                                     # 切换压缩开/关
  threshold: 0.50                                   # 在此 % 的上下文限制处压缩
  target_ratio: 0.20                                # 保留为最近尾部的阈值分数
  protect_last_n: 20                                # 保持未压缩的最小最近消息数

# 摘要模型/提供商在 auxiliary 下配置：
auxiliary:
  compression:
    model: "google/gemini-3-flash-preview"          # 用于摘要的模型
    provider: "auto"                                # 提供商："auto"、"openrouter"、"nous"、"codex"、"main" 等
    base_url: null                                  # 自定义 OpenAI 兼容端点（覆盖提供商）
```

:::info 旧配置迁移
具有 `compression.summary_model`、`compression.summary_provider` 和 `compression.summary_base_url` 的旧配置在首次加载时自动迁移到 `auxiliary.compression.*`（配置版本 17）。无需手动操作。
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
指向自定义 OpenAI 兼容端点。使用 `OPENAI_API_KEY` 进行认证。

### How the three knobs interact

| `auxiliary.compression.provider` | `auxiliary.compression.base_url` | Result |
|---------------------|---------------------|--------|
| `auto` (default) | not set | Auto-detect best available provider |
| `nous` / `openrouter` / etc. | not set | Force that provider, use its auth |
| any | set | Use the custom endpoint directly (provider ignored) |

:::warning Summary model context length requirement
摘要模型**必须**具有至少与您主智能体模型一样大的上下文窗口。压缩器将对话的完整中间部分发送到摘要模型 — 如果该模型的上下文窗口小于主模型的，摘要调用将因上下文长度错误而失败。发生这种情况时，中间轮次**会在没有摘要的情况下被丢弃**，静默丢失对话上下文。如果您覆盖了模型，请验证其上下文长度是否满足或超过您主模型的。
:::

## Context Engine

上下文引擎控制接近模型令牌限制时对话的管理方式。内置的 `compressor` 引擎使用有损摘要（请参阅[上下文压缩](/docs/developer-guide/context-compression-and-caching)）。插件引擎可以用替代策略替换它。

```yaml
context:
  engine: "compressor"    # 默认 — 内置有损摘要
```

要使用插件引擎（例如，用于无损上下文管理的 LCM）：

```yaml
context:
  engine: "lcm"          # 必须与插件名称匹配
```

插件引擎**永远不会自动激活** — 您必须明确设置 `context.engine` 为插件名称。可用的引擎可以通过 `hermes plugins` → Provider Plugins → Context Engine 浏览和选择。

请参阅[记忆提供商](/docs/user-guide/features/memory-providers) 了解类似的记忆插件单选系统。

## Iteration Budget Pressure

当智能体正在处理具有许多工具调用的复杂任务时，它可能会在不知不觉中耗尽其迭代预算（默认：90 轮）。预算压力会在接近限制时自动警告模型：

| 阈值 | 级别 | 模型看到的内容 |
|---------|-------|---------------------|
| **70%** | 谨慎 | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | 警告 | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |

警告被注入到最后一个工具结果的 JSON 中（作为 `_budget_warning` 字段）而不是作为单独的消息 — 这保留了提示缓存并不会破坏对话结构。

```yaml
agent:
  max_turns: 90                # 每次对话轮次的最大迭代次数（默认：90）
```

预算压力默认启用。智能体会自然地将警告视为工具结果的一部分，鼓励它在迭代耗尽之前整合工作并交付响应。

当迭代预算完全耗尽时，CLI 会向用户显示通知：`⚠ Iteration budget reached (90/90) — response may be incomplete`。如果预算在积极工作期间耗尽，智能体会生成所完成工作的摘要，然后停止。

### 流式传输超时

LLM 流式传输连接有两层超时。两者都会为本地提供商（localhost、LAN IP）自动调整 — 大多数设置不需要配置。

| 超时 | 默认 | 本地提供商 | 环境变量 |
|---------|---------|----------------|---------|
| 套接字读取超时 | 120s | 自动提高到 1800s | `HERMES_STREAM_READ_TIMEOUT` |
| Stale stream detection | 180s | Auto-disabled | `HERMES_STREAM_STALE_TIMEOUT` |
| API call (non-streaming) | 1800s | Unchanged | `HERMES_API_TIMEOUT` |

The **socket read timeout** controls how long httpx waits for the next chunk of data from the provider. Local LLMs can take minutes for prefill on large contexts before producing the first token, so Hermes raises this to 30 minutes when it detects a local endpoint. If you explicitly set `HERMES_STREAM_READ_TIMEOUT`, that value is always used regardless of endpoint detection.

The **stale stream detection** kills connections that receive SSE keep-alive pings but no actual content. This is disabled entirely for local providers since they don't send keep-alive pings during prefill.

## Context Pressure Warnings

Separate from iteration budget pressure, context pressure tracks how close the conversation is to the **compaction threshold** — the point where context compression fires to summarize older messages. This helps both you and the agent understand when the conversation is getting long.

| Progress | Level | What happens |
|----------|-------|-------------|
| **≥ 60%** to threshold | Info | CLI shows a cyan progress bar; gateway sends an informational notice |
| **≥ 85%** to threshold | Warning | CLI shows a bold yellow bar; gateway warns compaction is imminent |

In the CLI, context pressure appears as a progress bar in the tool output feed:

```
  ◐ context ████████████░░░░░░░░ 62% to compaction  48k threshold (50%) · approaching compaction
```

On messaging platforms, a plain-text notification is sent:

```
◐ Context: ████████████░░░░░░░░ 62% to compaction (threshold: 50% of window).
```

如果自动压缩被禁用，警告会告诉您上下文可能会被截断。

上下文压力是自动的 — 无需配置。它纯粹作为面向用户的通知触发，不会修改消息流或向模型的上下文中注入任何内容。

## 凭据池策略

当您有多个相同提供商的 API 密钥或 OAuth 令牌时，配置轮换策略：

```yaml
credential_pool_strategies:
  openrouter: round_robin    # 均匀循环使用密钥
  anthropic: least_used      # 总是选择使用最少的密钥
```

选项：`fill_first`（默认）、`round_robin`、`least_used`、`random`。完整文档请参阅[凭据池](/docs/user-guide/features/credential-pools)。

## 辅助模型

Hermes 使用轻量级"辅助"模型来处理图像分析、网页摘要和浏览器截图分析等辅助任务。默认情况下，这些通过自动检测使用**Gemini Flash** — 您无需配置任何内容。

### 通用配置模式

Hermes 中的每个模型插槽 — 辅助任务、压缩、备用 — 都使用相同的三个控制旋钮：

| 键 | 作用 | 默认值 |
|-----|-------------|---------|
| `provider` | 用于认证和路由的提供商 | `"auto"` |
| `model` | 请求的模型 | 提供商的默认值 |
| `base_url` | 自定义 OpenAI 兼容端点（覆盖提供商） | 未设置 |

当设置 `base_url` 时，Hermes 忽略提供商并直接调用该端点（使用 `api_key` 或 `OPENAI_API_KEY` 进行认证）。当仅设置 `provider` 时，Hermes 使用该提供商的内置认证和基础 URL。

辅助任务的可用提供商：`auto`、`openrouter`、`nous`、`codex`、`copilot`、`anthropic`、`main`、`zai`、`kimi-coding`、`kimi-coding-cn`、`arcee`、`minimax`、[提供商注册表](/docs/reference/environment-variables)中注册的任何提供商，或来自您的 `custom_providers` 列表的任何命名自定义提供商（例如 `provider: "beans"`）。

:::warning `"main"` 仅用于辅助任务
`"main"` 提供商选项意味着"使用我的主智能体使用的任何提供商" — 它仅在 `auxiliary:`、`compression:` 和 `fallback_model:` 配置中有效。它不是您顶级 `model.provider` 设置的有效值。如果您使用自定义 OpenAI 兼容端点，请在 `model:` 部分设置 `provider: custom`。所有主模型提供商选项请参阅 [AI 提供商](/docs/integrations/providers)。
:::

### 完整辅助配置参考

```yaml
auxiliary:
  # 图像分析（vision_analyze 工具 + 浏览器截图）
  vision:
    provider: "auto"           # "auto"、"openrouter"、"nous"、"codex"、"main" 等
    model: ""                  # 例如 "openai/gpt-4o"、"google/gemini-2.5-flash"
    base_url: ""               # 自定义 OpenAI 兼容端点（覆盖提供商）
    api_key: ""                # base_url 的 API 密钥（回退到 OPENAI_API_KEY）
    timeout: 120               # 秒 — LLM API 调用超时；视觉负载需要宽松的超时
    download_timeout: 30       # 秒 — 图像 HTTP 下载；为慢速连接增加

  # 网页摘要 + 浏览器页面文本提取
  web_extract:
    provider: "auto"
    model: ""                  # 例如 "google/gemini-2.5-flash"
    base_url: ""
    api_key: ""
    timeout: 360               # 秒（6分钟）— 每次尝试的 LLM 摘要

  # 危险命令批准分类器
  approval:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30                # 秒

  # 上下文压缩超时（与 compression.* 配置分开）
  compression:
    timeout: 120               # 秒 — 压缩摘要长对话，需要更多时间

  # 会话搜索 — 摘要过去的会话匹配
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

  # MCP 工具分发
  mcp:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30

  # 内存刷新 — 为持久化内存摘要对话
  flush_memories:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30
```

:::tip
每个辅助任务都有可配置的 `timeout`（以秒为单位）。默认值：vision 120秒、web_extract 360秒、approval 30秒、compression 120秒。如果您为辅助任务使用慢速本地模型，请增加这些值。Vision 还有一个单独的 `download_timeout`（默认 30秒）用于 HTTP 图像下载 — 为慢速连接或自托管图像服务器增加此值。
:::

:::info
上下文压缩有自己的 `compression:` 块用于阈值，以及 `auxiliary.compression:` 块用于模型/提供商设置 — 请参阅上面的[上下文压缩](#context-compression)。备用模型使用 `fallback_model:` 块 — 请参阅[备用模型](/docs/integrations/providers#fallback-model)。所有三个都遵循相同的 provider/model/base_url 模式。
:::

### 更改 Vision 模型

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

这些选项适用于**辅助任务配置**（`auxiliary:`、`compression:`、`fallback_model:`），而不是您的主 `model.provider` 设置。

| 提供商 | 描述 | 要求 |
|----------|-------------|-------------|
| `"auto"` | 最佳可用（默认）。Vision 尝试 OpenRouter → Nous → Codex。 | — |
| `"openrouter"` | 强制 OpenRouter — 路由到任何模型（Gemini、GPT-4o、Claude 等） | `OPENROUTER_API_KEY` |
| `"nous"` | 强制 Nous Portal | `hermes auth` |
| `"codex"` | 强制 Codex OAuth（ChatGPT 帐户）。支持 vision（gpt-5.3-codex）。 | `hermes model` → Codex |
| `"main"` | 使用您活动的自定义/主端点。这可以来自 `OPENAI_BASE_URL` + `OPENAI_API_KEY` 或通过 `hermes model` / `config.yaml` 保存的自定义端点。适用于 OpenAI、本地模型或任何 OpenAI 兼容 API。**仅用于辅助任务 — 对 `model.provider` 无效。** | 自定义端点凭据 + 基础 URL |

### 常见设置

**使用直接自定义端点**（比 `provider: "main"` 更清晰，适用于本地/自托管 API）：
```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` 优先于 `provider`，因此这是将辅助任务路由到特定端点的最明确方式。对于直接端点覆盖，Hermes 使用配置的 `api_key` 或回退到 `OPENAI_API_KEY`；它不会为该自定义端点重用 `OPENROUTER_API_KEY`。

**使用 OpenAI API 密钥进行 vision：**
```yaml
# 在 ~/.hermes/.env 中：
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # 或 "gpt-4o-mini" 更便宜
```

**使用 OpenRouter 进行 vision**（路由到任何模型）：
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # 或 "google/gemini-2.5-flash" 等
```

**使用 Codex OAuth**（ChatGPT Pro/Plus 帐户 — 无需 API 密钥）：
```yaml
auxiliary:
  vision:
    provider: "codex"     # 使用您的 ChatGPT OAuth 令牌
    # model 默认为 gpt-5.3-codex（支持 vision）
```

**使用本地/自托管模型：**
```yaml
auxiliary:
  vision:
    provider: "main"      # 使用您活动的自定义端点
    model: "my-local-model"
```

`provider: "main"` 使用 Hermes 用于正常聊天的任何提供商 — 无论是命名自定义提供商（例如 `beans`）、内置提供商如 `openrouter`，还是遗留的 `OPENAI_BASE_URL` 端点。

:::tip
如果您使用 Codex OAuth 作为您的主模型提供商，vision 会自动工作 — 无需额外配置。Codex 包含在 vision 的自动检测链中。
:::

:::warning
**Vision 需要多模态模型。**如果您设置 `provider: "main"`，请确保您的端点支持多模态/vision — 否则图像分析将失败。
:::

### Environment Variables (legacy)

Auxiliary models can also be configured via environment variables. However, `config.yaml` is the preferred method — it's easier to manage and supports all options including `base_url` and `api_key`.

| Setting | Environment Variable |
|---------|---------------------|
| Vision provider | `AUXILIARY_VISION_PROVIDER` |
| Vision model | `AUXILIARY_VISION_MODEL` |
| Vision endpoint | `AUXILIARY_VISION_BASE_URL` |
| Vision API key | `AUXILIARY_VISION_API_KEY` |
| Web extract provider | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Web extract model | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Web extract endpoint | `AUXILIARY_WEB_EXTRACT_BASE_URL` |
| Web extract API key | `AUXILIARY_WEB_EXTRACT_API_KEY` |

Compression and fallback model settings are config.yaml-only.

:::tip
运行 `hermes config` 查看您当前的辅助模型设置。覆盖只在与默认值不同时才会显示。
:::

## Reasoning Effort

控制模型在响应之前进行多少"思考"：

```yaml
agent:
  reasoning_effort: ""   # 空 = medium（默认）。选项：none、minimal、low、medium、high、xhigh（最大）
```

当未设置（默认）时，推理努力默认为"medium" — 一个对大多数任务都有效的平衡级别。设置一个值会覆盖它 — 更高的推理努力会在复杂任务上给出更好的结果，但代价是更多的令牌和延迟。

您也可以在运行时使用 `/reasoning` 命令更改推理努力：

```
/reasoning           # 显示当前努力级别和显示状态
/reasoning high      # 将推理努力设置为高
/reasoning none      # 禁用推理
/reasoning show      # 在每个响应上方显示模型思考
/reasoning hide      # 隐藏模型思考
```

## Tool-Use Enforcement

一些模型偶尔会将预期动作描述为文本而不是进行工具调用（"我会运行测试..."而不是真正调用终端）。工具使用强制注入系统提示引导，将模型重新引导到实际调用工具。

```yaml
agent:
  tool_use_enforcement: "auto"   # "auto" | true | false | ["model-substring", ...]
```

| 值 | 行为 |
|-------|----------|
| `"auto"`（默认） | 对匹配的模型启用：`gpt`、`codex`、`gemini`、`gemma`、`grok`。对所有其他模型禁用（Claude、DeepSeek、Qwen 等）。 |
| `true` | 始终启用，无论模型如何。如果您注意到当前模型描述动作而不是执行它们，这很有用。 |
| `false` | 始终禁用，无论模型如何。 |
| `["gpt", "codex", "qwen", "llama"]` | 仅当模型名称包含列出的子字符串之一时启用（不区分大小写）。 |

### 它注入的内容

启用时，三层引导可能会被添加到系统提示中：

1. **通用工具使用强制**（所有匹配的模型）— 指示模型立即进行工具调用而不是描述意图，继续工作直到任务完成，永不以承诺未来行动来结束一轮。

2. **OpenAI 执行纪律**（仅限 GPT 和 Codex 模型）— 解决 GPT 特定失败模式的额外指导：在部分结果时放弃工作、跳过先决条件查找、幻觉而不是使用工具、以及在没有验证的情况下声明"完成"。

3. **Google 操作指导**（仅限 Gemini 和 Gemma 模型）— 简洁性、绝对路径、并行工具调用和验证后编辑模式。

These are transparent to the user and only affect the system prompt. Models that already use tools reliably (like Claude) don't need this guidance, which is why `"auto"` excludes them.

### When to turn it on

If you're using a model not in the default auto list and notice it frequently describes what it *would* do instead of doing it, set `tool_use_enforcement: true` or add the model substring to the list:

```yaml
agent:
  tool_use_enforcement: ["gpt", "codex", "gemini", "grok", "my-custom-model"]
```

## TTS Configuration

```yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "neutts"
  speed: 1.0                    # Global speed multiplier (fallback for all providers)
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
    speed: 1.0                  # Speed multiplier (converted to rate percentage, e.g. 1.5 → +50%)
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    speed: 1.0                  # Speed multiplier (clamped to 0.25–4.0 by the API)
    base_url: "https://api.openai.com/v1"  # Override for OpenAI-compatible TTS endpoints
  minimax:
    speed: 1.0                  # Speech speed multiplier
    # base_url: ""              # Optional: override for OpenAI-compatible TTS endpoints
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

This controls both the `text_to_speech` tool and spoken replies in voice mode (`/voice tts` in the CLI or messaging gateway).

**速度回退层次结构：** 提供商特定速度（例如 `tts.edge.speed`）→ 全局 `tts.speed` → `1.0` 默认值。设置全局 `tts.speed` 以在所有提供商之间应用统一速度，或为每个提供商覆盖以进行细粒度控制。

## Display Settings

```yaml
display:
  tool_progress: all      # off | new | all | verbose
  tool_progress_command: false  # 在消息网关中启用 /verbose 斜杠命令
  tool_progress_overrides: {}  # 每个平台的覆盖（见下文）
  interim_assistant_messages: true  # 网关：将自然的回合中助手更新作为单独消息发送
  skin: default           # 内置或自定义 CLI 皮肤（请参阅 user-guide/features/skins）
  personality: "kawaii"  # 传统 cosmetic 字段仍在某些摘要中显示
  compact: false          # 紧凑输出模式（更少空白）
  resume_display: full    # full（恢复时显示之前消息）| minimal（仅一行）
  bell_on_complete: false # 智能体完成时播放终端铃声（非常适合长时间任务）
  show_reasoning: false   # 在每个响应上方显示模型推理/思考（使用 /reasoning show|hide 切换）
  streaming: false        # 实时将令牌流式传输到终端（实时输出）
  show_cost: false        # 在 CLI 状态栏显示估计费用
  tool_preview_length: 0  # 工具调用预览的最大字符数（0 = 无限制，显示完整路径/命令）
```

| 模式 | 您看到的内容 |
|------|-------------|
| `off` | 静默 — 仅最终响应 |
| `new` | 仅在工具更改时显示工具指示器 |
| `all` | 每个工具调用带简短预览（默认） |
| `verbose` | 完整参数、结果和调试日志 |

在 CLI 中，使用 `/verbose` 循环切换这些模式。要在消息平台（Telegram、Discord、Slack 等）中使用 `/verbose`，请在上面 的 `display` 部分设置 `tool_progress_command: true`。该命令将循环切换模式并保存到配置中。

### 每平台进度覆盖

不同的平台有不同的详细程度需求。例如，Signal 无法编辑消息，因此每个进度更新都会成为一条单独的消息 — 很吵杂。使用 `tool_progress_overrides` 设置每平台模式：

```yaml
display:
  tool_progress: all          # 全局默认
  tool_progress_overrides:
    signal: 'off'             # 在 Signal 上静音进度
    telegram: verbose         # 在 Telegram 上详细进度
    slack: 'off'              # 在共享 Slack 工作区中安静
```

没有覆盖的平台回退到全局 `tool_progress` 值。有效的平台键：`telegram`、`discord`、`slack`、`signal`、`whatsapp`、`matrix`、`mattermost`、`email`、`sms`、`homeassistant`、`dingtalk`、`feishu`、`wecom`、`weixin`、`bluebubbles`、`qqbot`。

`interim_assistant_messages` 仅限网关。当启用时，Hermes 会将完成的回合中助手更新作为单独的聊天消息发送。这独立于 `tool_progress`，不需要网关流式传输。

## Privacy

```yaml
privacy:
  redact_pii: false  # Strip PII from LLM context (gateway only)
```

当 `redact_pii` 为 `true` 时，网关会在将系统提示发送到支持的平台上的 LLM 之前，对其进行个人身份信息编辑：

| 字段 | 处理方式 |
|-------|-----------|
| 电话号码（WhatsApp/Signal 上的用户 ID）| 哈希为 `user_<12-char-sha256>` |
| 用户 ID | 哈希为 `user_<12-char-sha256>` |
| 聊天 ID | 数字部分哈希，保留平台前缀（`telegram:<hash>`）|
| 主页频道 ID | 数字部分哈希 |
| 用户名 / 用户昵称 | **不受影响**（用户选择、公开可见）|

**平台支持：** 编辑适用于 WhatsApp、Signal 和 Telegram。Discord 和 Slack 被排除，因为它们的提及系统（`<@user_id>`）需要在 LLM 上下文中使用真实 ID。

哈希是确定性的 — 同一用户始终映射到同一哈希，因此模型仍然可以区分群聊中的用户。路由和传递在内部使用原始值。

## Speech-to-Text (STT)

```yaml
stt:
  provider: "local"            # "local" | "groq" | "openai" | "mistral"
  local:
    model: "base"              # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"         # whisper-1 | gpt-4o-mini-transcribe | gpt-4o-transcribe
  # model: "whisper-1"         # 仍会识别传统回退键
```

提供商行为：

- `local` 使用在您机器上运行的 `faster-whisper`。使用 `pip install faster-whisper` 单独安装。
- `groq` 使用 Groq 的 Whisper 兼容端点并读取 `GROQ_API_KEY`。
- `openai` 使用 OpenAI 语音 API 并读取 `VOICE_TOOLS_OPENAI_KEY`。

如果请求的提供商不可用，Hermes 会按此顺序自动回退：`local` → `groq` → `openai`。

Groq 和 OpenAI 模型覆盖由环境驱动：

```bash
STT_GROQ_MODEL=whisper-large-v3-turbo
STT_OPENAI_MODEL=whisper-1
GROQ_BASE_URL=https://api.groq.com/openai/v1
STT_OPENAI_BASE_URL=https://api.openai.com/v1
```

## Voice Mode (CLI)

```yaml
voice:
  record_key: "ctrl+b"         # CLI 内的按键说话键
  max_recording_seconds: 120    # 长时间录音的硬性停止
  auto_tts: false               # 启用 /voice on 时自动启用语音回复
  silence_threshold: 200        # 语音检测的 RMS 阈值
  silence_duration: 3.0         # 自动停止前的沉默秒数
```

在 CLI 中使用 `/voice on` 启用麦克风模式，使用 `record_key` 开始/停止录音，以及使用 `/voice tts` 切换语音回复。请参阅[语音模式](/docs/user-guide/features/voice-mode) 了解端到端设置和平台特定行为。

## Streaming

将令牌流式传输到终端或消息平台，而不是等待完整响应。

### CLI 流式传输

```yaml
display:
  streaming: true         # 实时将令牌流式传输到终端
  show_reasoning: true    # 也流式传输推理/思考令牌（可选）
```

启用后，响应会在流式传输框中逐个令牌显示。工具调用仍然会被静默捕获。如果提供商不支持流式传输，它会自动回退到正常显示。

### 网关流式传输（Telegram、Discord、Slack）

```yaml
streaming:
  enabled: true           # 启用渐进式消息编辑
  transport: edit         # "edit"（渐进式消息编辑）或 "off"
  edit_interval: 0.3      # 消息编辑之间的秒数
  buffer_threshold: 40    # 强制刷新编辑前的字符数
  cursor: " ▉"            # 流式传输期间显示的光标
```

启用后，机器人在第一个令牌时发送一条消息，然后随着更多令牌的到达逐步编辑它。不支持消息编辑的平台（Signal、Email、Home Assistant）会在首次尝试时自动检测 — 该会话的流式传输会被优雅地禁用，不会产生大量消息。

要获取单独的、自然的回合中助手更新而不是渐进式令牌编辑，请设置 `display.interim_assistant_messages: true`。

**溢出处理：** 如果流式传输的文本超过平台的消息长度限制（~4096 字符），当前消息会被完成并自动开始新消息。

:::note
流式传输默认禁用。在 `~/.hermes/config.yaml` 中启用它以尝试流式传输用户体验。
:::

## Group Chat Session Isolation

控制共享聊天是每个房间保持一个对话还是每个参与者保持一个对话：

```yaml
group_sessions_per_user: true  # true = 组/频道中的按用户隔离，false = 每个聊天一个共享会话
```

- `true` 是默认和推荐设置。在 Discord 频道、Telegram 群组、Slack 频道和类似的共享上下文中，当平台提供用户 ID 时，每个发送者都会获得自己的会话。
- `false` 恢复为旧的共享房间行为。如果您明确希望 Hermes 将频道视为一次协作对话，这可能很有用，但它也意味着用户共享上下文、令牌成本和中断状态。
- 私聊不受影响。Hermes 仍然像往常一样按聊天/私聊 ID 密钥化私聊。
- 线程无论如何都会与父频道隔离；使用 `true` 时，每个参与者在线程内也有自己的会话。

有关行为详情和示例，请参阅[Sessions](/docs/user-guide/sessions)和[Discord 指南](/docs/user-guide/messaging/discord)。

## Unauthorized DM Behavior

控制当未知用户发送直接消息时 Hermes 的行为：

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `pair` 是默认设置。Hermes 拒绝访问，但在私聊中回复一次性的配对码。
- `ignore` 静默丢弃未经授权的私聊。
- 平台部分会覆盖全局默认值，因此您可以在保持广泛启用配对的同时让一个平台更安静。

## Quick Commands

定义自定义命令，无需调用 LLM 即可运行 shell 命令 — 零令牌使用，即时执行。特别适用于消息平台（Telegram、Discord 等）进行快速服务器检查或实用脚本。

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

- **30 秒超时** — 长时间运行的命令会被终止并返回错误消息
- **优先级** — 快速命令在技能命令之前检查，因此您可以覆盖技能名称
- **自动补全** — 快速命令在分发时解析，不会显示在内置斜杠命令自动补全表中
- **类型** — 仅支持 `exec`（运行 shell 命令）；其他类型会显示错误
- **随时可用** — CLI、Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant

## Human Delay

在消息平台中模拟类似人类的响应节奏：

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 800                  # 最小延迟（自定义模式）
  max_ms: 2500                 # 最大延迟（自定义模式）
```

## Code Execution

配置沙盒 Python 代码执行工具：

```yaml
code_execution:
  timeout: 300                 # 最大执行时间（秒）
  max_tool_calls: 50           # 代码执行内的最大工具调用次数
```

## Web Search Backends

`web_search`、`web_extract` 和 `web_crawl` 工具支持四个后端提供商。在 `config.yaml` 中或通过 `hermes tools` 配置后端：

```yaml
web:
  backend: firecrawl    # firecrawl | parallel | tavily | exa
```

| 后端 | 环境变量 | 搜索 | 提取 | 爬取 |
|---------|---------|--------|---------|-------|
| **Firecrawl**（默认）| `FIRECRAWL_API_KEY` | ✔ | ✔ | ✔ |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | — |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | ✔ |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | — |

**后端选择：** 如果未设置 `web.backend`，后端会从可用的 API 密钥自动检测。如果仅设置了 `EXA_API_KEY`，则使用 Exa。如果仅设置了 `TAVILY_API_KEY`，则使用 Tavily。如果仅设置了 `PARALLEL_API_KEY`，则使用 Parallel。否则默认为 Firecrawl。

**自托管 Firecrawl：** 设置 `FIRECRAWL_API_URL` 指向您自己的实例。设置自定义 URL 时，API 密钥变为可选（在服务器上设置 `USE_DB_AUTHENTICATION=false` 以禁用认证）。

**Parallel 搜索模式：** 设置 `PARALLEL_SEARCH_MODE` 来控制搜索行为 — `fast`、`one-shot` 或 `agentic`（默认：`agentic`）。

## Browser

配置浏览器自动化行为：

```yaml
browser:
  inactivity_timeout: 120        # 空闲会话自动关闭前的秒数
  command_timeout: 30             # 浏览器命令超时秒数（截图、导航等）
  record_sessions: false         # 自动将浏览器会话录制为 WebM 视频到 ~/.hermes/browser_recordings/
  camofox:
    managed_persistence: false   # 为 true 时，Camofox 会话在重启后保留 cookie/登录
```

浏览器工具集支持多个提供商。请参阅[浏览器功能页面](/docs/user-guide/features/browser) 了解 Browserbase、Browser Use 和本地 Chrome CDP 设置的详细信息。

## Timezone

使用 IANA 时区字符串覆盖服务器本地时区。影响日志中的时间戳、cron 调度和系统提示时间注入。

```yaml
timezone: "America/New_York"   # IANA 时区（默认："" = 服务器本地时间）
```

支持的值：任何 IANA 时区标识符（例如 `America/New_York`、`Europe/London`、`Asia/Kolkata`、`UTC`）。留空或省略以使用服务器本地时间。

## Discord

为消息网关配置 Discord 特定行为：

```yaml
discord:
  require_mention: true          # 要求在服务器频道中 @mention 才能响应
  free_response_channels: ""     # 逗号分隔的频道 ID，机器人在这些频道中无需 @mention 即可响应
  auto_thread: true              # 在频道中 @mention 时自动创建线程
```

- `require_mention` — 当 `true`（默认）时，机器人仅在服务器频道中被 @mention 时才响应。私信始终无需 mention 即可工作。
- `free_response_channels` — 逗号分隔的频道 ID 列表，机器人在这些频道中对每条消息都响应，无需 mention。
- `auto_thread` — 当 `true`（默认）时，频道中的 mention 会自动为对话创建线程，保持频道清洁（类似于 Slack 线程）。

## Security

Pre-execution security scanning and secret redaction:

```yaml
security:
  redact_secrets: true           # 在工具输出和日志中编辑 API 密钥模式
  tirith_enabled: true           # 启用 Tirith 安全扫描以检测终端命令
  tirith_path: "tirith"          # tirith 二进制文件的路径（默认：$PATH 中的 "tirith"）
  tirith_timeout: 5              # 等待 tirith 扫描的超时秒数
  tirith_fail_open: true         # 当 tirith 不可用时允许命令执行
  website_blocklist:             # 请参阅下面的网站黑名单部分
    enabled: false
    domains: []
    shared_files: []
```

- `redact_secrets` — 自动检测并编辑工具输出中看起来像 API 密钥、令牌和密码的模式，然后它们才会进入对话上下文和日志。
- `tirith_enabled` — 当 `true` 时，终端命令在执行前会由 [Tirith](https://github.com/StackGuardian/tirith) 扫描，以检测潜在的危险操作。
- `tirith_path` — tirith 二进制文件的路径。如果 tirith 安装在非标准位置，请设置此项。
- `tirith_timeout` — 等待 tirith 扫描的最大秒数。如果扫描超时，命令将继续执行。
- `tirith_fail_open` — 当 `true`（默认）时，如果 tirith 不可用或失败，命令仍被允许执行。设置为 `false` 以在 tirith 无法验证时阻止命令。

## Website Blocklist

阻止特定域名被智能体的网络和浏览器工具访问：

```yaml
security:
  website_blocklist:
    enabled: false               # 启用 URL 阻止（默认：false）
    domains:                     # 阻止的域名模式列表
      - "*.internal.company.com"
      - "admin.example.com"
      - "*.local"
    shared_files:                # 从外部文件加载额外规则
      - "/etc/hermes/blocked-sites.txt"
```

启用后，在网络或浏览器工具执行前，任何匹配阻止域名模式的 URL 都会被拒绝。这适用于 `web_search`、`web_extract`、`browser_navigate` 以及任何访问 URL 的工具。

域名规则支持：
- 精确域名：`admin.example.com`
- 通配符子域名：`*.internal.company.com`（阻止所有子域名）
- 顶级域名通配符：`*.local`

共享文件每行包含一个域名规则（空行和 `#` 注释被忽略）。缺失或不可读的文件记录警告但不会禁用其他网络工具。

策略被缓存 30 秒，因此配置更改会快速生效而无需重启。

## Smart Approvals

Control how Hermes handles potentially dangerous commands:

```yaml
approvals:
  mode: manual   # manual | smart | off
```

| 模式 | 行为 |
|------|----------|
| `manual`（默认）| 在执行任何标记的命令前提示用户。在 CLI 中，显示交互式批准对话框。在消息中，排队等待批准请求。 |
| `smart` | 使用辅助 LLM 评估标记的命令是否真的危险。低风险命令会使用会话级持久性自动批准。真正危险的命令会上报给用户。 |
| `off` | 跳过所有批准检查。相当于 `HERMES_YOLO_MODE=true`。**谨慎使用。** |

智能模式对于减少批准疲劳特别有用 — 它让智能体在安全操作上更加自主，同时仍然捕捉真正的破坏性命令。

:::warning
设置 `approvals.mode: off` 会禁用终端命令的所有安全检查。仅在受信任的沙盒环境中使用。
:::

## Checkpoints

破坏性文件操作前的自动文件系统快照。详情请参阅[检查点和回滚](/docs/user-guide/checkpoints-and-rollback)。

```yaml
checkpoints:
  enabled: true                  # 启用自动检查点（也是：hermes --checkpoints）
  max_snapshots: 50              # 每个目录保留的最大检查点数
```


## Delegation

为 delegate 工具配置子智能体行为：

```yaml
delegation:
  # model: "google/gemini-3-flash-preview"  # 覆盖模型（空 = 继承父级）
  # provider: "openrouter"                  # 覆盖提供商（空 = 继承父级）
  # base_url: "http://localhost:1234/v1"    # 直接 OpenAI 兼容端点（优先于提供商）
  # api_key: "local-key"                    # base_url 的 API 密钥（回退到 OPENAI_API_KEY）
```

**子智能体提供商：模型覆盖：** 默认情况下，子智能体继承父智能体的提供商和模型。设置 `delegation.provider` 和 `delegation.model` 将子智能体路由到不同的提供商：模型对 — 例如，当您的主要智能体运行昂贵的推理模型时，使用便宜/快速的模型进行范围狭窄的子任务。

**直接端点覆盖：** 如果您想要明显的自定义端点路径，请设置 `delegation.base_url`、`delegation.api_key` 和 `delegation.model`。这将子智能体直接发送到该 OpenAI 兼容端点，并优先于 `delegation.provider`。如果省略 `delegation.api_key`，Hermes 仅回退到 `OPENAI_API_KEY`。

委托提供商使用与 CLI/gateway 启动相同的凭证解析。支持所有配置的提供商：`openrouter`、`nous`、`copilot`、`zai`、`kimi-coding`、`minimax`、`minimax-cn`。设置提供商时，系统会自动解析正确的基础 URL、API 密钥和 API 模式 — 无需手动凭证连接。

**优先级：** 配置中的 `delegation.base_url` → 配置中的 `delegation.provider` → 父提供商（继承）。配置中的 `delegation.model` → 父模型（继承）。仅设置 `model` 而不设置 `provider` 只更改模型名称，同时保持父级的凭证（在同一路由器内切换模型很有用，如 OpenRouter）。

## Clarify

配置澄清提示行为：

```yaml
clarify:
  timeout: 120                 # 等待用户澄清响应的秒数
```

## Context Files (SOUL.md, AGENTS.md)

Hermes 使用两种不同的上下文范围：

| 文件 | 用途 | 范围 |
|------|---------|-------|
| `SOUL.md` | **主要智能体身份** — 定义智能体是谁（系统提示中的插槽 #1）| `~/.hermes/SOUL.md` 或 `$HERMES_HOME/SOUL.md` |
| `.hermes.md` / `HERMES.md` | 项目特定指令（最高优先级）| 步进到 git 根目录 |
| `AGENTS.md` | 项目特定指令、编码约定 | 递归目录遍历 |
| `CLAUDE.md` | Claude Code 上下文文件（也检测）| 工作目录仅 |
| `.cursorrules` | Cursor IDE 规则（也检测）| 工作目录仅 |
| `.cursor/rules/*.mdc` | Cursor 规则文件（也检测）| 工作目录仅 |

- **SOUL.md** 是智能体的主要身份。它占据系统提示中的插槽 #1，完全替换内置默认身份。编辑它以完全自定义智能体是谁。
- 如果 SOUL.md 缺失、为空或无法加载，Hermes 回退到内置默认身份。
- **项目上下文文件使用优先级系统** — 仅加载一种类型（首次匹配获胜）：`.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`。SOUL.md 始终独立加载。
- **AGENTS.md** 是分层的：如果子目录也有 AGENTS.md，所有都将组合。
- Hermes 在不存在默认 `SOUL.md` 时自动播种。
- 所有加载的上下文文件最多限制为 20,000 个字符，并带有智能截断。

另请参阅：
- [Personality & SOUL.md](/docs/user-guide/features/personality)
- [Context Files](/docs/user-guide/features/context-files)

## Working Directory

| Context | Default |
|---------|---------|
| **CLI (`hermes`)** | Current directory where you run the command |
| **消息网关** | 主目录 `~`（使用 `MESSAGING_CWD` 覆盖）|
| **Docker / Singularity / Modal / SSH** | 容器或远程机器内的用户主目录 |

覆盖工作目录：
```bash
# 在 ~/.hermes/.env 或 ~/.hermes/config.yaml 中：
MESSAGING_CWD=/home/myuser/projects    # 网关会话
TERMINAL_CWD=/workspace                # 所有终端会话
```