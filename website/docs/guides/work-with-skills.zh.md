---
sidebar_position: 12
title: "使用技能"
description: "查找、安装、使用和创建技能 — 教Hermes新工作流的按需知识"
---

# 使用技能

技能是按需知识文档，教Hermes如何处理特定任务 — 从生成ASCII艺术到管理GitHub PR。本指南将引导您日常使用它们。

有关完整的技术参考，请参阅[技能系统](/docs/user-guide/features/skills)。

---

## 查找技能

每个Hermes安装都随附捆绑技能。查看可用的技能：

```bash
# 在任何聊天会话中：
/skills

# 或从CLI：
hermes skills list
```

这会显示带有名称和描述的紧凑列表：

```
ascii-art         使用pyfiglet、cowsay、boxes等生成ASCII艺术...
arxiv             从arXiv搜索和检索学术论文...
github-pr-workflow 完整的PR生命周期 — 创建分支、提交...
plan              计划模式 — 检查上下文，编写markdown...
excalidraw        使用Excalidraw创建手绘风格的图表...
```

### 搜索技能

```bash
# 按关键字搜索
/skills search docker
/skills search music
```

### 技能中心

官方可选技能（默认不活跃的较重或小众技能）可通过中心获取：

```bash
# 浏览官方可选技能
/skills browse

# 搜索中心
/skills search blockchain
```

---

## 使用技能

每个已安装的技能自动成为斜杠命令。只需输入其名称：

```bash
# 加载技能并给它一个任务
/ascii-art Make a banner that says "HELLO WORLD"
/plan Design a REST API for a todo app
/github-pr-workflow Create a PR for the auth refactor

# 仅技能名称（无任务）会加载它并让您描述您需要什么
/excalidraw
```

您也可以通过自然对话触发技能 — 要求Hermes使用特定技能，它会通过`skill_view`工具加载它。

### 渐进式披露

技能使用令牌高效加载模式。代理不会一次加载所有内容：

1. **`skills_list()`** — 所有技能的紧凑列表（约3k令牌）。在会话开始时加载。
2. **`skill_view(name)`** — 一个技能的完整SKILL.md内容。当代理决定需要该技能时加载。
3. **`skill_view(name, file_path)`** — 技能中的特定参考文件。仅在需要时加载。

这意味着技能在实际使用之前不会消耗令牌。

---

## 从中心安装

官方可选技能随Hermes一起提供，但默认不活跃。显式安装它们：

```bash
# 安装官方可选技能
hermes skills install official/research/arxiv

# 在聊天会话中从中心安装
/skills install official/creative/songwriting-and-ai-music
```

发生的情况：
1. 技能目录被复制到`~/.hermes/skills/`
2. 它出现在您的`skills_list`输出中
3. 它作为斜杠命令可用

:::tip
已安装的技能在新会话中生效。如果您希望它在当前会话中可用，请使用`/reset`重新开始，或添加`--now`立即使提示缓存失效（下一轮会消耗更多令牌）。
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
# 按其限定名称加载插件技能
skill_view("superpowers:writing-plans")

# 具有相同基本名称的内置技能不受影响
skill_view("writing-plans")
```

插件技能**不会**在系统提示中列出，也不会出现在`skills_list`中。它们是选择加入的 — 当您知道插件提供一个技能时，显式加载它。加载时，代理会看到一个横幅，列出同一插件的兄弟技能。

有关如何在您自己的插件中发布技能，请参阅[构建Hermes插件 → 捆绑技能](/docs/guides/build-a-hermes-plugin#bundle-skills)。

---

## 配置技能设置

一些技能在其前置内容中声明它们需要的配置：

```yaml
metadata:
  hermes:
    config:
      - key: tenor.api_key
        description: "Tenor API key for GIF search"
        prompt: "Enter your Tenor API key"
        url: "https://developers.google.com/tenor/guides/quickstart"
```

当首次加载带有配置的技能时，Hermes会提示您输入值。它们存储在`config.yaml`的`skills.config.*`下。

从CLI管理技能配置：

```bash
# 特定技能的交互式配置
hermes skills config gif-search

# 查看所有技能配置
hermes config get skills.config
```

---

## 创建自己的技能

技能只是带有YAML前置内容的markdown文件。创建一个不到五分钟。

### 1. 创建目录

```bash
mkdir -p ~/.hermes/skills/my-category/my-skill
```

### 2. 编写SKILL.md

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

## When to Use
Use this skill when the user asks about [specific topic] or needs to [specific task].

## Procedure
1. First, check if [prerequisite] is available
2. Run `command --with-flags`
3. Parse the output and present results

## Pitfalls
- Common failure: [description]. Fix: [solution]
- Watch out for [edge case]

## Verification
Run `check-command` to confirm the result is correct.
```

### 3. 添加参考文件（可选）

技能可以包含代理按需加载的支持文件：

```
my-skill/
├── SKILL.md                    # 主要技能文档
├── references/
│   ├── api-docs.md             # 代理可以参考的API文档
│   └── examples.md             # 输入/输出示例
├── templates/
│   └── config.yaml             # 代理可以使用的模板文件
└── scripts/
    └── setup.sh                # 代理可以执行的脚本
```

在您的SKILL.md中引用这些：

```markdown
For API details, load the reference: `skill_view("my-skill", "references/api-docs.md")`
```

### 4. 测试它

启动新会话并尝试您的技能：

```bash
hermes chat -q "/my-skill help me with the thing"
```

技能会自动出现 — 无需注册。将其放入`~/.hermes/skills/`，它就会生效。

:::info
代理也可以使用`skill_manage`创建和更新技能。解决复杂问题后，Hermes可能会提出将方法保存为技能以备下次使用。
:::

---

## 每个平台的技能管理

控制哪些技能在哪些平台上可用：

```bash
hermes skills
```

这会打开一个交互式TUI，您可以在其中按平台（CLI、Telegram、Discord等）启用或禁用技能。当您希望某些技能仅在特定上下文中可用时很有用 — 例如，在Telegram上保持开发技能不可用。

---

## 技能与内存

两者都跨会话持久，但它们服务于不同的目的：

| | 技能 | 内存 |
|---|---|---|
| **内容** | 程序性知识 — 如何做事 | 事实性知识 — 事物是什么 |
| **时机** | 按需加载，仅在相关时 | 自动注入到每个会话中 |
| **大小** | 可以很大（数百行） | 应该紧凑（仅关键事实） |
| **成本** | 加载前零令牌 | 小但恒定的令牌成本 |
| **示例** | "如何部署到Kubernetes" | "用户喜欢深色模式，居住在PST" |
| **创建者** | 您、代理或从中心安装 | 代理，基于对话 |

**经验法则：** 如果您会将其放入参考文档，那就是技能。如果您会将其放在便利贴上，那就是内存。

---

## 提示

**保持技能专注。** 试图涵盖"所有DevOps"的技能会太长太模糊。涵盖"将Python应用部署到Fly.io"的技能足够具体，真正有用。

**让代理创建技能。** 完成复杂的多步骤任务后，Hermes通常会提出将方法保存为技能。说是 — 这些由代理编写的技能捕获了确切的工作流程，包括沿途发现的陷阱。

**使用类别。** 将技能组织到子目录中（`~/.hermes/skills/devops/`、`~/.hermes/skills/research/`等）。这使列表易于管理，并帮助代理更快找到相关技能。

**当技能过时更新它们。** 如果您使用技能并遇到未涵盖的问题，告诉Hermes使用您学到的内容更新技能。未维护的技能会成为负担。

---

*有关完整的技能参考 — 前置内容字段、条件激活、外部目录等 — 请参阅[技能系统](/docs/user-guide/features/skills)。*