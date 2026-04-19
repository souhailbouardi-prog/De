---
sidebar_position: 8
title: "内存提供程序插件"
description: "如何为 Hermes Agent 构建内存提供程序插件"
---

# 构建内存提供程序插件

内存提供程序插件为 Hermes Agent 提供持久的、跨会话的知识，超越了内置的 MEMORY.md 和 USER.md。本指南介绍如何构建一个内存提供程序插件。

:::tip
内存提供程序是两种**提供程序插件**类型之一。另一种是[上下文引擎插件](/docs/developer-guide/context-engine-plugin)，用于替换内置的上下文压缩器。两者遵循相同的模式：单选、配置驱动、通过 `hermes plugins` 管理。
:::

## 目录结构

每个内存提供程序位于 `plugins/memory/<name>/` 目录中：

```
plugins/memory/my-provider/
├── __init__.py      # MemoryProvider 实现 + register() 入口点
├── plugin.yaml      # 元数据（名称、描述、钩子）
└── README.md        # 设置说明、配置参考、工具
```

## MemoryProvider 抽象基类

你的插件需要实现 `agent/memory_provider.py` 中的 `MemoryProvider` 抽象基类：

```python
from agent.memory_provider import MemoryProvider

class MyMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "my-provider"

    def is_available(self) -> bool:
        """检查此提供程序是否可以激活。不进行网络调用。"""
        return bool(os.environ.get("MY_API_KEY"))

    def initialize(self, session_id: str, **kwargs) -> None:
        """在代理启动时调用一次。

        kwargs 始终包含：
          hermes_home (str): 活动的 HERMES_HOME 路径。用于存储。
        """
        self._api_key = os.environ.get("MY_API_KEY", "")
        self._session_id = session_id

    # ... 实现剩余方法
```

## 必需方法

### 核心生命周期

| 方法 | 调用时机 | 必须实现？ |
|--------|-----------|-----------------|
| `name` (属性) | 始终 | **是** |
| `is_available()` | 代理初始化，激活前 | **是** — 不进行网络调用 |
| `initialize(session_id, **kwargs)` | 代理启动 | **是** |
| `get_tool_schemas()` | 初始化后，用于工具注入 | **是** |
| `handle_tool_call(name, args)` | 当代理使用你的工具时 | **是**（如果你有工具） |

### 配置

| 方法 | 目的 | 必须实现？ |
|--------|---------|-----------------|
| `get_config_schema()` | 为 `hermes memory setup` 声明配置字段 | **是** |
| `save_config(values, hermes_home)` | 将非机密配置写入原生位置 | **是**（除非仅使用环境变量） |

### 可选钩子

| 方法 | 调用时机 | 使用场景 |
|--------|-----------|----------|
| `system_prompt_block()` | 系统提示组装 | 静态提供程序信息 |
| `prefetch(query)` | 每次 API 调用前 | 返回召回的上下文 |
| `queue_prefetch(query)` | 每轮之后 | 为下一轮预热 |
| `sync_turn(user, assistant)` | 每轮完成后 | 持久化对话 |
| `on_session_end(messages)` | 对话结束 | 最终提取/刷新 |
| `on_pre_compress(messages)` | 上下文压缩前 | 在丢弃前保存见解 |
| `on_memory_write(action, target, content)` | 内置内存写入 | 镜像到你的后端 |
| `shutdown()` | 进程退出 | 清理连接 |

## 配置模式

`get_config_schema()` 返回 `hermes memory setup` 使用的字段描述符列表：

```python
def get_config_schema(self):
    return [
        {
            "key": "api_key",
            "description": "My Provider API key",
            "secret": True,           # → 写入 .env
            "required": True,
            "env_var": "MY_API_KEY",   # 显式环境变量名称
            "url": "https://my-provider.com/keys",  # 在哪里获取
        },
        {
            "key": "region",
            "description": "Server region",
            "default": "us-east",
            "choices": ["us-east", "eu-west", "ap-south"],
        },
        {
            "key": "project",
            "description": "Project identifier",
            "default": "hermes",
        },
    ]
```

带有 `secret: True` 和 `env_var` 的字段会写入 `.env`。非机密字段会传递给 `save_config()`。

:::tip 最小模式 vs 完整模式
`get_config_schema()` 中的每个字段都会在 `hermes memory setup` 期间提示用户。具有许多选项的提供程序应保持模式最小化 — 仅包含用户**必须**配置的字段（API 密钥、必需的凭据）。在配置文件参考（例如 `$HERMES_HOME/myprovider.json`）中记录可选设置，而不是在设置期间提示所有选项。这可以保持设置向导快速，同时仍然支持高级配置。请参阅 Supermemory 提供程序的示例 — 它只提示 API 密钥；所有其他选项都在 `supermemory.json` 中。
:::

## 保存配置

```python
def save_config(self, values: dict, hermes_home: str) -> None:
    """将非机密配置写入你的原生位置。"""
    import json
    from pathlib import Path
    config_path = Path(hermes_home) / "my-provider.json"
    config_path.write_text(json.dumps(values, indent=2))
```

对于仅使用环境变量的提供程序，保留默认的空操作。

## 插件入口点

```python
def register(ctx) -> None:
    """由内存插件发现系统调用。"""
    ctx.register_memory_provider(MyMemoryProvider())
```

## plugin.yaml

```yaml
name: my-provider
version: 1.0.0
description: "此提供程序功能的简短描述。"
hooks:
  - on_session_end    # 列出你实现的钩子
```

## 线程约定

**`sync_turn()` 必须是非阻塞的。** 如果你的后端有延迟（API 调用、LLM 处理），请在守护线程中运行工作：

```python
def sync_turn(self, user_content, assistant_content):
    def _sync():
        try:
            self._api.ingest(user_content, assistant_content)
        except Exception as e:
            logger.warning("Sync failed: %s", e)

    if self._sync_thread and self._sync_thread.is_alive():
        self._sync_thread.join(timeout=5.0)
    self._sync_thread = threading.Thread(target=_sync, daemon=True)
    self._sync_thread.start()
```

## 配置文件隔离

所有存储路径**必须**使用 `initialize()` 中的 `hermes_home` 参数，而不是硬编码的 `~/.hermes`：

```python
# 正确 — 配置文件作用域
from hermes_constants import get_hermes_home
data_dir = get_hermes_home() / "my-provider"

# 错误 — 跨所有配置文件共享
data_dir = Path("~/.hermes/my-provider").expanduser()
```

## 测试

请参阅 `tests/agent/test_memory_plugin_e2e.py` 获取使用真实 SQLite 提供程序的完整端到端测试模式。

```python
from agent.memory_manager import MemoryManager

mgr = MemoryManager()
mgr.add_provider(my_provider)
mgr.initialize_all(session_id="test-1", platform="cli")

# 测试工具路由
result = mgr.handle_tool_call("my_tool", {"action": "add", "content": "test"})

# 测试生命周期
mgr.sync_all("user msg", "assistant msg")
mgr.on_session_end([])
mgr.shutdown_all()
```

## 添加 CLI 命令

内存提供程序插件可以注册自己的 CLI 子命令树（例如 `hermes my-provider status`、`hermes my-provider config`）。这使用基于约定的发现系统 — 不需要修改核心文件。

### 工作原理

1. 在插件目录中添加 `cli.py` 文件
2. 定义一个 `register_cli(subparser)` 函数，构建 argparse 树
3. 内存插件系统在启动时通过 `discover_plugin_cli_commands()` 发现它
4. 你的命令会出现在 `hermes <provider-name> <subcommand>` 下

**活动提供程序门控：** 只有当你的提供程序是配置中的活动 `memory.provider` 时，你的 CLI 命令才会出现。如果用户尚未配置你的提供程序，你的命令不会在 `hermes --help` 中显示。

### 示例

```python
# plugins/memory/my-provider/cli.py

def my_command(args):
    """由 argparse 调度的处理程序。"""
    sub = getattr(args, "my_command", None)
    if sub == "status":
        print("Provider is active and connected.")
    elif sub == "config":
        print("Showing config...")
    else:
        print("Usage: hermes my-provider <status|config>")

def register_cli(subparser) -> None:
    """构建 hermes my-provider argparse 树。

    在 argparse 设置时由 discover_plugin_cli_commands() 调用。
    """
    subs = subparser.add_subparsers(dest="my_command")
    subs.add_parser("status", help="Show provider status")
    subs.add_parser("config", help="Show provider config")
    subparser.set_defaults(func=my_command)
```

### 参考实现

请参阅 `plugins/memory/honcho/cli.py` 获取完整示例，包含 13 个子命令、跨配置文件管理（`--target-profile`）和配置读写。

### 带 CLI 的目录结构

```
plugins/memory/my-provider/
├── __init__.py      # MemoryProvider 实现 + register()
├── plugin.yaml      # 元数据
├── cli.py           # register_cli(subparser) — CLI 命令
└── README.md        # 设置说明
```

## 单一提供程序规则

同一时间只能有**一个**外部内存提供程序处于活动状态。如果用户尝试注册第二个，MemoryManager 会拒绝它并发出警告。这可以防止工具模式膨胀和后端冲突。