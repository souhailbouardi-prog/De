# Hermes Agent - 开发指南

面向在 hermes-agent 代码库上工作的 AI 编码助手和开发人员的指南。

## 开发环境

```bash
source venv/bin/activate  # 运行 Python 前始终激活
```

## 项目结构

```
hermes-agent/
├── run_agent.py          # AIAgent 类 — 核心对话循环
├── model_tools.py        # 工具编排，discover_builtin_tools(), handle_function_call()
├── toolsets.py           # 工具集定义，_HERMES_CORE_TOOLS 列表
├── cli.py                # HermesCLI 类 — 交互式 CLI 编排器
├── hermes_state.py       # SessionDB — SQLite 会话存储（FTS5 搜索）
├── agent/                # 代理内部
│   ├── prompt_builder.py     # 系统提示组装
│   ├── context_compressor.py # 自动上下文压缩
│   ├── prompt_caching.py     # Anthropic 提示缓存
│   ├── auxiliary_client.py   # 辅助 LLM 客户端（视觉、摘要）
│   ├── model_metadata.py     # 模型上下文长度、令牌估计
│   ├── models_dev.py         # models.dev 注册表集成（提供商感知上下文）
│   ├── display.py            # KawaiiSpinner，工具预览格式化
│   ├── skill_commands.py     # 技能斜杠命令（共享 CLI/网关）
│   └── trajectory.py         # 轨迹保存助手
├── hermes_cli/           # CLI 子命令和设置
│   ├── main.py           # 入口点 — 所有 `hermes` 子命令
│   ├── config.py         # DEFAULT_CONFIG, OPTIONAL_ENV_VARS, 迁移
│   ├── commands.py       # 斜杠命令定义 + SlashCommandCompleter
│   ├── callbacks.py      # 终端回调（澄清、sudo、批准）
│   ├── setup.py          # 交互式设置向导
│   ├── skin_engine.py    # 皮肤/主题引擎 — CLI 视觉定制
│   ├── skills_config.py  # `hermes skills` — 按平台启用/禁用技能
│   ├── tools_config.py   # `hermes tools` — 按平台启用/禁用工具
│   ├── skills_hub.py     # `/skills` 斜杠命令（搜索、浏览、安装）
│   ├── models.py         # 模型目录，提供商模型列表
│   ├── model_switch.py   # 共享 /model 切换管道（CLI + 网关）
│   └── auth.py           # 提供商凭据解析
├── tools/                # 工具实现（每个工具一个文件）
│   ├── registry.py       # 中央工具注册表（架构、处理程序、调度）
│   ├── approval.py       # 危险命令检测
│   ├── terminal_tool.py  # 终端编排
│   ├── process_registry.py # 后台进程管理
│   ├── file_tools.py     # 文件读/写/搜索/补丁
│   ├── web_tools.py      # 网络搜索/提取（Parallel + Firecrawl）
│   ├── browser_tool.py   # Browserbase 浏览器自动化
│   ├── code_execution_tool.py # execute_code 沙箱
│   ├── delegate_tool.py  # 子代理委托
│   ├── mcp_tool.py       # MCP 客户端（~1050 行）
│   └── environments/     # 终端后端（local, docker, ssh, modal, daytona, singularity）
├── gateway/              # 消息平台网关
│   ├── run.py            # 主循环，斜杠命令，消息调度
│   ├── session.py        # SessionStore — 对话持久性
│   └── platforms/        # 适配器：telegram, discord, slack, whatsapp, homeassistant, signal, qqbot
├── ui-tui/               # Ink（React）终端 UI — `hermes --tui`
│   ├── src/entry.tsx        # TTY 门 + render()
│   ├── src/app.tsx          # 主状态机和 UI
│   ├── src/gatewayClient.ts # 子进程 + JSON-RPC 桥接
│   ├── src/app/             # 分解的应用逻辑（事件处理程序、斜杠处理程序、存储、钩子）
│   ├── src/components/      # Ink 组件（品牌、markdown、提示、选择器等）
│   ├── src/hooks/           # useCompletion, useInputHistory, useQueue, useVirtualHistory
│   └── src/lib/             # 纯辅助函数（历史、osc52、文本、rpc、消息）
├── tui_gateway/          # TUI 的 Python JSON-RPC 后端
│   ├── entry.py             # stdio 入口点
│   ├── server.py            # RPC 处理程序和会话逻辑
│   ├── render.py            # 可选的 rich/ANSI 桥接
│   └── slash_worker.py      # 用于斜杠命令的持久 HermesCLI 子进程
├── acp_adapter/          # ACP 服务器（VS Code / Zed / JetBrains 集成）
├── cron/                 # 调度器（jobs.py, scheduler.py）
├── environments/         # RL 训练环境（Atropos）
├── tests/                # Pytest 套件（~3000 个测试）
└── batch_runner.py       # 并行批处理
```

**用户配置：** `~/.hermes/config.yaml`（设置），`~/.hermes/.env`（API 密钥）

## 文件依赖链

```
tools/registry.py （无依赖 — 被所有工具文件导入）
       ↑
tools/*.py （每个在导入时调用 registry.register()）
       ↑
model_tools.py （导入 tools/registry + 触发工具发现）
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

---

## AIAgent 类（run_agent.py）

```python
class AIAgent:
    def __init__(self,
        model: str = "anthropic/claude-opus-4.6",
        max_iterations: int = 90,
        enabled_toolsets: list = None,
        disabled_toolsets: list = None,
        quiet_mode: bool = False,
        save_trajectories: bool = False,
        platform: str = None,           # "cli", "telegram", etc.
        session_id: str = None,
        skip_context_files: bool = False,
        skip_memory: bool = False,
        # ... 加上 provider, api_mode, callbacks, routing params
    ): ...

    def chat(self, message: str) -> str:
        """简单接口 — 返回最终响应字符串。"""

    def run_conversation(self, user_message: str, system_message: str = None,
                         conversation_history: list = None, task_id: str = None) -> dict:
        """完整接口 — 返回包含 final_response + messages 的字典。"""
```

### 代理循环

核心循环在 `run_conversation()` 内部 — 完全同步：

```python
while api_call_count < self.max_iterations and self.iteration_budget.remaining > 0:
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```

消息遵循 OpenAI 格式：`{"role": "system/user/assistant/tool", ...}`。推理内容存储在 `assistant_msg["reasoning"]` 中。

---

## CLI 架构（cli.py）

- **Rich** 用于横幅/面板，**prompt_toolkit** 用于带自动完成的输入
- **KawaiiSpinner**（`agent/display.py`）— API 调用期间的动画面孔，工具结果的 `┊` 活动 feed
- `load_cli_config()` 在 cli.py 中合并硬编码默认值 + 用户配置 YAML
- **皮肤引擎**（`hermes_cli/skin_engine.py`）— 数据驱动的 CLI 主题；在启动时从 `display.skin` 配置键初始化；皮肤自定义横幅颜色、微调器面孔/动词/翅膀、工具前缀、响应框、品牌文本
- `process_command()` 是 `HermesCLI` 上的方法 — 对通过中央注册表的 `resolve_command()` 解析的规范命令名进行调度
- 技能斜杠命令：`agent/skill_commands.py` 扫描 `~/.hermes/skills/`，注入为**用户消息**（不是系统提示）以保持提示缓存

### 斜杠命令注册表（`hermes_cli/commands.py`）

所有斜杠命令在 `CommandDef` 对象的中央 `COMMAND_REGISTRY` 列表中定义。每个下游消费者自动从该注册表派生：

- **CLI** — `process_command()` 通过 `resolve_command()` 解析别名，对规范名称进行调度
- **网关** — `GATEWAY_KNOWN_COMMANDS` 冻结集用于钩子发射，`resolve_command()` 用于调度
- **网关帮助** — `gateway_help_lines()` 生成 `/help` 输出
- **Telegram** — `telegram_bot_commands()` 生成 BotCommand 菜单
- **Slack** — `slack_subcommand_map()` 生成 `/hermes` 子命令路由
- **自动完成** — `COMMANDS` 扁平字典提供给 `SlashCommandCompleter`
- **CLI 帮助** — `COMMANDS_BY_CATEGORY` 字典提供给 `show_help()`

### 添加斜杠命令

1. 在 `hermes_cli/commands.py` 中的 `COMMAND_REGISTRY` 添加 `CommandDef` 条目：
```python
CommandDef("mycommand", "它的功能描述", "Session",
           aliases=("mc",), args_hint="[arg]"),
```
2. 在 `cli.py` 的 `HermesCLI.process_command()` 中添加处理程序：
```python
elif canonical == "mycommand":
    self._handle_mycommand(cmd_original)
```
3. 如果命令在网关中可用，在 `gateway/run.py` 中添加处理程序：
```python
if canonical == "mycommand":
    return await self._handle_mycommand(event)
```
4. 对于持久设置，使用 `cli.py` 中的 `save_config_value()`

**CommandDef 字段：**
- `name` — 不带斜杠的规范名称（例如 `"background"`）
- `description` — 人类可读的描述
- `category` — 以下之一：`"Session"`, `"Configuration"`, `"Tools & Skills"`, `"Info"`, `"Exit"`
- `aliases` — 替代名称元组（例如 `("bg",)`）
- `args_hint` — 帮助中显示的参数占位符（例如 `"<prompt>"`, `"[name]"`）
- `cli_only` — 仅在交互式 CLI 中可用
- `gateway_only` — 仅在消息平台中可用
- `gateway_config_gate` — 配置点路径（例如 `"display.tool_progress_command"`）；当在 `cli_only` 命令上设置时，如果配置值为真，则该命令在网关中可用。`GATEWAY_KNOWN_COMMANDS` 始终包含配置门控命令，以便网关可以调度它们；帮助/菜单仅在门打开时显示它们。

**添加别名** 只需要将其添加到现有 `CommandDef` 的 `aliases` 元组中。无需其他文件更改 — 调度、帮助文本、Telegram 菜单、Slack 映射和自动完成都会自动更新。

---

## TUI 架构（ui-tui + tui_gateway）

TUI 是经典（prompt_toolkit）CLI 的完整替代品，通过 `hermes --tui` 或 `HERMES_TUI=1` 激活。

### 进程模型

```
hermes --tui
  └─ Node (Ink)  ──stdio JSON-RPC──  Python (tui_gateway)
       │                                  └─ AIAgent + tools + sessions
       └─ renders transcript, composer, prompts, activity
```

TypeScript 负责屏幕。Python 负责会话、工具、模型调用和斜杠命令逻辑。

### 传输

通过 stdio 的换行分隔 JSON-RPC。来自 Ink 的请求，来自 Python 的事件。有关完整的方法/事件目录，请参阅 `tui_gateway/server.py`。

### 关键界面

| 界面 | Ink 组件 | 网关方法 |
|------|----------|----------|
| 聊天流 | `app.tsx` + `messageLine.tsx` | `prompt.submit` → `message.delta/complete` |
| 工具活动 | `thinking.tsx` | `tool.start/progress/complete` |
| 批准 | `prompts.tsx` | `approval.respond` ← `approval.request` |
| 澄清/ sudo/ 秘密 | `prompts.tsx`, `maskedPrompt.tsx` | `clarify/sudo/secret.respond` |
| 会话选择器 | `sessionPicker.tsx` | `session.list/resume` |
| 斜杠命令 | 本地处理程序 + 回退 | `slash.exec` → `_SlashWorker`, `command.dispatch` |
| 完成 | `useCompletion` 钩子 | `complete.slash`, `complete.path` |
| 主题 | `theme.ts` + `branding.tsx` | `gateway.ready` 带皮肤数据 |

### 斜杠命令流程

1. 内置客户端命令（`/help`, `/quit`, `/clear`, `/resume`, `/copy`, `/paste` 等）在 `app.tsx` 中本地处理
2. 其他所有 → `slash.exec`（在持久 `_SlashWorker` 子进程中运行）→ `command.dispatch` 回退

### 开发命令

```bash
cd ui-tui
npm install       # 首次
npm run dev       # 监视模式（重建 hermes-ink + tsx --watch）
npm start         # 生产
npm run build     # 完整构建（hermes-ink + tsc）
npm run type-check # 仅类型检查（tsc --noEmit）
npm run lint      # eslint
npm run fmt       # prettier
npm test          # vitest
```

---

## 添加新工具

需要在 **2 个文件** 中进行更改：

**1. 创建 `tools/your_tool.py`：**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. 添加到 `toolsets.py`** — 要么 `_HERMES_CORE_TOOLS`（所有平台），要么新工具集。

自动发现：任何带有顶级 `registry.register()` 调用的 `tools/*.py` 文件都会被自动导入 — 无需维护手动导入列表。

注册表处理架构收集、调度、可用性检查和错误包装。所有处理程序必须返回 JSON 字符串。

**工具架构中的路径引用**：如果架构描述提及文件路径（例如默认输出目录），使用 `display_hermes_home()` 使其具有配置文件感知能力。架构在导入时生成，这是在 `_apply_profile_override()` 设置 `HERMES_HOME` 之后。

**状态文件**：如果工具存储持久状态（缓存、日志、检查点），使用 `get_hermes_home()` 作为基目录 — 永远不要使用 `Path.home() / ".hermes"`。这确保每个配置文件都有自己的状态。

**代理级工具**（todo, memory）：在 `handle_function_call()` 之前被 `run_agent.py` 拦截。有关模式，请参阅 `todo_tool.py`。

---

## 添加配置

### config.yaml 选项：
1. 添加到 `hermes_cli/config.py` 中的 `DEFAULT_CONFIG`
2. 增加 `_config_version`（当前为 5）以触发现有用户的迁移

### .env 变量：
1. 添加到 `hermes_cli/config.py` 中的 `OPTIONAL_ENV_VARS` 并带有元数据：
```python
"NEW_API_KEY": {
    "description": "它的用途",
    "prompt": "显示名称",
    "url": "https://...",
    "password": True,
    "category": "tool",  # provider, tool, messaging, setting
},
```

### 配置加载器（两个独立系统）：

| 加载器 | 使用者 | 位置 |
|--------|--------|------|
| `load_cli_config()` | CLI 模式 | `cli.py` |
| `load_config()` | `hermes tools`, `hermes setup` | `hermes_cli/config.py` |
| 直接 YAML 加载 | 网关 | `gateway/run.py` |

---

## 皮肤/主题系统

皮肤引擎（`hermes_cli/skin_engine.py`）提供数据驱动的 CLI 视觉定制。皮肤是**纯数据** — 添加新皮肤不需要代码更改。

### 架构

```
hermes_cli/skin_engine.py    # SkinConfig 数据类，内置皮肤，YAML 加载器
~/.hermes/skins/*.yaml       # 用户安装的自定义皮肤（即插即用）
```

- `init_skin_from_config()` — 在 CLI 启动时调用，从配置中读取 `display.skin`
- `get_active_skin()` — 返回当前皮肤的缓存 `SkinConfig`
- `set_active_skin(name)` — 在运行时切换皮肤（由 `/skin` 命令使用）
- `load_skin(name)` — 首先从用户皮肤加载，然后是内置皮肤，最后回退到默认值
- 缺失的皮肤值自动从 `default` 皮肤继承

### 皮肤自定义内容

| 元素 | 皮肤键 | 使用者 |
|------|--------|--------|
| 横幅面板边框 | `colors.banner_border` | `banner.py` |
| 横幅面板标题 | `colors.banner_title` | `banner.py` |
| 横幅部分标题 | `colors.banner_accent` | `banner.py` |
| 横幅暗淡文本 | `colors.banner_dim` | `banner.py` |
| 横幅正文文本 | `colors.banner_text` | `banner.py` |
| 响应框边框 | `colors.response_border` | `cli.py` |
| 微调器面孔（等待） | `spinner.waiting_faces` | `display.py` |
| 微调器面孔（思考） | `spinner.thinking_faces` | `display.py` |
| 微调器动词 | `spinner.thinking_verbs` | `display.py` |
| 微调器翅膀（可选） | `spinner.wings` | `display.py` |
| 工具输出前缀 | `tool_prefix` | `display.py` |
| 每个工具的表情符号 | `tool_emojis` | `display.py` → `get_tool_emoji()` |
| 代理名称 | `branding.agent_name` | `banner.py`, `cli.py` |
| 欢迎消息 | `branding.welcome` | `cli.py` |
| 响应框标签 | `branding.response_label` | `cli.py` |
| 提示符号 | `branding.prompt_symbol` | `cli.py` |

### 内置皮肤

- `default` — 经典 Hermes 金色/卡哇伊（当前外观）
- `ares` — 深红色/青铜战神主题，带有自定义微调器翅膀
- `mono` — 干净的灰度单色
- `slate` — 冷蓝色开发者专注主题

### 添加内置皮肤

添加到 `hermes_cli/skin_engine.py` 中的 `_BUILTIN_SKINS` 字典：

```python
"mytheme": {
    "name": "mytheme",
    "description": "简短描述",
    "colors": { ... },
    "spinner": { ... },
    "branding": { ... },
    "tool_prefix": "┊",
},
```

### 用户皮肤（YAML）

用户创建 `~/.hermes/skins/<name>.yaml`：

```yaml
name: cyberpunk
description: 霓虹浸泡的终端主题

colors:
  banner_border: "#FF00FF"
  banner_title: "#00FFFF"
  banner_accent: "#FF1493"

spinner:
  thinking_verbs: ["jacking in", "decrypting", "uploading"]
  wings:
    - ["⟨⚡", "⚡⟩"]

branding:
  agent_name: "Cyber Agent"
  response_label: " ⚡ Cyber "

tool_prefix: "▏"
```

使用 `/skin cyberpunk` 或在 config.yaml 中使用 `display.skin: cyberpunk` 激活。

---

## 重要政策
### 提示缓存不得中断

Hermes-Agent 确保缓存在整个对话中保持有效。**不要实现会导致以下情况的更改：**
- 在对话过程中更改过去的上下文
- 在对话过程中更改工具集
- 在对话过程中重新加载记忆或重建系统提示

缓存中断会导致成本大幅增加。我们唯一改变上下文的时间是在上下文压缩期间。

### 工作目录行为
- **CLI**：使用当前目录（`.` → `os.getcwd()`）
- **消息传递**：使用 `MESSAGING_CWD` 环境变量（默认：主目录）

### 后台进程通知（网关）

当使用 `terminal(background=true, notify_on_complete=true)` 时，网关运行一个监视器，
检测进程完成并触发新的代理轮次。控制后台进程的详细程度
消息通过 `display.background_process_notifications`
在 config.yaml 中（或 `HERMES_BACKGROUND_NOTIFICATIONS` 环境变量）：

- `all` — 运行输出更新 + 最终消息（默认）
- `result` — 仅最终完成消息
- `error` — 仅当退出代码 != 0 时的最终消息
- `off` — 完全没有监视器消息

---

## 配置文件：多实例支持

Hermes 支持**配置文件** — 多个完全隔离的实例，每个实例都有自己的
`HERMES_HOME` 目录（配置、API 密钥、内存、会话、技能、网关等）。

核心机制：`hermes_cli/main.py` 中的 `_apply_profile_override()` 设置
`HERMES_HOME` 在任何模块导入之前。所有 119+ 对 `get_hermes_home()` 的引用
自动作用于活动配置文件。

### 配置文件安全代码的规则

1. **对所有 HERMES_HOME 路径使用 `get_hermes_home()`**。从 `hermes_constants` 导入。
   永远不要在读取/写入状态的代码中硬编码 `~/.hermes` 或 `Path.home() / ".hermes"`。
   ```python
   # 好
   from hermes_constants import get_hermes_home
   config_path = get_hermes_home() / "config.yaml"

   # 坏 — 破坏配置文件
   config_path = Path.home() / ".hermes" / "config.yaml"
   ```

2. **对面向用户的消息使用 `display_hermes_home()`**。从 `hermes_constants` 导入。
   这返回默认的 `~/.hermes` 或配置文件的 `~/.hermes/profiles/<name>`。
   ```python
   # 好
   from hermes_constants import display_hermes_home
   print(f"配置保存到 {display_hermes_home()}/config.yaml")

   # 坏 — 为配置文件显示错误路径
   print("配置保存到 ~/.hermes/config.yaml")
   ```

3. **模块级常量没问题** — 它们在导入时缓存 `get_hermes_home()`，
   这是在 `_apply_profile_override()` 设置环境变量之后。只需使用 `get_hermes_home()`，
   而不是 `Path.home() / ".hermes"`。

4. **模拟 `Path.home()` 的测试也必须设置 `HERMES_HOME`** — 因为代码现在使用
   `get_hermes_home()`（读取环境变量），而不是 `Path.home() / ".hermes"`：
   ```python
   with patch.object(Path, "home", return_value=tmp_path), \
        patch.dict(os.environ, {"HERMES_HOME": str(tmp_path / ".hermes")}):
       ...
   ```

5. **网关平台适配器应使用令牌锁** — 如果适配器使用
   唯一凭据（机器人令牌、API 密钥），在 `connect()`/`start()` 方法中从
   `gateway.status` 调用 `acquire_scoped_lock()`，并在
   `disconnect()`/`stop()` 中调用 `release_scoped_lock()`。这防止两个配置文件使用相同的凭据。
   有关规范模式，请参阅 `gateway/platforms/telegram.py`。

6. **配置文件操作是 HOME 锚定的，不是 HERMES_HOME 锚定的** — `_get_profiles_root()`
   返回 `Path.home() / ".hermes" / "profiles"`，而不是 `get_hermes_home() / "profiles"`。
   这是有意的 — 它允许 `hermes -p coder profile list` 查看所有配置文件，无论
   哪个是活动的。

## 已知陷阱

### 不要硬编码 `~/.hermes` 路径
使用 `hermes_constants` 中的 `get_hermes_home()` 作为代码路径。使用 `display_hermes_home()`
用于面向用户的打印/日志消息。硬编码 `~/.hermes` 会破坏配置文件 — 每个配置文件
都有自己的 `HERMES_HOME` 目录。这是 PR #3575 中修复的 5 个错误的来源。

### 不要使用 `simple_term_menu` 进行交互式菜单
在 tmux/iTerm2 中渲染错误 — 滚动时重影。改用 `curses`（标准库）。有关模式，请参阅 `hermes_cli/tools_config.py`。

### 不要在微调器/显示代码中使用 `\033[K`（ANSI 擦除到行尾）
在 `prompt_toolkit` 的 `patch_stdout` 下泄露为文字 `?[K` 文本。使用空格填充：`f"\r{line}{' ' * pad}"`。

### `_last_resolved_tool_names` 是 `model_tools.py` 中的进程全局变量
`delegate_tool.py` 中的 `_run_single_child()` 在子代理执行周围保存和恢复此全局变量。如果您添加读取此全局变量的新代码，请注意在子代理运行期间它可能暂时过时。

### 不要在架构描述中硬编码跨工具引用
工具架构描述不得按名称提及其他工具集的工具（例如，`browser_navigate` 说 "prefer web_search"）。这些工具可能不可用（缺少 API 密钥、禁用的工具集），导致模型幻觉调用不存在的工具。如果需要交叉引用，请在 `model_tools.py` 的 `get_tool_definitions()` 中动态添加 — 有关模式，请参阅 `browser_navigate` / `execute_code` 后处理块。

### 测试不得写入 `~/.hermes/`
`tests/conftest.py` 中的 `_isolate_hermes_home` 自动使用夹具将 `HERMES_HOME` 重定向到临时目录。永远不要在测试中硬编码 `~/.hermes/` 路径。

**配置文件测试**：测试配置文件功能时，还需要模拟 `Path.home()`，以便
`_get_profiles_root()` 和 `_get_default_hermes_home()` 在临时目录中解析。
使用 `tests/hermes_cli/test_profiles.py` 中的模式：
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

---

## 测试

**始终使用 `scripts/run_tests.sh`** — 不要直接调用 `pytest`。该脚本强制执行
与 CI 的密封环境一致性（取消设置凭据变量，TZ=UTC，LANG=C.UTF-8，
4 个 xdist 工作器匹配 GHA ubuntu-latest）。在 16+ 核心上直接使用 `pytest`
设置了 API 密钥的开发机器与 CI 存在差异，导致
多次 "本地工作，CI 失败" 事件（以及相反的情况）。

```bash
scripts/run_tests.sh                                  # 完整套件，CI 一致性
scripts/run_tests.sh tests/gateway/                   # 一个目录
scripts/run_tests.sh tests/agent/test_foo.py::test_x  # 一个测试
scripts/run_tests.sh -v --tb=long                     # 传递 pytest 标志
```

### 为什么使用包装器（以及为什么旧的 "直接调用 pytest" 不起作用）

脚本关闭的本地与 CI 漂移的五个真实来源：

| | 无包装器 | 有包装器 |
|---|---|---|
| 提供商 API 密钥 | 环境中的任何内容（自动检测池） | 所有 `*_API_KEY`/`*_TOKEN`/等都取消设置 |
| HOME / `~/.hermes/` | 您的真实配置+auth.json | 每个测试的临时目录 |
| 时区 | 本地 TZ（PDT 等） | UTC |
| 区域设置 | 任何设置 | C.UTF-8 |
| xdist 工作器 | `-n auto` = 所有核心（工作站上 20+） | `-n 4` 匹配 CI |

`tests/conftest.py` 还将 1-4 点作为自动使用夹具强制执行，因此任何 pytest
调用（包括 IDE 集成）都会获得密封行为 — 但包装器是双重保险。

### 不使用包装器运行（仅在必须时）

如果您不能使用包装器（例如，在 Windows 上或在直接使用 pytest 的 IDE 中），至少激活 venv 并传递 `-n 4`：

```bash
source venv/bin/activate
python -m pytest tests/ -q -n 4
```

工作器计数超过 4 将显示 CI 从未见过的测试顺序 flakes。

推送更改前始终运行完整套件。