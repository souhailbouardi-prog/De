---
sidebar_position: 1
title: "工具与工具集"
description: "Hermes Agent 工具概述 — 可用工具、工具集工作原理和终端后端"
---

# 工具与工具集

工具是扩展代理能力的函数。它们被组织成逻辑**工具集**，可以按平台启用或禁用。

## 可用工具

Hermes 附带广泛的内置工具注册表，涵盖网络搜索、浏览器自动化、终端执行、文件编辑、记忆、委托、RL 训练、消息传递、Home Assistant 等。

:::note
**Honcho 跨会话记忆**作为记忆提供程序插件（`plugins/memory/honcho/`）可用，而不是内置工具集。请参阅[插件](./plugins.md)了解安装。
:::

高级类别：

| 类别 | 示例 | 描述 |
|----------|----------|-------------|
| **Web** | `web_search`, `web_extract` | 搜索网络并提取页面内容。 |
| **终端与文件** | `terminal`, `process`, `read_file`, `patch` | 执行命令和操作文件。 |
| **浏览器** | `browser_navigate`, `browser_snapshot`, `browser_vision` | 支持文本和视觉的交互式浏览器自动化。 |
| **媒体** | `vision_analyze`, `image_generate`, `text_to_speech` | 多模态分析和生成。 |
| **代理编排** | `todo`, `clarify`, `execute_code`, `delegate_task` | 规划、澄清、代码执行和子代理委托。 |
| **记忆与召回** | `memory`, `session_search` | 持久记忆和会话搜索。 |
| **自动化与交付** | `cronjob`, `send_message` | 具有创建/列出/更新/暂停/恢复/运行/删除操作的计划任务，以及出站消息传递。 |
| **集成** | `ha_*`, MCP 服务器工具, `rl_*` | Home Assistant、MCP、RL 训练和其他集成。 |

有关权威的代码派生注册表，请参阅[内置工具参考](/docs/reference/tools-reference)和[工具集参考](/docs/reference/toolsets-reference)。

:::tip Nous 工具网关
付费的 [Nous Portal](https://portal.nousresearch.com) 订阅者可以通过**[工具网关](tool-gateway.md)**使用网络搜索、图像生成、TTS 和浏览器自动化 — 无需单独的 API 密钥。运行 `hermes model` 启用它，或使用 `hermes tools` 配置单个工具。
:::

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

请参阅[工具集参考](/docs/reference/toolsets-reference)了解完整集合，包括平台预设，如 `hermes-cli`、`hermes-telegram` 和动态 MCP 工具集，如 `mcp-<server>`。

## 终端后端

终端工具可以在不同环境中执行命令：

| 后端 | 描述 | 用例 |
|---------|-------------|----------|
| `local` | 在您的机器上运行（默认） | 开发、受信任的任务 |
| `docker` | 隔离容器 | 安全性、可重现性 |
| `ssh` | 远程服务器 | 沙箱化，让代理远离自己的代码 |
| `singularity` | HPC 容器 | 集群计算、无根 |
| `modal` | 云端执行 | 无服务器、扩展 |
| `daytona` | 云端沙箱工作区 | 持久化远程开发环境 |

### 配置

```yaml
# 在 ~/.hermes/config.yaml 中
terminal:
  backend: local    # 或：docker, ssh, singularity, modal, daytona
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

推荐用于安全性 — 代理无法修改自己的代码：

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
# 为并行工作者预构建 SIF
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
  container_cpu: 1              # CPU 核心（默认：1）
  container_memory: 5120        # 内存（MB）（默认：5GB）
  container_disk: 51200         # 磁盘（MB）（默认：50GB）
  container_persistent: true    # 跨会话持久化文件系统（默认：true）
```

当 `container_persistent: true` 时，安装的包、文件和配置在会话之间保留。

### 容器安全性

所有容器后端都使用安全强化运行：

- 只读根文件系统（Docker）
- 所有 Linux 功能被删除
- 无权限提升
- PID 限制（256 个进程）
- 完整命名空间隔离
- 通过卷而不是可写根层的持久工作区

Docker 可以选择性地通过 `terminal.docker_forward_env` 接收明确的环境允许列表，但转发的变量对容器内的命令可见，应被视为暴露给该会话。

## 后台进程管理

启动后台进程并管理它们：

```python
terminal(command="pytest -v tests/", background=true)
# 返回：{"session_id": "proc_abc123", "pid": 12345}

# 然后使用进程工具管理：
process(action="list")       # 显示所有运行进程
process(action="poll", session_id="proc_abc123")   # 检查状态
process(action="wait", session_id="proc_abc123")   # 阻塞直到完成
process(action="log", session_id="proc_abc123")    # 完整输出
process(action="kill", session_id="proc_abc123")   # 终止
process(action="write", session_id="proc_abc123", data="y")  # 发送输入
```

PTY 模式（`pty=true`）启用交互式 CLI 工具，如 Codex 和 Claude Code。

## Sudo 支持

如果命令需要 sudo，您将被提示输入密码（会话缓存）。或在 `~/.hermes/.env` 中设置 `SUDO_PASSWORD`。

:::warning
在消息平台上，如果 sudo 失败，输出包括一个提示，将 `SUDO_PASSWORD` 添加到 `~/.hermes/.env`。
:::
