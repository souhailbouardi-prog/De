---
sidebar_position: 5
title: "提示组装"
description: "Hermes 如何构建系统提示、保持缓存稳定性并注入临时层"
---

# 提示组装

Hermes 刻意分离：

- **缓存的系统提示状态**
- **临时 API 调用时添加**

这是项目中最重要的设计选择之一，因为它影响：

- 令牌使用
- 提示缓存效果
- 会话连续性
- 记忆正确性

主要文件：

- `run_agent.py`
- `agent/prompt_builder.py`
- `tools/memory_tool.py`

## 缓存的系统提示层

缓存的系统提示大致按以下顺序组装：

1. 代理身份 — 当可用时从 `HERMES_HOME` 加载 `SOUL.md`，否则回退到 `prompt_builder.py` 中的 `DEFAULT_AGENT_IDENTITY`
2. 工具感知行为指导
3. Honcho 静态块（激活时）
4. 可选系统消息
5. 冻结的 MEMORY 快照
6. 冻结的 USER 配置文件快照
7. 技能索引
8. 上下文文件（`AGENTS.md`、`.cursorrules`、`.cursor/rules/*.mdc`）— 当 `SOUL.md` 已在步骤 1 中作为身份加载时，此处不包含它
9. 时间戳 / 可选会话 ID
10. 平台提示

当设置了 `skip_context_files` 时（例如子代理委托），不会加载 `SOUL.md`，而是使用硬编码的 `DEFAULT_AGENT_IDENTITY`。

### 具体示例：组装的系统提示

当所有层都存在时，最终系统提示的简化视图如下（注释显示每个部分的来源）：

```
# Layer 1: Agent Identity (from ~/.hermes/SOUL.md)
You are Hermes, an AI assistant created by Nous Research.
You are an expert software engineer and researcher.
You value correctness, clarity, and efficiency.
...

# Layer 2: Tool-aware behavior guidance
You have persistent memory across sessions. Save durable facts using
the memory tool: user preferences, environment details, tool quirks,
and stable conventions. Memory is injected into every turn, so keep
it compact and focused on facts that will still matter later.
...
When the user references something from a past conversation or you
suspect relevant cross-session context exists, use session_search
to recall it before asking them to repeat themselves.

# Tool-use enforcement (for GPT/Codex models only)
You MUST use your tools to take action — do not describe what you
would do or plan to do without actually doing it.
...

# Layer 3: Honcho static block (when active)
[Honcho personality/context data]

# Layer 4: Optional system message (from config or API)
[User-configured system message override]

# Layer 5: Frozen MEMORY snapshot
## Persistent Memory
- User prefers Python 3.12, uses pyproject.toml
- Default editor is nvim
- Working on project "atlas" in ~/code/atlas
- Timezone: US/Pacific

# Layer 6: Frozen USER profile snapshot
## User Profile
- Name: Alice
- GitHub: alice-dev

# Layer 7: Skills index
## Skills (mandatory)
Before replying, scan the skills below. If one clearly matches
your task, load it with skill_view(name) and follow its instructions.
...
<available_skills>
  software-development:
    - code-review: Structured code review workflow
    - test-driven-development: TDD methodology
  research:
    - arxiv: Search and summarize arXiv papers
</available_skills>

# Layer 8: Context files (from project directory)
# Project Context
The following project context files have been loaded and should be followed:

## AGENTS.md
This is the atlas project. Use pytest for testing. The main
entry point is src/atlas/main.py. Always run `make lint` before
committing.

# Layer 9: Timestamp + session
Current time: 2026-03-30T14:30:00-07:00
Session: abc123

# Layer 10: Platform hint
You are a CLI AI Agent. Try not to use markdown but simple text
renderable inside a terminal.
```

## SOUL.md 如何出现在提示中

`SOUL.md` 位于 `~/.hermes/SOUL.md`，作为代理的身份 — 系统提示的第一部分。`prompt_builder.py` 中的加载逻辑如下：

```python
# From agent/prompt_builder.py (simplified)
def load_soul_md() -> Optional[str]:
    soul_path = get_hermes_home() / "SOUL.md"
    if not soul_path.exists():
        return None
    content = soul_path.read_text(encoding="utf-8").strip()
    content = _scan_context_content(content, "SOUL.md")  # Security scan
    content = _truncate_content(content, "SOUL.md")       # Cap at 20k chars
    return content
```

当 `load_soul_md()` 返回内容时，它会替换硬编码的 `DEFAULT_AGENT_IDENTITY`。然后调用 `build_context_files_prompt()` 并设置 `skip_soul=True` 以防止 `SOUL.md` 出现两次（一次作为身份，一次作为上下文文件）。

如果 `SOUL.md` 不存在，系统会回退到：

```
You are Hermes Agent, an intelligent AI assistant created by Nous Research.
You are helpful, knowledgeable, and direct. You assist users with a wide
range of tasks including answering questions, writing and editing code,
analyzing information, creative work, and executing actions via your tools.
You communicate clearly, admit uncertainty when appropriate, and prioritize
being genuinely useful over being verbose unless otherwise directed below.
Be targeted and efficient in your exploration and investigations.
```

## 上下文文件如何注入

`build_context_files_prompt()` 使用 **优先级系统** — 只加载一种项目上下文类型（第一个匹配项获胜）：

```python
# From agent/prompt_builder.py (simplified)
def build_context_files_prompt(cwd=None, skip_soul=False):
    cwd_path = Path(cwd).resolve()

    # Priority: first match wins — only ONE project context loaded
    project_context = (
        _load_hermes_md(cwd_path)       # 1. .hermes.md / HERMES.md (walks to git root)
        or _load_agents_md(cwd_path)    # 2. AGENTS.md (cwd only)
        or _load_claude_md(cwd_path)    # 3. CLAUDE.md (cwd only)
        or _load_cursorrules(cwd_path)  # 4. .cursorrules / .cursor/rules/*.mdc
    )

    sections = []
    if project_context:
        sections.append(project_context)

    # SOUL.md from HERMES_HOME (independent of project context)
    if not skip_soul:
        soul_content = load_soul_md()
        if soul_content:
            sections.append(soul_content)

    if not sections:
        return ""

    return (
        "# Project Context\n\n"
        "The following project context files have been loaded "
        "and should be followed:\n\n"
        + "\n".join(sections)
    )
```

### 上下文文件发现详情

| 优先级 | 文件 | 搜索范围 | 说明 |
|----------|-------|-------------|-------|
| 1 | `.hermes.md`, `HERMES.md` | CWD 到 git 根目录 | Hermes 原生项目配置 |
| 2 | `AGENTS.md` | 仅 CWD | 通用代理指令文件 |
| 3 | `CLAUDE.md` | 仅 CWD | Claude Code 兼容性 |
| 4 | `.cursorrules`, `.cursor/rules/*.mdc` | 仅 CWD | Cursor 兼容性 |

所有上下文文件：
- **安全扫描** — 检查提示注入模式（不可见 Unicode、"忽略先前指令"、凭证泄露尝试）
- **截断** — 使用 70/20 头尾比例限制在 20,000 字符，并添加截断标记
- **YAML 前置内容剥离** — `.hermes.md` 前置内容被移除（保留用于未来配置覆盖）

## 仅 API 调用时的层

这些故意**不**作为缓存系统提示的一部分持久化：

- `ephemeral_system_prompt`
- 预填充消息
- 网关派生的会话上下文覆盖
- 注入到当前轮用户消息中的后期 Honcho 召回

这种分离保持了稳定前缀的稳定性，有利于缓存。

## 记忆快照

本地记忆和用户配置文件数据在会话开始时作为冻结快照注入。会话中期的写入会更新磁盘状态，但直到新会话或强制重建发生时，才会改变已构建的系统提示。

## 上下文文件

`agent/prompt_builder.py` 使用**优先级系统**扫描和清理项目上下文文件 — 只加载一种类型（第一个匹配项获胜）：

1. `.hermes.md` / `HERMES.md`（走到 git 根目录）
2. `AGENTS.md`（启动时的 CWD；会话期间通过 `agent/subdirectory_hints.py` 逐步发现子目录）
3. `CLAUDE.md`（仅 CWD）
4. `.cursorrules` / `.cursor/rules/*.mdc`（仅 CWD）

`SOUL.md` 通过 `load_soul_md()` 单独加载到身份槽中。当加载成功时，`build_context_files_prompt(skip_soul=True)` 防止它出现两次。

长文件在注入前会被截断。

## 技能索引

当技能工具可用时，技能系统会向提示中贡献一个紧凑的技能索引。

## 为什么提示组装这样拆分

该架构特意优化为：

- 保留提供商端的提示缓存
- 避免不必要地改变历史
- 保持记忆语义可理解
- 让网关/ACP/CLI 添加上下文而不污染持久提示状态

## 相关文档

- [上下文压缩和提示缓存](./context-compression-and-caching.md)
- [会话存储](./session-storage.md)
- [网关内部原理](./gateway-internals.md)
