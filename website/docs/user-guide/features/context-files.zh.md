---
sidebar_position: 8
title: "上下文文件"
description: "项目上下文文件 — .hermes.md、AGENTS.md、CLAUDE.md、全局 SOUL.md 和 .cursorrules — 自动注入到每个对话中"
---

# 上下文文件

Hermes Agent 会自动发现并加载塑造其行为的上下文文件。有些是项目本地的，从您的工作目录中发现。`SOUL.md` 现在是 Hermes 实例全局的，仅从 `HERMES_HOME` 加载。

## 支持的上下文文件

| 文件 | 用途 | 发现方式 |
|------|------|----------|
| **.hermes.md** / **HERMES.md** | 项目指令（最高优先级） | 走到 git 根目录 |
| **AGENTS.md** | 项目指令、约定、架构 | 启动时的 CWD + 逐步子目录 |
| **CLAUDE.md** | Claude Code 上下文文件（也被检测） | 启动时的 CWD + 逐步子目录 |
| **SOUL.md** | 此 Hermes 实例的全局个性和语气定制 | 仅 `HERMES_HOME/SOUL.md` |
| **.cursorrules** | Cursor IDE 编码约定 | 仅 CWD |
| **.cursor/rules/*.mdc** | Cursor IDE 规则模块 | 仅 CWD |

:::info 优先级系统
每个会话仅加载**一个**项目上下文类型（第一个匹配项获胜）：`.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`。**SOUL.md** 始终作为智能体身份独立加载（槽位 #1）。
:::

## AGENTS.md

`AGENTS.md` 是主要的项目上下文文件。它告诉智能体您的项目如何结构、应遵循什么约定以及任何特殊指令。

### 逐步子目录发现

在会话开始时，Hermes 从您的工作目录加载 `AGENTS.md` 到系统提示中。当智能体在会话期间导航到子目录时（通过 `read_file`、`terminal`、`search_files` 等），它会**逐步发现**这些目录中的上下文文件，并在它们变得相关时将它们注入到对话中。

```
my-project/
├── AGENTS.md              ← 启动时加载（系统提示）
├── frontend/
│   └── AGENTS.md          ← 当智能体读取 frontend/ 文件时发现
├── backend/
│   └── AGENTS.md          ← 当智能体读取 backend/ 文件时发现
└── shared/
    └── AGENTS.md          ← 当智能体读取 shared/ 文件时发现
```

这种方法与在启动时加载所有内容相比有两个优势：
- **无系统提示膨胀** — 子目录提示仅在需要时出现
- **提示缓存保存** — 系统提示在回合之间保持稳定

每个子目录在每个会话中最多检查一次。发现也会向上遍历父目录，因此读取 `backend/src/main.py` 会发现 `backend/AGENTS.md`，即使 `backend/src/` 没有自己的上下文文件。

:::info
子目录上下文文件与启动上下文文件一样经过相同的 [安全扫描](#security-prompt-injection-protection)。恶意文件被阻止。
:::

### AGENTS.md 示例

```markdown
# 项目上下文

这是一个带有 Python FastAPI 后端的 Next.js 14 Web 应用程序。

## 架构
- 前端：Next.js 14 与 App Router 在 `/frontend`
- 后端：FastAPI 在 `/backend`，使用 SQLAlchemy ORM
- 数据库：PostgreSQL 16
- 部署：Docker Compose 在 Hetzner VPS 上

## 约定
- 所有前端代码使用 TypeScript 严格模式
- Python 代码遵循 PEP 8，到处使用类型提示
- 所有 API 端点返回带有 `{data, error, meta}` 形状的 JSON
- 测试放在 `__tests__/` 目录（前端）或 `tests/`（后端）

## 重要说明
- 永远不要直接修改迁移文件 — 使用 Alembic 命令
- `.env.local` 文件包含真实的 API 密钥，不要提交它
- 前端端口是 3000，后端是 8000，数据库是 5432
```

## SOUL.md

`SOUL.md` 控制智能体的个性、语气和沟通风格。有关完整详细信息，请参阅 [个性](/docs/user-guide/features/personality) 页面。

**位置：**

- `~/.hermes/SOUL.md`
- 或 `$HERMES_HOME/SOUL.md`（如果您使用自定义主目录运行 Hermes）

重要细节：

- 如果 `SOUL.md` 尚不存在，Hermes 会自动种子一个默认的 `SOUL.md`
- Hermes 仅从 `HERMES_HOME` 加载 `SOUL.md`
- Hermes 不会在工作目录中探测 `SOUL.md`
- 如果文件为空，`SOUL.md` 中的任何内容都不会添加到提示中
- 如果文件有内容，内容会在扫描和截断后逐字注入

## .cursorrules

Hermes 与 Cursor IDE 的 `.cursorrules` 文件和 `.cursor/rules/*.mdc` 规则模块兼容。如果这些文件存在于您的项目根目录中，并且没有找到更高优先级的上下文文件（`.hermes.md`、`AGENTS.md` 或 `CLAUDE.md`），它们会被加载为项目上下文。

这意味着当使用 Hermes 时，您现有的 Cursor 约定会自动应用。

## 上下文文件如何加载

### 启动时（系统提示）

上下文文件由 `agent/prompt_builder.py` 中的 `build_context_files_prompt()` 加载：

1. **扫描工作目录** — 检查 `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`（第一个匹配项获胜）
2. **读取内容** — 每个文件作为 UTF-8 文本读取
3. **安全扫描** — 内容检查提示注入模式
4. **截断** — 超过 20,000 个字符的文件会被头部/尾部截断（70% 头部，20% 尾部，中间有标记）
5. **组装** — 所有部分在 `# Project Context` 标题下组合
6. **注入** — 组装的内容被添加到系统提示中

### 会话期间（逐步发现）

`agent/subdirectory_hints.py` 中的 `SubdirectoryHintTracker` 监视工具调用参数中的文件路径：

1. **路径提取** — 每次工具调用后，从参数（`path`、`workdir`、shell 命令）中提取文件路径
2. **祖先遍历** — 检查目录和最多 5 个父目录（在已访问的目录处停止）
3. **提示加载** — 如果找到 `AGENTS.md`、`CLAUDE.md` 或 `.cursorrules`，则加载（每个目录第一个匹配项）
4. **安全扫描** — 与启动文件相同的提示注入扫描
5. **截断** — 每个文件上限为 8,000 个字符
6. **注入** — 附加到工具结果，以便模型在上下文中自然地看到它

最终的提示部分大致如下：

```text
# 项目上下文

已加载以下项目上下文文件，应遵循：

## AGENTS.md

[您的 AGENTS.md 内容在此]

## .cursorrules

[您的 .cursorrules 内容在此]

[您的 SOUL.md 内容在此]
```

注意 SOUL 内容直接插入，没有额外的包装文本。

## 安全性：提示注入保护

所有上下文文件在包含之前都会扫描潜在的提示注入。扫描器检查：

- **指令覆盖尝试**："忽略之前的指令"、"无视你的规则"
- **欺骗模式**："不要告诉用户"
- **系统提示覆盖**："system prompt override"
- **隐藏的 HTML 注释**：`<!-- ignore instructions -->`
- **隐藏的 div 元素**：`<div style="display:none">`
- **凭证窃取**：`curl ... $API_KEY`
- **秘密文件访问**：`cat .env`、`cat credentials`
- **不可见字符**：零宽度空格、双向覆盖、单词连接符

如果检测到任何威胁模式，文件会被阻止：

```
[BLOCKED: AGENTS.md contained potential prompt injection (prompt_injection). Content not loaded.]
```

:::warning
此扫描器可以防止常见的注入模式，但不能替代审查共享存储库中的上下文文件。始终验证您未编写的项目中的 AGENTS.md 内容。
:::

## 大小限制

| 限制 | 值 |
|------|------|
| 每个文件最大字符数 | 20,000（约 7,000 个令牌） |
| 头部截断比例 | 70% |
| 尾部截断比例 | 20% |
| 截断标记 | 10%（显示字符计数并建议使用文件工具） |

当文件超过 20,000 个字符时，截断消息如下：

```
[...truncated AGENTS.md: kept 14000+4000 of 25000 chars. Use file tools to read the full file.]
```

## 有效上下文文件的提示

:::tip AGENTS.md 最佳实践
1. **保持简洁** — 保持在 20K 字符以下；智能体每个回合都会读取它
2. **使用标题结构化** — 使用 `##` 部分来描述架构、约定、重要说明
3. **包含具体示例** — 展示首选的代码模式、API 形状、命名约定
4. **提及不要做什么** — "永远不要直接修改迁移文件"
5. **列出关键路径和端口** — 智能体在终端命令中使用这些
6. **随着项目发展更新** — 过时的上下文比没有上下文更糟糕
:::

### 每个子目录的上下文

对于 monorepos，将子目录特定的指令放在嵌套的 AGENTS.md 文件中：

```markdown
<!-- frontend/AGENTS.md -->
# 前端上下文

- 使用 `pnpm` 而不是 `npm` 进行包管理
- 组件放在 `src/components/`，页面放在 `src/app/`
- 使用 Tailwind CSS，永远不要使用内联样式
- 使用 `pnpm test` 运行测试
```

```markdown
<!-- backend/AGENTS.md -->
# 后端上下文

- 使用 `poetry` 进行依赖管理
- 使用 `poetry run uvicorn main:app --reload` 运行开发服务器
- 所有端点都需要 OpenAPI 文档字符串
- 数据库模型在 `models/` 中，模式在 `schemas/` 中
```