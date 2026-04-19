---
sidebar_position: 2
title: "ACP 内部原理"
description: "ACP 适配器如何工作：生命周期、会话、事件桥接、审批和工具渲染"
---

# ACP 内部原理

ACP 适配器将 Hermes 的同步 `AIAgent` 包装在异步 JSON-RPC stdio 服务器中。

关键实现文件：

- `acp_adapter/entry.py`
- `acp_adapter/server.py`
- `acp_adapter/session.py`
- `acp_adapter/events.py`
- `acp_adapter/permissions.py`
- `acp_adapter/tools.py`
- `acp_adapter/auth.py`
- `acp_registry/agent.json`

## 启动流程

```text
hermes acp / hermes-acp / python -m acp_adapter
  -> acp_adapter.entry.main()
  -> 加载 ~/.hermes/.env
  -> 配置 stderr 日志
  -> 构建 HermesACPAgent
  -> acp.run_agent(agent)
```

stdout 保留给 ACP JSON-RPC 传输。人类可读的日志发送到 stderr。

## 主要组件

### `HermesACPAgent`

`acp_adapter/server.py` 实现 ACP 代理协议。

职责：

- 初始化 / 认证
- 新/加载/恢复/分叉/列出/取消会话方法
- 提示执行
- 会话模型切换
- 将同步 AIAgent 回调连接到 ACP 异步通知

### `SessionManager`

`acp_adapter/session.py` 跟踪活动的 ACP 会话。

每个会话存储：

- `session_id`
- `agent`
- `cwd`
- `model`
- `history`
- `cancel_event`

管理器是线程安全的，支持：

- 创建
- 获取
- 删除
- 分叉
- 列出
- 清理
- cwd 更新

### 事件桥接

`acp_adapter/events.py` 将 AIAgent 回调转换为 ACP `session_update` 事件。

桥接的回调：

- `tool_progress_callback`
- `thinking_callback`
- `step_callback`
- `message_callback`

由于 `AIAgent` 在工作线程中运行，而 ACP I/O 位于主事件循环上，桥接使用：

```python
asyncio.run_coroutine_threadsafe(...)
```

### 权限桥接

`acp_adapter/permissions.py` 将危险的终端审批提示适配为 ACP 权限请求。

映射：

- `allow_once` -> Hermes `once`
- `allow_always` -> Hermes `always`
- 拒绝选项 -> Hermes `deny`

超时和桥接失败默认拒绝。

### 工具渲染助手

`acp_adapter/tools.py` 将 Hermes 工具映射到 ACP 工具类型并构建面向编辑器的内容。

示例：

- `patch` / `write_file` -> 文件差异
- `terminal` -> shell 命令文本
- `read_file` / `search_files` -> 文本预览
- 大结果 -> 为 UI 安全截断文本块

## 会话生命周期

```text
new_session(cwd)
  -> 创建 SessionState
  -> 创建 AIAgent(platform="acp", enabled_toolsets=["hermes-acp"])
  -> 将 task_id/session_id 绑定到 cwd 覆盖

prompt(..., session_id)
  -> 从 ACP 内容块提取文本
  -> 重置取消事件
  -> 安装回调 + 审批桥接
  -> 在 ThreadPoolExecutor 中运行 AIAgent
  -> 更新会话历史
  -> 发出最终代理消息块
```

### 取消

`cancel(session_id)`:

- 设置会话取消事件
- 当可用时调用 `agent.interrupt()`
- 导致提示响应返回 `stop_reason="cancelled"`

### 分叉

`fork_session()` 将消息历史深度复制到新的活动会话中，保留对话状态，同时为分叉提供自己的会话 ID 和 cwd。

## 提供商/认证行为

ACP 不实现自己的认证存储。

相反，它重用 Hermes 的运行时解析器：

- `acp_adapter/auth.py`
- `hermes_cli/runtime_provider.py`

因此，ACP 宣传并使用当前配置的 Hermes 提供商/凭证。

## 工作目录绑定

ACP 会话携带编辑器 cwd。

会话管理器通过任务范围的终端/文件覆盖将该 cwd 绑定到 ACP 会话 ID，因此文件和终端工具相对于编辑器工作区操作。

## 同名工具调用重复

事件桥接按工具名称 FIFO 跟踪工具 ID，而不仅仅是每个名称一个 ID。这对于以下情况很重要：

- 并行同名调用
- 一步中重复同名调用

没有 FIFO 队列，完成事件会附加到错误的工具调用。

## 审批回调恢复

ACP 在提示执行期间临时在终端工具上安装审批回调，然后在之后恢复之前的回调。这避免了将 ACP 会话特定的审批处理程序永久全局安装。

## 当前限制

- 从 ACP 服务器的角度来看，ACP 会话是进程本地的
- 当前忽略非文本提示块以进行请求文本提取
- 编辑器特定的 UX 因 ACP 客户端实现而异

## 相关文件

- `tests/acp/` — ACP 测试套件
- `toolsets.py` — `hermes-acp` 工具集定义
- `hermes_cli/main.py` — `hermes acp` CLI 子命令
- `pyproject.toml` — `[acp]` 可选依赖 + `hermes-acp` 脚本
