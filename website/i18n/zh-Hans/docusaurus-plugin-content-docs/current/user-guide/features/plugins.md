---
sidebar_position: 11
sidebar_label: "插件"
title: "插件"
description: "通过插件系统使用自定义工具、钩子和集成扩展 Hermes"
---

# 插件

Hermes 有一个插件系统，用于在不修改核心代码的情况下添加自定义工具、钩子和集成。

**→ [构建 Hermes 插件](/docs/guides/build-a-hermes-plugin)** — 包含完整工作示例的分步指南。

## 快速概览

将包含 `plugin.yaml` 和 Python 代码的目录放入 `~/.hermes/plugins/`：

```
~/.hermes/plugins/my-plugin/
├── plugin.yaml      # 清单
├── __init__.py      # register() — 将模式连接到处理程序
├── schemas.py       # 工具模式（LLM 看到的内容）
└── tools.py         # 工具处理程序（调用时运行的内容）
```

启动 Hermes — 您的工具会与内置工具一起出现。模型可以立即调用它们。

### 最小工作示例

这是一个完整的插件，添加了 `hello_world` 工具并通过钩子记录每次工具调用。

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

将两个文件放入 `~/.hermes/plugins/hello-world/`，重启 Hermes，模型可以立即调用 `hello_world`。钩子在每次工具调用后打印日志行。

项目本地插件在 `./.hermes/plugins/` 下默认禁用。通过在启动 Hermes 前设置 `HERMES_ENABLE_PROJECT_PLUGINS=true`，只为受信任的存储库启用它们。

## 插件可以做什么

| 功能 | 方法 |
|-----------|-----|
| 添加工具 | `ctx.register_tool(name, schema, handler)` |
| 添加钩子 | `ctx.register_hook("post_tool_call", callback)` |
| 添加 CLI 命令 | `ctx.register_cli_command(name, help, setup_fn, handler_fn)` — 添加 `hermes <plugin> <subcommand>` |
| 注入消息 | `ctx.inject_message(content, role="user")` — 参见 [注入消息](#injecting-messages) |
| 附带数据文件 | `Path(__file__).parent / "data" / "file.yaml"` |
| 捆绑技能 | `ctx.register_skill(name, path)` — 命名空间为 `plugin:skill`，通过 `skill_view("plugin:skill")` 加载 |
| 基于环境变量的门控 | plugin.yaml 中的 `requires_env: [API_KEY]` — 在 `hermes plugins install` 期间提示 |
| 通过 pip 分发 | `[project.entry-points."hermes_agent.plugins"]` |

## 可用钩子

插件可以为这些生命周期事件注册回调。有关完整详细信息、回调签名和示例，请参阅 **[事件钩子页面](/docs/user-guide/features/hooks#plugin-hooks)**。

| 钩子 | 触发时机 |
|------|-----------|
| [`pre_tool_call`](/docs/user-guide/features/hooks#pre_tool_call) | 任何工具执行前 |
| [`post_tool_call`](/docs/user-guide/features/hooks#post_tool_call) | 任何工具返回后 |
| [`pre_llm_call`](/docs/user-guide/features/hooks#pre_llm_call) | 每轮一次，LLM 循环前 — 可以返回 `{"context": "..."}` 来 [向用户消息注入上下文](/docs/user-guide/features/hooks#pre_llm_call) |
| [`post_llm_call`](/docs/user-guide/features/hooks#post_llm_call) | 每轮一次，LLM 循环后（仅限成功轮次） |
| [`on_session_start`](/docs/user-guide/features/hooks#on_session_start) | 创建新会话时（仅第一轮） |
| [`on_session_end`](/docs/user-guide/features/hooks#on_session_end) | 每次 `run_conversation` 调用结束 + CLI 退出处理程序 |

## 插件类型

Hermes 有三种类型的插件：

| 类型 | 功能 | 选择 | 位置 |
|------|-------------|-----------|----------|
| **通用插件** | 添加工具、钩子、CLI 命令 | 多选（启用/禁用） | `~/.hermes/plugins/` |
| **内存提供商** | 替换或增强内置内存 | 单选（一个活动） | `plugins/memory/` |
| **上下文引擎** | 替换内置上下文压缩器 | 单选（一个活动） | `plugins/context_engine/` |

内存提供商和上下文引擎是 **提供商插件** — 每种类型一次只能有一个处于活动状态。通用插件可以以任何组合启用。

## 管理插件

```bash
hermes plugins                  # 统一交互式 UI
hermes plugins list             # 带启用/禁用状态的表格视图
hermes plugins install user/repo  # 从 Git 安装
hermes plugins update my-plugin   # 拉取最新版本
hermes plugins remove my-plugin   # 卸载
hermes plugins enable my-plugin   # 重新启用已禁用的插件
hermes plugins disable my-plugin  # 禁用但不删除
```

### 交互式 UI

运行不带参数的 `hermes plugins` 会打开一个复合交互式屏幕：

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

- **通用插件部分** — 复选框，按空格键切换
- **提供商插件部分** — 显示当前选择。按 ENTER 进入单选选择器，选择一个活动提供商。

提供商插件选择保存在 `config.yaml` 中：

```yaml
memory:
  provider: "honcho"      # 空字符串 = 仅内置

context:
  engine: "compressor"    # 默认内置压缩器
```

### 禁用通用插件

已禁用的插件保持安装状态，但在加载期间会被跳过。禁用列表存储在 `config.yaml` 的 `plugins.disabled` 下：

```yaml
plugins:
  disabled:
    - my-noisy-plugin
```

在运行会话中，`/plugins` 显示当前加载了哪些插件。

## 注入消息

插件可以使用 `ctx.inject_message()` 向活动对话注入消息：

```python
ctx.inject_message("New data arrived from the webhook", role="user")
```

**签名：** `ctx.inject_message(content: str, role: str = "user") -> bool`

工作原理：

- 如果代理**空闲**（等待用户输入），消息会被排队作为下一个输入并开始新一轮。
- 如果代理**正在转弯**（积极运行），消息会中断当前操作 — 就像用户键入新消息并按 Enter 一样。
- 对于非 `"user"` 角色，内容会以 `[role]` 为前缀（例如 `[system] ...`）。
- 如果消息成功排队，返回 `True`；如果没有可用的 CLI 引用（例如在网关模式下），返回 `False`。

这使远程控制查看器、消息桥或 webhook 接收器等插件能够从外部源向对话馈送消息。

:::note
`inject_message` 仅在 CLI 模式下可用。在网关模式下，没有 CLI 引用，该方法返回 `False`。
:::

有关处理程序契约、模式格式、钩子行为、错误处理和常见错误，请参阅 **[完整指南](/docs/guides/build-a-hermes-plugin)**。