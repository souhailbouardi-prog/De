---
sidebar_position: 11
sidebar_label: "插件"
title: "插件"
description: "通过插件系统使用自定义工具、钩子和集成来扩展 Hermes"
---

# 插件

Hermes 有一个插件系统，用于添加自定义工具、钩子和集成，而无需修改核心代码。

**→ [构建 Hermes 插件](/docs/guides/build-a-hermes-plugin)** — 带有完整工作示例的分步指南。

## 快速概述

将目录放入 `~/.hermes/plugins/`，包含 `plugin.yaml` 和 Python 代码：

```
~/.hermes/plugins/my-plugin/
├── plugin.yaml      # 清单
├── __init__.py      # register() — 将架构连接到处理程序
├── schemas.py       # 工具架构（LLM 看到的）
└── tools.py         # 工具处理程序（调用时运行的）
```

启动 Hermes — 您的工具与内置工具一起出现。模型可以立即调用它们。

### 最小工作示例

这是一个完整的插件，添加了 `hello_world` 工具并通过钩子记录每个工具调用。

**`~/.hermes/plugins/hello-world/plugin.yaml`**

```yaml
name: hello-world
version: "1.0"
description: A minimal example plugin
```

**`~/.hermes/plugins/hello-world/__init__.py`**

```python
"""Minimal Hermes plugin — registers a tool and a hook."""


def register(ctx):
    # --- Tool: hello_world ---
    schema = {
        "name": "hello_world",
        "description": "Returns a friendly greeting for the given name.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet",
                }
            },
            "required": ["name"],
        },
    }

    def handle_hello(params):
        name = params.get("name", "World")
        return f"Hello, {name}! 👋  (from the hello-world plugin)"

    ctx.register_tool("hello_world", schema, handle_hello)

    # --- Hook: log every tool call ---
    def on_tool_call(tool_name, params, result):
        print(f"[hello-world] tool called: {tool_name}")

    ctx.register_hook("post_tool_call", on_tool_call)
```

将两个文件放入 `~/.hermes/plugins/hello-world/`，重启 Hermes，模型可以立即调用 `hello_world`。钩子在每次工具调用后打印一个日志行。

默认情况下禁用 `./.hermes/plugins/` 下的项目本地插件。仅在启动 Hermes 之前通过设置 `HERMES_ENABLE_PROJECT_PLUGINS=true` 为受信任的存储库启用它们。

## 插件可以做什么

| 功能 | 如何 |
|-----------|-----|
| 添加工具 | `ctx.register_tool(name, schema, handler)` |
| 添加钩子 | `ctx.register_hook("post_tool_call", callback)` |
| 添加斜杠命令 | `ctx.register_command(name, handler, description)` — 在 CLI 和网关会话中添加 `/name` |
| 添加 CLI 命令 | `ctx.register_cli_command(name, help, setup_fn, handler_fn)` — 添加 `hermes <plugin> <subcommand>` |
| 注入消息 | `ctx.inject_message(content, role="user")` — 请参阅[注入消息](#注入消息) |
| 附带数据文件 | `Path(__file__).parent / "data" / "file.yaml"` |
| 捆绑技能 | `ctx.register_skill(name, path)` — 命名空间为 `plugin:skill`，通过 `skill_view("plugin:skill")` 加载 |
| 在环境变量上门控 | plugin.yaml 中的 `requires_env: [API_KEY]` — 在 `hermes plugins install` 期间提示 |
| 通过 pip 分发 | `[project.entry-points."hermes_agent.plugins"]` |

## 插件发现

| 来源 | 路径 | 用例 |
|--------|------|----------|
| 用户 | `~/.hermes/plugins/` | 个人插件 |
| 项目 | `.hermes/plugins/` | 项目特定插件（需要 `HERMES_ENABLE_PROJECT_PLUGINS=true`） |
| pip | `hermes_agent.plugins` 入口点 | 分布式包 |

## 可用钩子

插件可以为这些生命周期事件注册回调。请参阅**[事件钩子页面](/docs/user-guide/features/hooks#插件钩子)**获取完整详细信息、回调签名和示例。

| 钩子 | 何时触发 |
|------|-----------|
| [`pre_tool_call`](/docs/user-guide/features/hooks#pre_tool_call) | 在任何工具执行之前 |
| [`post_tool_call`](/docs/user-guide/features/hooks#post_tool_call) | 在任何工具返回之后 |
| [`pre_llm_call`](/docs/user-guide/features/hooks#pre_llm_call) | 每个回合一次，在 LLM 循环之前 — 可以返回 `{"context": "..."}` 以[将上下文注入到用户消息中](/docs/user-guide/features/hooks#pre_llm_call) |
| [`post_llm_call`](/docs/user-guide/features/hooks#post_llm_call) | 每个回合一次，在 LLM 循环之后（仅成功的回合） |
| [`on_session_start`](/docs/user-guide/features/hooks#on_session_start) | 新会话已创建（仅第一回合） |
| [`on_session_end`](/docs/user-guide/features/hooks#on_session_end) | 每次 `run_conversation` 调用结束 + CLI 退出处理程序 |

## 插件类型

Hermes 有三种插件：

| 类型 | 它做什么 | 选择 | 位置 |
|------|-------------|-----------|----------|
| **通用插件** | 添加工具、钩子、斜杠命令、CLI 命令 | 多选（启用/禁用） | `~/.hermes/plugins/` |
| **记忆提供程序** | 替换或扩充内置记忆 | 单选（一个活动） | `plugins/memory/` |
| **上下文引擎** | 替换内置上下文压缩器 | 单选（一个活动） | `plugins/context_engine/` |

记忆提供程序和上下文引擎是**提供程序插件** — 每种类型一次只能有一个活动。通用插件可以以任何组合启用。

## 管理插件

```bash
hermes plugins                  # 统一交互式 UI
hermes plugins list             # 带启用/禁用状态的表格视图
hermes plugins install user/repo  # 从 Git 安装
hermes plugins update my-plugin   # 拉取最新
hermes plugins remove my-plugin   # 卸载
hermes plugins enable my-plugin   # 重新启用禁用的插件
hermes plugins disable my-plugin  # 禁用而不删除
```

### 交互式 UI

不带参数运行 `hermes plugins` 会打开一个复合交互式屏幕：

```
Plugins
  ↑↓ navigate  SPACE toggle  ENTER configure/confirm  ESC done

  General Plugins
 → [✓] my-tool-plugin — Custom search tool
   [ ] webhook-notifier — Event hooks

  Provider Plugins
     Memory Provider          ▸ honcho
     Context Engine           ▸ compressor
```

- **通用插件部分** — 复选框，使用 SPACE 切换
- **提供程序插件部分** — 显示当前选择。按 ENTER 深入到单选选择器，在其中选择一个活动的提供程序。

提供程序插件选择保存到 `config.yaml`：

```yaml
memory:
  provider: "honcho"      # 空字符串 = 仅内置

context:
  engine: "compressor"    # 默认内置压缩器
```

### 禁用通用插件

禁用的插件保持安装但在加载期间被跳过。禁用列表存储在 `config.yaml` 的 `plugins.disabled` 下：

```yaml
plugins:
  disabled:
    - my-noisy-plugin
```

在运行的会话中，`/plugins` 显示当前加载了哪些插件。

## 注入消息

插件可以使用 `ctx.inject_message()` 将消息注入到活动对话中：

```python
ctx.inject_message("New data arrived from the webhook", role="user")
```

**签名：** `ctx.inject_message(content: str, role: str = "user") -> bool`

工作原理：

- 如果代理**空闲**（等待用户输入），消息被排队作为下一个输入并启动新回合。
- 如果代理**回合中**（正在运行），消息会中断当前操作 — 与用户键入新消息并按 Enter 相同。
- 对于非 `"user"` 角色，内容以 `[role]` 为前缀（例如 `[system] ...`）。
- 如果消息成功排队，则返回 `True`，如果没有可用的 CLI 引用（例如在网关模式下），则返回 `False`。

这使远程控制查看器、消息桥接器或 webhook 接收器等插件能够从外部源向对话提供消息。

:::note
`inject_message` 仅在 CLI 模式下可用。在网关模式下，没有 CLI 引用，该方法返回 `False`。
:::

请参阅**[完整指南](/docs/guides/build-a-hermes-plugin)**获取处理程序契约、架构格式、钩子行为、错误处理和常见错误。
