---
sidebar_position: 12
title: "使用技能"
description: "查找、安装、使用和创建技能 — 按需知识，教会 Hermes 新的工作流程"
---

# 使用技能

技能是按需知识文档，教会 Hermes 如何处理特定任务 — 从生成 ASCII 艺术到管理 GitHub PR。本指南将引导您日常使用它们。

有关完整的技术参考，请参阅[技能系统](/docs/user-guide/features/skills)。

---

## 查找技能

每个 Hermes 安装都附带捆绑的技能。查看可用内容：

```bash
# 在任何聊天会话中：
/skills

# 或从 CLI：
hermes skills list
```

这将显示一个包含名称和描述的紧凑列表：

```
ascii-art         使用 pyfiglet、cowsay、boxes 生成 ASCII 艺术...
arxiv             从 arXiv 搜索和检索学术论文...
github-pr-workflow 完整的 PR 生命周期 — 创建分支、提交...
plan              计划模式 — 检查上下文，编写 markdown...
excalidraw        使用 Excalidraw 创建手绘风格图表...
```

### 搜索技能

```bash
# 按关键字搜索
/skills search docker
/skills search music
```

### 技能中心

官方可选技能（默认不激活的较重或利基技能）可通过中心获得：

```bash
# 浏览官方可选技能
/skills browse

# 搜索中心
/skills search blockchain
```

---

## 使用技能

每个已安装的技能自动成为一个斜杠命令。只需输入其名称：

```bash
# 加载技能并给它一个任务
/ascii-art Make a banner that says "HELLO WORLD"
/plan Design a REST API for a todo app
/github-pr-workflow Create a PR for the auth refactor

# 只有技能名称（无任务）会加载它并让您描述您需要什么
/excalidraw
```

您也可以通过自然对话触发技能 — 要求 Hermes 使用特定技能，它会通过 `skill_view` 工具加载它。

### 渐进式披露

技能使用令牌高效的加载模式。智能体不会一次加载所有内容：

1. **`skills_list()`** — 所有技能的紧凑列表（约 3k 令牌）。在会话开始时加载。
2. **`skill_view(name)`** — 一个技能的完整 SKILL.md 内容。当智能体决定需要该技能时加载。
3. **`skill_view(name, file_path)`** — 技能中的特定参考文件。仅在需要时加载。

这意味着技能在实际使用之前不会消耗令牌。

---

## 从中心安装

官方可选技能随 Hermes 一起提供，但默认不激活。明确安装它们：

```bash
# 安装官方可选技能
hermes skills install official/research/arxiv

# 在聊天会话中从中心安装
/skills install official/creative/songwriting-and-ai-music
```

发生的情况：
1. 技能目录被复制到 `~/.hermes/skills/`
2. 它出现在您的 `skills_list` 输出中
3. 它作为斜杠命令可用

:::tip
已安装的技能在新会话中生效。如果您希望它在当前会话中可用，请使用 `/reset` 重新开始，或添加 `--now` 立即使提示缓存失效（下一轮会消耗更多令牌）。
:::

### 验证安装

```bash
# 检查它是否存在
hermes skills list | grep arxiv

# 或在聊天中
/skills search arxiv
```

---

## 插件提供的技能

插件可以使用命名空间名称（`plugin:skill`）捆绑自己的技能。这可以防止与内置技能的名称冲突。

```bash
# 通过其限定名称加载插件技能
skill_view("superpowers:writing-plans")

# 具有相同基本名称的内置技能不受影响
skill_view("writing-plans")
```

插件技能**不会**列在系统提示中，也不会出现在 `skills_list` 中。它们是选择加入的 — 当您知道插件提供一个技能时，明确加载它们。加载时，智能体会看到一个横幅，列出来自同一插件的同级技能。

有关如何在您自己的插件中提供技能，请参阅[构建 Hermes 插件 → 捆绑技能](/docs/guides/build-a-hermes-plugin#bundle-skills)。

---

## 配置技能设置

一些技能在其前言中声明它们需要的配置：

```yaml
metadata:
  hermes:
    config:
      - key: tenor.api_key
        description: "Tenor API key for GIF search"
        prompt: "Enter your Tenor API key"
        url: "https://developers.google.com/tenor/guides/quickstart"
```

当首次加载带有配置的技能时，Hermes 会提示您输入值。它们存储在 `config.yaml` 中的 `skills.config.*` 下。

从 CLI 管理技能配置：

```bash
# 特定技能的交互式配置
hermes skills config gif-search

# 查看所有技能配置
hermes config get skills.config
```

---

## 创建自己的技能

技能只是带有 YAML 前言的 markdown 文件。创建一个只需不到五分钟。

### 1. 创建目录

```bash
mkdir -p ~/.hermes/skills/my-category/my-skill
```

### 2. 编写 SKILL.md

```markdown title="~/.hermes/skills/my-category/my-skill/SKILL.md"
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
metadata:
  hermes:
    tags: [my-tag, automation]
    category: my-category
---

# My Skill

## 何时使用
当用户询问[特定主题]或需要[特定任务]时使用此技能。

## 步骤
1. 首先，检查[先决条件]是否可用
2. 运行 `command --with-flags`
3. 解析输出并呈现结果

## 陷阱
- 常见失败：[描述]。解决方法：[解决方案]
- 注意[边缘情况]

## 验证
运行 `check-command` 确认结果正确。
```

### 3. 添加参考文件（可选）

技能可以包含智能体按需加载的支持文件：

```
my-skill/
├── SKILL.md                    # 主要技能文档
├── references/
│   ├── api-docs.md             # 智能体可以查阅的 API 参考
│   └── examples.md             # 示例输入/输出
├── templates/
│   └── config.yaml             # 智能体可以使用的模板文件
└── scripts/
    └── setup.sh                # 智能体可以执行的脚本
```

在您的 SKILL.md 中引用这些：

```markdown
For API details, load the reference: `skill_view("my-skill", "references/api-docs.md")`
```

### 4. 测试它

开始一个新会话并尝试您的技能：

```bash
hermes chat -q "/my-skill help me with the thing"
```

技能会自动出现 — 无需注册。将其放入 `~/.hermes/skills/` 即可生效。

:::info
智能体也可以使用 `skill_manage` 创建和更新技能本身。解决复杂问题后，Hermes 可能会主动提出将该方法保存为技能，以便下次使用。
:::

---

## 按平台技能管理

控制哪些技能在哪些平台上可用：

```bash
hermes skills
```

这会打开一个交互式 TUI，您可以在其中按平台（CLI、Telegram、Discord 等）启用或禁用技能。当您希望某些技能仅在特定上下文中可用时非常有用 — 例如，在 Telegram 上禁用开发技能。

---

## 技能 vs 记忆

两者都在会话之间持久存在，但它们服务于不同的目的：

| | 技能 | 记忆 |
|---|---|---|
| **内容** | 程序性知识 — 如何做事 | 事实性知识 — 事物是什么 |
| **时机** | 按需加载，仅在相关时 | 自动注入到每个会话中 |
| **大小** | 可以很大（数百行） | 应该紧凑（仅关键事实） |
| **成本** | 加载前零令牌 | 小但恒定的令牌成本 |
| **示例** | "如何部署到 Kubernetes" | "用户偏好深色模式，住在 PST 时区" |
| **创建者** | 您、智能体或从中心安装 | 智能体，基于对话 |

**经验法则：** 如果您会将其放在参考文档中，它就是技能。如果您会将其放在便利贴上，它就是记忆。

---

## 提示

**保持技能专注。** 尝试涵盖"所有 DevOps"的技能会太长太模糊。涵盖"将 Python 应用部署到 Fly.io"的技能足够具体，真正有用。

**让智能体创建技能。** 在复杂的多步任务之后，Hermes 通常会主动提出将该方法保存为技能。说是的 — 这些智能体编写的技能捕获了确切的工作流程，包括沿途发现的陷阱。

**使用类别。** 将技能组织到子目录中（`~/.hermes/skills/devops/`、`~/.hermes/skills/research/` 等）。这使列表易于管理，并帮助智能体更快找到相关技能。

**当技能过时及时更新。** 如果您使用技能并遇到其中未涵盖的问题，请告诉 Hermes 使用您学到的内容更新技能。未维护的技能会成为负担。

---

*有关完整的技能参考 — 前言字段、条件激活、外部目录等 — 请参阅[技能系统](/docs/user-guide/features/skills)。*