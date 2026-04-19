---
sidebar_position: 1
title: "工具与工具集"
description: "Hermes Agent 工具概述 — 可用工具、工具集工作原理和终端后端"
---

# 工具与工具集

工具是扩展智能体能力的函数。它们被组织成逻辑**工具集**，可以按平台启用或禁用。

## 可用工具

Hermes 附带一个广泛的内置工具注册表，涵盖网络搜索、浏览器自动化、终端执行、文件编辑、内存、委托、RL 训练、消息传递、Home Assistant 等。

:::note
**Honcho 跨会话内存**作为内存提供商插件（`plugins/memory/honcho/`）可用，而不是作为内置工具集。有关安装，请参阅[插件](./plugins.md)。
:::

高级类别：

| 类别 | 示例 | 描述 |
|----------|----------|-------------|
| **Web** | `web_search`, `web_extract` | 搜索网络并提取页面内容。 |
| **终端和文件** | `terminal`, `process`, `read_file`, `patch` | 执行命令和操作文件。 |
| **浏览器** | `browser_navigate`, `browser_snapshot`, `browser_vision` | 具有文本和视觉支持的交互式浏览器自动化。 |
| **媒体** | `vision_analyze`, `image_generate`, `text_to_speech` | 多模态分析和生成。 |
| **智能体编排** | `todo`, `clarify`, `execute_code`, `delegate_task` | 规划、澄清、代码执行和子智能体委托。 |
| **记忆与召回** | `memory`, `session_search` | 持久记忆和会话搜索。 |
| **自动化与传递** | `cronjob`, `send_message` | 具有创建/列出/更新/暂停/恢复/运行/删除操作的计划任务，以及出站消息传递。 |
| **集成** | `ha_*`, MCP server tools, `rl_*` | Home Assistant、MCP、RL 训练和其他集成。 |

有关权威的代码派生注册表，请参阅[内置工具参考](/docs/reference/tools-reference)和[工具集参考](/docs/reference/toolsets-reference)。

## 使用工具集

```bash
# 使用特定工具集
hermes chat --toolsets "web,terminal"

# 查看所有可用工具
hermes tools

# 按平台配置工具（交互式）
hermes tools
```

常见工具集包括 `web`、`terminal`、`file`、`browser`、`vision`、`image_gen`、`moa`、`skills`、`tts`、`todo`、`memory`、`session_search`、`cronjob`、`code_execution`、`delegation`、`clarify`、`homeassistant` 和 `rl`。

有关完整集合，请参阅[工具集参考](/docs/reference/toolsets-reference)，包括平台预设（如 `hermes-cli`、`hermes-telegram`）和动态 MCP 工具集（如 `mcp-<server>`）。

## 终端后端

终端工具可以在不同环境中执行命令：

| 后端 | 描述 | 使用场景 |
|---------|-------------|----------|
| `local` | 在您的机器上运行（默认） | 开发、受信任的任务 |
| `docker` | 隔离容器 | 安全性、可重现性 |
| `ssh` | 远程服务器 | 沙盒隔离、防止智能体修改自身代码 |
| `singularity` | HPC 容器 | 集群计算、无 root 权限 |
| `modal` | 云执行 | 无服务器、可扩展 |
| `daytona` | 云沙盒工作区 | 持久远程开发环境 |

### 配置

```yaml
# 在 ~/.hermes/config.yaml 中
terminal:
  backend: local    # 或: docker, ssh, singularity, modal, daytona
  cwd: "."          # 工作目录
  timeout: 180      # 命令超时（秒）
```

### Docker 后端

```yaml
terminal:
  backend: docker
  docker_image: python:3.11-slim
```

### SSH 后端

推荐用于安全性 — 智能体无法修改自身代码：

```yaml
terminal:
  backend: ssh
```
```bash
# 在 ~/.hermes/.env 中设置凭据
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=myuser
TERMINAL_SSH_KEY=~/.ssh/id_rsa
```

### Singularity/Apptainer

```bash
# 为并行工作器预构建 SIF
apptainer build ~/python.sif docker://python:3.11-slim

# 配置
hermes config set terminal.backend singularity
hermes config set terminal.singularity_image ~/python.sif
```

### Modal（无服务器云）

```bash
uv pip install modal
modal setup
hermes config set terminal.backend modal
```

### 容器资源

为所有容器后端配置 CPU、内存、磁盘和持久性：

```yaml
terminal:
  backend: docker  # 或 singularity, modal, daytona
  container_cpu: 1              # CPU 核心数（默认：1）
  container_memory: 5120        # 内存（MB，默认：5GB）
  container_disk: 51200         # 磁盘（MB，默认：50GB）
  container_persistent: true    # 在会话间持久化文件系统（默认：true）
```

当 `container_persistent: true` 时，安装的包、文件和配置会在会话间保持。

### 容器安全性

所有容器后端都运行安全强化：

- 只读根文件系统（Docker）
- 所有 Linux 功能被禁用
- 无权限提升
- PID 限制（256 个进程）
- 完整的命名空间隔离
- 通过卷实现持久工作区，而非可写根层

Docker 可以通过 `terminal.docker_forward_env` 接收显式环境变量白名单，但转发的变量对容器内的命令可见，应被视为对该会话公开。

## 后台进程管理

启动后台进程并管理它们：

```python
terminal(command="pytest -v tests/", background=true)
# Returns: {"session_id": "proc_abc123", "pid": 12345}

# Then manage with the process tool:
process(action="list")       # Show all running processes
process(action="poll", session_id="proc_abc123")   # Check status
process(action="wait", session_id="proc_abc123")   # Block until done
process(action="log", session_id="proc_abc123")    # Full output
process(action="kill", session_id="proc_abc123")   # Terminate
process(action="write", session_id="proc_abc123", data="y")  # Send input
```

PTY mode (`pty=true`) enables interactive CLI tools like Codex and Claude Code.

## Sudo Support

If a command needs sudo, you'll be prompted for your password (cached for the session). Or set `SUDO_PASSWORD` in `~/.hermes/.env`.

:::warning
On messaging platforms, if sudo fails, the output includes a tip to add `SUDO_PASSWORD` to `~/.hermes/.env`.
:::
