---
sidebar_position: 8
title: "安全性"
description: "安全模型、危险命令批准、用户授权、容器隔离和生产部署最佳实践"
---

# 安全性

Hermes Agent 采用纵深防御安全模型设计。本页涵盖每个安全边界 — 从命令批准到容器隔离再到消息平台上的用户授权。

## 概述

安全模型有七层：

1. **用户授权** — 谁可以与智能体对话（允许列表、DM 配对）
2. **危险命令批准** — 破坏性操作的人工干预
3. **容器隔离** — 使用强化设置的 Docker/Singularity/Modal 沙箱
4. **MCP 凭据过滤** — MCP 子进程的环境变量隔离
5. **上下文文件扫描** — 项目文件中的提示注入检测
6. **跨会话隔离** — 会话无法访问彼此的数据或状态；定时任务存储路径针对路径遍历攻击进行了强化
7. **输入清理** — 终端工具后端中的工作目录参数根据允许列表进行验证，以防止 shell 注入

## 危险命令批准

在执行任何命令之前，Hermes 会根据精心策划的危险模式列表进行检查。如果发现匹配，用户必须明确批准。

### 批准模式

批准系统支持三种模式，通过 `~/.hermes/config.yaml` 中的 `approvals.mode` 配置：

```yaml
approvals:
  mode: manual    # manual | smart | off
  timeout: 60     # 等待用户响应的秒数（默认：60）
```

| 模式 | 行为 |
|------|----------|
| **manual**（默认） | 总是提示用户批准危险命令 |
| **smart** | 使用辅助 LLM 评估风险。低风险命令（例如，`python -c "print('hello')"`）自动批准。真正危险的命令自动拒绝。不确定的情况升级为手动提示。 |
| **off** | 禁用所有批准检查 — 相当于使用 `--yolo` 运行。所有命令在无提示的情况下执行。 |

:::warning
设置 `approvals.mode: off` 会禁用所有安全提示。仅在受信任的环境（CI/CD、容器等）中使用。
:::

### YOLO 模式

YOLO 模式绕过当前会话的**所有**危险命令批准提示。它可以通过三种方式激活：

1. **CLI 标志**: 使用 `hermes --yolo` 或 `hermes chat --yolo` 启动会话
2. **斜杠命令**: 在会话期间输入 `/yolo` 以切换开关
3. **环境变量**: 设置 `HERMES_YOLO_MODE=1`

`/yolo` 命令是一个**切换** — 每次使用都会打开或关闭模式：

```
> /yolo
  ⚡ YOLO 模式已开启 — 所有命令自动批准。谨慎使用。

> /yolo
  ⚠ YOLO 模式已关闭 — 危险命令将需要批准。
```

YOLO 模式在 CLI 和网关会话中都可用。在内部，它设置 `HERMES_YOLO_MODE` 环境变量，在每次命令执行前都会检查该变量。

:::danger
YOLO 模式禁用会话的**所有**危险命令安全检查。仅在您完全信任生成的命令时使用（例如，临时环境中经过良好测试的自动化脚本）。
:::

### 批准超时

当危险命令提示出现时，用户有可配置的时间来响应。如果在超时时间内没有响应，命令**默认被拒绝**（故障关闭）。

在 `~/.hermes/config.yaml` 中配置超时：

```yaml
approvals:
  timeout: 60  # 秒（默认：60）
```

### 什么会触发批准

以下模式会触发批准提示（定义在 `tools/approval.py` 中）：

| 模式 | 描述 |
|---------|-------------|
| `rm -r` / `rm --recursive` | 递归删除 |
| `rm ... /` | 删除根路径中的内容 |
| `chmod 777/666` / `o+w` / `a+w` | 全局/其他可写权限 |
| `chmod --recursive` 加上不安全的权限 | 递归全局/其他可写（长标志） |
| `chown -R root` / `chown --recursive root` | 递归 chown 到 root |
| `mkfs` | 格式化文件系统 |
| `dd if=` | 磁盘复制 |
| `> /dev/sd` | 写入块设备 |
| `DROP TABLE/DATABASE` | SQL DROP |
| `DELETE FROM`（没有 WHERE）| 没有 WHERE 的 SQL DELETE |
| `TRUNCATE TABLE` | SQL TRUNCATE |
| `> /etc/` | 覆盖系统配置 |
| `systemctl stop/disable/mask` | 停止/禁用系统服务 |
| `kill -9 -1` | 杀死所有进程 |
| `pkill -9` | 强制杀死进程 |
| Fork bomb patterns | Fork 炸弹 |
| `bash -c` / `sh -c` / `zsh -c` / `ksh -c` | 通过 `-c` 标志执行 shell 命令（包括组合标志如 `-lc`） |
| `python -e` / `perl -e` / `ruby -e` / `node -c` | 通过 `-e`/`-c` 标志执行脚本 |
| `curl ... | sh` / `wget ... | sh` | 将远程内容通过管道传输到 shell |
| `bash <(curl ...)` / `sh <(wget ...)` | 通过进程替换执行远程脚本 |
| `tee` 到 `/etc/`、`~/.ssh/`、`~/.hermes/.env` | 通过 tee 覆盖敏感文件 |
| `>` / `>>` 到 `/etc/`、`~/.ssh/`、`~/.hermes/.env` | 通过重定向覆盖敏感文件 |
| `xargs rm` | 带有 rm 的 xargs |
| `find -exec rm` / `find -delete` | 带有破坏性操作的 find |
| `cp`/`mv`/`install` 到 `/etc/` | 将文件复制/移动到系统配置 |
| `sed -i` / `sed --in-place` 在 `/etc/` 上 | 系统配置的就地编辑 |
| `pkill`/`killall` hermes/gateway | 防止自我终止 |
| 使用 `&`/`disown`/`nohup`/`setsid` 的 `gateway run` | 防止在服务管理器外启动网关 |

:::info
**容器绕过**: 当在 `docker`、`singularity`、`modal` 或 `daytona` 后端运行时，危险命令检查会被**跳过**，因为容器本身是安全边界。容器内的破坏性命令无法损害主机。
:::

### 批准流程（CLI）

在交互式 CLI 中，危险命令显示内联批准提示：

```
  ⚠️  危险命令：递归删除
      rm -rf /tmp/old-project

      [o]一次  |  [s]会话  |  [a]始终  |  [d]拒绝

      选择 [o/s/a/D]：
```

四个选项：

- **一次** — 允许此次执行
- **会话** — 在会话剩余时间内允许此模式
- **始终** — 添加到永久允许列表（保存到 `config.yaml`）
- **拒绝**（默认）— 阻止命令

### 批准流程（网关/消息）

在消息平台上，智能体将危险命令详情发送到聊天中并等待用户回复：

- 回复 **yes**、**y**、**approve**、**ok** 或 **go** 以批准
- 回复 **no**、**n**、**deny** 或 **cancel** 以拒绝

运行网关时自动设置 `HERMES_EXEC_ASK=1` 环境变量。

### 永久允许列表

使用"始终"批准的 命令会保存到 `~/.hermes/config.yaml`：

```yaml
# 永久允许的危险命令模式
command_allowlist:
  - rm
  - systemctl
```

这些模式在启动时加载，并在所有未来会话中静默批准。

:::tip
使用 `hermes config edit` 查看或从永久允许列表中删除模式。
:::

## 用户授权（网关）

运行消息网关时，Hermes 通过分层授权系统控制谁可以与机器人交互。

### 授权检查顺序

`_is_user_authorized()` 方法按以下顺序检查：

1. **平台允许所有人标志**（例如 `DISCORD_ALLOW_ALL_USERS=true`）
2. **DM 配对批准列表**（通过配对代码批准的用户）
3. **平台特定允许列表**（例如 `TELEGRAM_ALLOWED_USERS=12345,67890`）
4. **全局允许列表**（`GATEWAY_ALLOWED_USERS=12345,67890`）
5. **全局允许所有人**（`GATEWAY_ALLOW_ALL_USERS=true`）
6. **默认：拒绝**

### 平台允许列表

在 `~/.hermes/.env` 中将允许的用户 ID 设置为逗号分隔的值：

```bash
# 平台特定允许列表
TELEGRAM_ALLOWED_USERS=123456789,987654321
DISCORD_ALLOWED_USERS=111222333444555666
WHATSAPP_ALLOWED_USERS=15551234567
SLACK_ALLOWED_USERS=U01ABC123

# 跨平台允许列表（所有平台检查）
GATEWAY_ALLOWED_USERS=123456789

# 平台允许所有人（谨慎使用）
DISCORD_ALLOW_ALL_USERS=true

# 全局允许所有人（极其谨慎使用）
GATEWAY_ALLOW_ALL_USERS=true
```

:::warning
如果**没有配置允许列表**且未设置 `GATEWAY_ALLOW_ALL_USERS`，**所有用户都被拒绝**。网关在启动时记录警告：

```
未配置用户允许列表。所有未经授权的用户将被拒绝。
在 ~/.hermes/.env 中设置 GATEWAY_ALLOW_ALL_USERS=true 以允许开放访问，
或配置平台允许列表（例如 TELEGRAM_ALLOWED_USERS=your_id）。
```
:::

### DM 配对系统

为了更灵活的授权，Hermes 包含基于代码的配对系统。无需预先要求用户 ID，未知的用户会收到一次性的配对代码，机器人所有者通过 CLI 批准。

**工作原理：**

1. 未知用户向机器人发送 DM
2. 机器人回复 8 字符的配对代码
3. 机器人在 CLI 上运行 `hermes pairing approve <platform> <code>`
4. 用户在该平台上永久获得批准

在 `~/.hermes/.env` 中配置如何处理未经授权的 DM：

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `pair` 是默认值。未经授权的 DM 会收到配对代码回复。
- `ignore` 静默丢弃未经授权的 DM。
- 平台部分覆盖全局默认值，因此您可以在 Telegram 上保持配对，同时让 WhatsApp 保持沉默。

**安全功能**（基于 OWASP + NIST SP 800-63-4 指导）：

| 功能 | 详情 |
|---------|---------|
| 代码格式 | 来自 32 字符无歧义字母表的 8 字符（无 0/O/1/I） |
| 随机性 | 加密随机（`secrets.choice()`） |
| 代码 TTL | 1 小时过期 |
| 速率限制 | 每个用户每 10 分钟 1 个请求 |
| 待处理限制 | 每个平台最多 3 个待处理代码 |
| 锁定 | 5 次失败批准尝试 → 1 小时锁定 |
| 文件安全 | 所有配对数据文件使用 `chmod 0600` |
| 日志记录 | 代码永远不会记录到 stdout |

**配对 CLI 命令：**

```bash
# 列出待处理和已批准的用户
hermes pairing list

# 批准配对代码
hermes pairing approve telegram ABC12DEF

# 撤销用户的访问权限
hermes pairing revoke telegram 123456789

# 清除所有待处理代码
hermes pairing clear-pending
```

**存储：** 配对数据存储在 `~/.hermes/pairing/` 中，包含每个平台的 JSON 文件：
- `{platform}-pending.json` — 待处理的配对请求
- `{platform}-approved.json` — 已批准的用户
- `_rate_limits.json` — 速率限制和锁定跟踪

## 容器隔离

使用 `docker` 终端后端时，Hermes 为每个容器应用严格的安全强化。

### Docker 安全标志

每个容器都使用这些标志运行（定义在 `tools/environments/docker.py` 中）：

```python
_SECURITY_ARGS = [
    "--cap-drop", "ALL",                          # 丢弃所有 Linux 能力
    "--cap-add", "DAC_OVERRIDE",                  # Root 可以写入绑定挂载的目录
    "--cap-add", "CHOWN",                         # 包管理器需要文件所有权
    "--cap-add", "FOWNER",                        # 包管理器需要文件所有权
    "--security-opt", "no-new-privileges",         # 阻止权限提升
    "--pids-limit", "256",                         # 限制进程数
    "--tmpfs", "/tmp:rw,nosuid,size=512m",         # 大小限制的 /tmp
    "--tmpfs", "/var/tmp:rw,noexec,nosuid,size=256m",  # 不可执行的 /var/tmp
    "--tmpfs", "/run:rw,noexec,nosuid,size=64m",   # 不可执行的 /run
]
```

### 资源限制

容器资源可在 `~/.hermes/config.yaml` 中配置：

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_forward_env: []  # 仅显式允许列表；空值使机密信息不进入容器
  container_cpu: 1        # CPU 核心
  container_memory: 5120  # MB（默认 5GB）
  container_disk: 51200   # MB（默认 50GB，需要 XFS 上的 overlay2）
  container_persistent: true  # 跨会话持久化文件系统
```

### 文件系统持久化

- **持久化模式**（`container_persistent: true`）：从 `~/.hermes/sandboxes/docker/<task_id>/` 绑定挂载 `/workspace` 和 `/root`
- **临时模式**（`container_persistent: false`）：对 workspace 使用 tmpfs — 清理后一切丢失

:::tip
对于生产网关部署，使用 `docker`、`modal` 或 `daytona` 后端将智能体命令与主机系统隔离。这完全消除了危险命令批准的需要。
:::

:::warning
如果向 `terminal.docker_forward_env` 添加名称，这些变量会被故意注入到容器中以供终端命令使用。这对于特定任务的凭据（如 `GITHUB_TOKEN`）很有用，但也意味着在容器中运行的代码可以读取和泄露它们。
:::

## 终端后端安全比较

| 后端 | 隔离 | 危险命令检查 | 适用场景 |
|---------|-----------|-------------------|----------|
| **local** | 无 — 在主机上运行 | ✅ 是 | 开发、受信任用户 |
| **ssh** | 远程机器 | ✅ 是 | 在单独的服务器上运行 |
| **docker** | 容器 | ❌ 跳过（容器是边界） | 生产网关 |
| **singularity** | 容器 | ❌ 跳过 | HPC 环境 |
| **modal** | 云沙箱 | ❌ 跳过 | 可扩展云隔离 |
| **daytona** | 云沙箱 | ❌ 跳过 | 持久云工作区 |

## 环境变量传递 {#environment-variable-passthrough}

`execute_code` 和 `terminal` 都会从子进程中剥离敏感环境变量，以防止 LLM 生成的代码泄露凭据。但是，声明 `required_environment_variables` 的技能合法需要访问这些变量。

### 工作原理

两种机制允许特定变量通过沙箱过滤器：

**1. 技能范围的传递（自动）**

当加载技能（通过 `skill_view` 或 `/skill` 命令）并声明 `required_environment_variables` 时，任何在实际环境中设置的这些变量都会自动注册为传递。缺失的变量（仍处于设置需要状态）**不会**被注册。

```yaml
# 在技能的 SKILL.md frontmatter 中
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API 密钥
    help: 从 https://developers.google.com/tenor 获取密钥
```

加载此技能后，`TENOR_API_KEY` 传递到 `execute_code`、`terminal`（本地）**以及远程后端（Docker、Modal）** — 无需手动配置。

:::info Docker 和 Modal
在 v0.5.1 之前，Docker 的 `forward_env` 是一个与技能传递独立的系统。它们现已合并 — 技能声明的环境变量会自动转发到 Docker 容器和 Modal 沙箱，无需手动将它们添加到 `docker_forward_env`。
:::

**2. 基于配置的传递（手动）**

对于任何技能未声明的环境变量，将它们添加到 `config.yaml` 中的 `terminal.env_passthrough`：

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_KEY
    - ANTHON_TOKEN
```

### 凭据文件传递（OAuth 令牌等）{#credential-file-passthrough}

某些技能需要沙箱中的**文件**（而不仅仅是环境变量）— 例如，Google Workspace 将 OAuth 令牌存储在活动配置文件 `HERMES_HOME` 下的 `google_token.json` 中。技能在 frontmatter 中声明这些：

```yaml
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 令牌（由设置脚本创建）
  - path: google_client_secret.json
    description: Google OAuth2 客户端凭据
```

加载时，Hermes 检查这些文件是否存在于活动配置文件的 `HERMES_HOME` 中，并注册它们以供挂载：

- **Docker**: 只读绑定挂载（`-v host:container:ro`）
- **Modal**: 在沙箱创建时挂载 + 在每次命令前同步（处理会话中 OAuth 设置）
- **Local**: 无需操作（文件已可访问）

您也可以在 `config.yaml` 中手动列出凭据文件：

```yaml
terminal:
  credential_files:
    - google_token.json
    - my_custom_oauth_token.json
```

路径相对于 `~/.hermes/`。文件挂载到容器内的 `/root/.hermes/`。

### 每个沙箱过滤的内容

| 沙箱 | 默认过滤器 | 传递覆盖 |
|---------|---------------|---------------------|
| **execute_code** | 阻止名称中包含 `KEY`、`TOKEN`、`SECRET`、`PASSWORD`、`CREDENTIAL`、`PASSWD`、`AUTH` 的变量；仅允许安全前缀变量通过 | ✅ 传递变量绕过两种检查 |
| **terminal**（本地） | 阻止显式 Hermes 基础设施变量（提供商密钥、网关令牌、工具 API 密钥） | ✅ 传递变量绕过阻止列表 |
| **terminal**（Docker） | 默认无主机环境变量 | ✅ 传递变量 + `docker_forward_env` 通过 `-e` 转发 |
| **terminal**（Modal） | 默认无主机环境/文件 | ✅ 凭据文件挂载；环境变量通过同步传递 |
| **MCP** | 阻止除安全系统变量 + 显式配置的 `env` 外的所有内容 | ❌ 不受传递影响（改用 MCP `env` 配置） |

### 安全注意事项

- 传递仅影响您或您的技能明确声明的变量 — 对于任意 LLM 生成的代码，默认安全态势保持不变
- 凭据文件以**只读**方式挂载到 Docker 容器中
- 技能守护在安装前扫描技能内容中可疑的环境访问模式
- 缺失/未设置的变量永远不会注册（您无法泄露不存在的内容）
- Hermes 基础设施机密（提供商 API 密钥、网关令牌）永远不应添加到 `env_passthrough` — 它们有专门的机制

## MCP 凭据处理

MCP（模型上下文协议）服务器子进程接收**过滤后的环境**以防止意外的凭据泄露。

### 安全环境变量

只有这些变量从主机传递到 MCP stdio 子进程：

```
PATH, HOME, USER, LANG, LC_ALL, TERM, SHELL, TMPDIR
```

加上任何 `XDG_*` 变量。所有其他环境变量（API 密钥、令牌、机密）都被**剥离**。

在 MCP 服务器的 `env` 配置中显式定义的变量会通过：

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."  # 只有这个被传递
```

### 凭据编辑

MCP 工具的错误消息在返回给 LLM 之前会被清理。以下模式会被替换为 `[REDACTED]`：

- GitHub PAT（`ghp_...`）
- OpenAI 风格的密钥（`sk-...`）
- Bearer 令牌
- `token=`、`key=`、`API_KEY=`、`password=`、`secret=` 参数

### 网站访问策略

您可以限制智能体可以通过其 Web 和浏览器工具访问的网站。这对于防止智能体访问内部服务、管理面板或其他敏感 URL 很有用。

```yaml
# 在 ~/.hermes/config.yaml 中
security:
  website_blocklist:
    enabled: true
    domains:
      - "*.internal.company.com"
      - "admin.example.com"
    shared_files:
      - "/etc/hermes/blocked-sites.txt"
```

当请求被阻止的 URL 时，工具会返回一个错误，说明该域被策略阻止。阻止列表在 `web_search`、`web_extract`、`browser_navigate` 和所有支持 URL 的工具中强制执行。

有关完整详细信息，请参阅配置指南中的[网站阻止列表](/docs/user-guide/configuration#website-blocklist)。

### SSRF 保护

所有支持 URL 的工具（Web 搜索、Web 提取、视觉、浏览器）在获取之前验证 URL，以防止服务器端请求伪造（SSRF）攻击。阻止的地址包括：

- **私有网络**（RFC 1918）：`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`
- **环回地址**：`127.0.0.0/8`、`::1`
- **链路本地**：`169.254.0.0/16`（包括云元数据 `169.254.169.254`）
- **CGNAT/共享地址空间**（RFC 6598）：`100.64.0.0/10`（Tailscale、WireGuard VPN）
- **云元数据主机名**：`metadata.google.internal`、`metadata.goog`
- **保留、多播和未指定地址**

SSRF 保护始终处于活动状态，无法禁用。DNS 失败被视为阻止（故障关闭）。重定向链在每跳重新验证，以防止基于重定向的绕过。

### Tirith 执行前安全扫描

Hermes 集成 [tirith](https://github.com/sheeki03/tirith) 在执行前进行内容级命令扫描。Tirith 检测模式匹配单独遗漏的威胁：

- 同形 URL 欺骗（国际化域攻击）
- 管道到解释器模式（`curl | bash`、`wget | sh`）
- 终端注入攻击

Tirith 在首次使用时会自动从 GitHub 版本安装，并进行 SHA-256 校验和验证（如果 cosign 可用，还会有 cosign 来源验证）。

```yaml
# 在 ~/.hermes/config.yaml 中
security:
  tirith_enabled: true       # 启用/禁用 tirith 扫描（默认：true）
  tirith_path: "tirith"      # tirith 二进制文件路径（默认：PATH 查找）
  tirith_timeout: 5          # 子进程超时（秒）
  tirith_fail_open: true     # 当 tirith 不可用时允许执行（默认：true）
```

当 `tirith_fail_open` 为 `true`（默认）时，如果 tirith 未安装或超时，命令将继续。在高安全环境中设置为 `false` 以在 tirith 不可用时阻止命令。

Tirith 的判决与批准流程集成：安全的命令通过，而可疑和被阻止的命令都会触发用户批准，并显示完整的 tirith 发现结果（严重性、标题、描述、更安全的替代方案）。用户可以批准或拒绝 — 默认选择是拒绝，以保持无人值守场景的安全。

### 上下文文件注入保护

上下文文件（AGENTS.md、.cursorrules、SOUL.md）在包含在系统提示之前会扫描提示注入。扫描器检查：

- 忽略/不理会先前指示的指示
- 带有可疑关键词的隐藏 HTML 注释
- 尝试读取机密信息（`.env`、`credentials`、`.netrc`）
- 通过 `curl` 进行凭据泄露
- 不可见的 Unicode 字符（零宽空格、双向覆盖）

被阻止的文件显示警告：

```
[已阻止：AGENTS.md 包含潜在提示注入（prompt_injection）。内容未加载。]
```

## 生产部署最佳实践

### 网关部署清单

1. **设置显式允许列表** — 在生产环境中永远不要使用 `GATEWAY_ALLOW_ALL_USERS=true`
2. **使用容器后端** — 在 config.yaml 中设置 `terminal.backend: docker`
3. **限制资源** — 设置适当的 CPU、内存和磁盘限制
4. **安全存储机密** — 将 API 密钥保存在 `~/.hermes/.env` 中，并设置适当的文件权限
5. **启用 DM 配对** — 尽可能使用配对代码而不是硬编码用户 ID
6. **审查命令允许列表** — 定期审计 config.yaml 中的 `command_allowlist`
7. **设置 `MESSAGING_CWD`** — 不要让智能体从敏感目录操作
8. **以非 root 身份运行** — 永远不要以 root 身份运行网关
9. **监控日志** — 检查 `~/.hermes/logs/` 以发现未经授权的访问尝试
10. **保持更新** — 定期运行 `hermes update` 以获取安全补丁

### 保护 API 密钥

```bash
# 设置 .env 文件的正确权限
chmod 600 ~/.hermes/.env

# 为不同服务保持单独的密钥
# 永远不要将 .env 文件提交到版本控制
```

### 网络隔离

为获得最大安全性，请在单独的机器或 VM 上运行网关：

```yaml
terminal:
  backend: ssh
  ssh_host: "agent-worker.local"
  ssh_user: "hermes"
  ssh_key: "~/.ssh/hermes_agent_key"
```

这使网关的消息连接与智能体的命令执行保持分离。