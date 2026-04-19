---
sidebar_position: 2
title: "ACP 内部机制"
description: "ACP 适配器工作原理：生命周期、会话、事件桥接、审批和工具渲染"
---

# ACP 内部机制

ACP 适配器将 Hermes 的同步 `AIAgent` 包装在一个异步 JSON-RPC stdio 服务器中。

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
  -> load ~/.hermes/.env
  -> configure stderr logging
  -> construct HermesACPAgent
  -> acp.run_agent(agent)
```

Stdout 保留给 ACP JSON-RPC 传输。人类可读的日志输出到 stderr。

## 主要组件

### `HermesACPAgent`

`acp_adapter/server.py` 实现了 ACP 代理协议。

职责：

- 初始化 / 身份验证
- 新建/加载/恢复/分支/列出/取消会话方法
- 提示执行
- 会话模型切换
- 将同步 AIAgent 回调连接到 ACP 异步通知

### `SessionManager`

`acp_adapter/session.py` tracks live ACP sessions.

Each session stores:

- `session_id`
- `agent`
- `cwd`
- `model`
- `history`
- `cancel_event`

The manager is thread-safe and supports:

- create
- get
- remove
- fork
- list
- cleanup
- cwd updates

### Event bridge

`acp_adapter/events.py` converts AIAgent callbacks into ACP `session_update` events.

Bridged callbacks:

- `tool_progress_callback`
- `thinking_callback`
- `step_callback`
- `message_callback`

Because `AIAgent` runs in a worker thread while ACP I/O lives on the main event loop, the bridge uses:

```python
asyncio.run_coroutine_threadsafe(...)
```

### Permission bridge

`acp_adapter/permissions.py` adapts dangerous terminal approval prompts into ACP permission requests.

Mapping:

- `allow_once` -> Hermes `once`
- `allow_always` -> Hermes `always`
- reject options -> Hermes `deny`

Timeouts and bridge failures deny by default.

### Tool rendering helpers

`acp_adapter/tools.py` maps Hermes tools to ACP tool kinds and builds editor-facing content.

Examples:

- `patch` / `write_file` -> file diffs
- `terminal` -> shell command text
- `read_file` / `search_files` -> text previews
- large results -> truncated text blocks for UI safety

## Session lifecycle

```text
new_session(cwd)
  -> create SessionState
  -> create AIAgent(platform="acp", enabled_toolsets=["hermes-acp"])
  -> bind task_id/session_id to cwd override

prompt(..., session_id)
  -> extract text from ACP content blocks
  -> reset cancel event
  -> install callbacks + approval bridge
  -> run AIAgent in ThreadPoolExecutor
  -> update session history
  -> emit final agent message chunk
```

### Cancelation

`cancel(session_id)`:

- sets the session cancel event
- calls `agent.interrupt()` when available
- causes the prompt response to return `stop_reason="cancelled"`

### Forking

`fork_session()` deep-copies message history into a new live session, preserving conversation state while giving the fork its own session ID and cwd.

## Provider/auth behavior

ACP does not implement its own auth store.

Instead it reuses Hermes' runtime resolver:

- `acp_adapter/auth.py`
- `hermes_cli/runtime_provider.py`

So ACP advertises and uses the currently configured Hermes provider/credentials.

## Working directory binding

ACP sessions carry an editor cwd.

The session manager binds that cwd to the ACP session ID via task-scoped terminal/file overrides, so file and terminal tools operate relative to the editor workspace.

## Duplicate same-name tool calls

The event bridge tracks tool IDs FIFO per tool name, not just one ID per name. This is important for:

- parallel same-name calls
- repeated same-name calls in one step

Without FIFO queues, completion events would attach to the wrong tool invocation.

## Approval callback restoration

ACP temporarily installs an approval callback on the terminal tool during prompt execution, then restores the previous callback afterward. This avoids leaving ACP session-specific approval handlers installed globally forever.

## Current limitations

- ACP sessions are process-local from the ACP server's point of view
- non-text prompt blocks are currently ignored for request text extraction
- editor-specific UX varies by ACP client implementation

## Related files

- `tests/acp/` — ACP test suite
- `toolsets.py` — `hermes-acp` toolset definition
- `hermes_cli/main.py` — `hermes acp` CLI subcommand
- `pyproject.toml` — `[acp]` optional dependency + `hermes-acp` script