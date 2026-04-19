---
sidebar_position: 3
title: "创建技能"
description: "如何为 Hermes Agent 创建技能 — SKILL.md 格式、指南和发布"
---

# 创建技能

技能是向 Hermes Agent 添加新功能的首选方式。它们比工具更容易创建，不需要对代理进行代码更改，并且可以与社区共享。

## 应该是技能还是工具？

当以下情况时，使其成为**技能**：
- 功能可以表示为指令 + shell 命令 + 现有工具
- 它包装了代理可以通过 `terminal` 或 `web_extract` 调用的外部 CLI 或 API
- 它不需要自定义 Python 集成或内置到代理中的 API 密钥管理
- 示例：arXiv 搜索、git 工作流、Docker 管理、PDF 处理、通过 CLI 工具发送电子邮件

当以下情况时，使其成为**工具**：
- 它需要与 API 密钥、认证流程或多组件配置的端到端集成
- 它需要每次都必须精确执行的自定义处理逻辑
- 它处理二进制数据、流式传输或实时事件
- 示例：浏览器自动化、TTS、视觉分析

## 技能目录结构

捆绑的技能位于 `skills/` 中，按类别组织。官方可选技能在 `optional-skills/` 中使用相同的结构：

```text
skills/
├── research/
│   └── arxiv/
│       ├── SKILL.md              # 必需：主要指令
│       └── scripts/              # 可选：辅助脚本
│           └── search_arxiv.py
├── productivity/
│   └── ocr-and-documents/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
└── ...
```

## SKILL.md 格式

```markdown
---
name: my-skill
description: 简短描述（显示在技能搜索结果中）
version: 1.0.0
author: 你的名字
license: MIT
platforms: [macos, linux]          # 可选 — 限制为特定的操作系统平台
                                   #   有效值：macos, linux, windows
                                   #   省略以在所有平台上加载（默认）
metadata:
  hermes:
    tags: [Category, Subcategory, Keywords]
    related_skills: [other-skill-name]
    requires_toolsets: [web]            # 可选 — 仅在这些工具集活跃时显示
    requires_tools: [web_search]        # 可选 — 仅在这些工具可用时显示
    fallback_for_toolsets: [browser]    # 可选 — 当这些工具集活跃时隐藏
    fallback_for_tools: [browser_navigate]  # 可选 — 当这些工具存在时隐藏
    config:                              # 可选 — 技能需要的 config.yaml 设置
      - key: my.setting
        description: "此设置控制什么"
        default: "sensible-default"
        prompt: "设置的显示提示"
required_environment_variables:          # 可选 — 技能需要的环境变量
  - name: MY_API_KEY
    prompt: "输入你的 API 密钥"
    help: "在 https://example.com 获取"
    required_for: "API 访问"
---

# 技能标题

简短介绍。

## 使用时机
触发条件 — 代理何时应该加载此技能？

## 快速参考
常用命令或 API 调用表。

## 流程
代理遵循的分步说明。

## 陷阱
已知的失败模式和如何处理它们。

## 验证
代理如何确认它有效。
```

### 特定平台的技能

技能可以使用 `platforms` 字段将自己限制在特定的操作系统：

```yaml
platforms: [macos]            # 仅限 macOS（例如，iMessage、Apple Reminders）
platforms: [macos, linux]     # macOS 和 Linux
platforms: [windows]          # 仅限 Windows
```

设置后，该技能会在不兼容的平台上自动从系统提示、`skills_list()` 和斜杠命令中隐藏。如果省略或为空，技能会在所有平台上加载（向后兼容）。

### 条件技能激活

技能可以声明对特定工具或工具集的依赖。这控制技能是否在给定会话的系统提示中出现。

```yaml
metadata:
  hermes:
    requires_toolsets: [web]           # 如果 web 工具集不可用，则隐藏
    requires_tools: [web_search]       # 如果 web_search 工具不可用，则隐藏
    fallback_for_toolsets: [browser]   # 如果浏览器工具集可用，则隐藏
    fallback_for_tools: [browser_navigate]  # 如果 browser_navigate 可用，则隐藏
```

| 字段 | 行为 |
|-------|----------|
| `requires_toolsets` | 当任何列出的工具集**不可用**时，技能**隐藏** |
| `requires_tools` | 当任何列出的工具**不可用**时，技能**隐藏** |
| `fallback_for_toolsets` | 当任何列出的工具集**可用**时，技能**隐藏** |
| `fallback_for_tools` | 当任何列出的工具**可用**时，技能**隐藏** |

**`fallback_for_*` 的用例**：创建一个技能，当主要工具不可用时作为变通方法。例如，一个 `duckduckgo-search` 技能，带有 `fallback_for_tools: [web_search]`，仅在 web 搜索工具（需要 API 密钥）未配置时显示。

**`requires_*` 的用例**：创建一个仅在某些工具存在时才有意义的技能。例如，一个带有 `requires_toolsets: [web]` 的网页抓取工作流技能，在网络工具禁用时不会使提示混乱。

### 环境变量要求

技能可以声明它们需要的环境变量。当通过 `skill_view` 加载技能时，其必需的变量会自动注册为传递到沙箱执行环境（终端、execute_code）。

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: "Tenor API key"               # 提示用户时显示
    help: "在 https://tenor.com 获取你的密钥"  # 帮助文本或 URL
    required_for: "GIF 搜索功能"   # 需要此变量的功能
```

每个条目支持：
- `name`（必需）— 环境变量名称
- `prompt`（可选）— 向用户询问值时的提示文本
- `help`（可选）— 帮助文本或获取值的 URL
- `required_for`（可选）— 描述哪个功能需要此变量

用户也可以在 `config.yaml` 中手动配置传递变量：

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_VAR
    - ANOTHER_VAR
```

请参阅 `skills/apple/` 获取仅限 macOS 技能的示例。

## 加载时的安全设置

当技能需要 API 密钥或令牌时，使用 `required_environment_variables`。缺少值**不会**从发现中隐藏技能。相反，当技能在本地 CLI 中加载时，Hermes 会安全地提示用户输入。

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

用户可以跳过设置并继续加载技能。Hermes 永远不会向模型暴露原始秘密值。网关和消息会话显示本地设置指南，而不是带内收集秘密。

:::tip 沙箱传递
当加载你的技能时，任何已设置的已声明 `required_environment_variables` 都会**自动传递**到 `execute_code` 和 `terminal` 沙箱 — 包括远程后端，如 Docker 和 Modal。你的技能脚本可以访问 `$TENOR_API_KEY`（或 Python 中的 `os.environ["TENOR_API_KEY"]`），用户无需额外配置。有关详细信息，请参阅[环境变量传递](/docs/user-guide/security#environment-variable-passthrough)。
:::

传统的 `prerequisites.env_vars` 仍然作为向后兼容的别名支持。

### 配置设置 (config.yaml)

技能可以声明存储在 `config.yaml` 中 `skills.config` 命名空间下的非秘密设置。与环境变量（存储在 `.env` 中的秘密）不同，配置设置用于路径、首选项和其他非敏感值。

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: 插件数据目录的路径
        default: "~/myplugin-data"
        prompt: 插件数据目录路径
      - key: myplugin.domain
        description: 插件操作的域
        default: ""
        prompt: 插件域（例如，AI/ML 研究）
```

每个条目支持：
- `key`（必需）— 设置的点路径（例如，`myplugin.path`）
- `description`（必需）— 解释设置控制什么
- `default`（可选）— 如果用户不配置，则为默认值
- `prompt`（可选）— 在 `hermes config migrate` 期间显示的提示文本；回退到 `description`

**工作原理：**

1. **存储：** 值写入 `config.yaml` 中的 `skills.config.<key>` 下：
   ```yaml
   skills:
     config:
       myplugin:
         path: ~/my-data
   ```

2. **发现：** `hermes config migrate` 扫描所有启用的技能，找到未配置的设置，并提示用户。设置也会在 `hermes config show` 中的"技能设置"下出现。

3. **运行时注入：** 当技能加载时，其配置值会被解析并附加到技能消息：
   ```
   [Skill config (from ~/.hermes/config.yaml):
     myplugin.path = /home/user/my-data
   ]
   ```
   代理可以看到配置的值，而无需自己读取 `config.yaml`。

4. **手动设置：** 用户也可以直接设置值：
   ```bash
   hermes config set skills.config.myplugin.path ~/my-data
   ```

:::tip 何时使用哪个
使用 `required_environment_variables` 用于 API 密钥、令牌和其他**秘密**（存储在 `~/.hermes/.env` 中，永远不会显示给模型）。使用 `config` 用于**路径、首选项和非敏感设置**（存储在 `config.yaml` 中，在配置显示中可见）。
:::

### 凭证文件要求（OAuth 令牌等）

使用 OAuth 或基于文件的凭证的技能可以声明需要挂载到远程沙箱的文件。这适用于存储为**文件**（不是环境变量）的凭证 — 通常是由设置脚本生成的 OAuth 令牌文件。

```yaml
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 令牌（由设置脚本创建）
  - path: google_client_secret.json
    description: Google OAuth2 客户端凭证
```

每个条目支持：
- `path`（必需）— 相对于 `~/.hermes/` 的文件路径
- `description`（可选）— 解释文件是什么以及如何创建

加载时，Hermes 会检查这些文件是否存在。缺少的文件会触发 `setup_needed`。现有文件会自动：
- **挂载到 Docker** 容器作为只读绑定挂载
- **同步到 Modal** 沙箱（在创建时 + 每个命令前，因此会话中期 OAuth 工作）
- 在**本地**后端可用，无需任何特殊处理

:::tip 何时使用哪个
使用 `required_environment_variables` 用于简单的 API 密钥和令牌（存储在 `~/.hermes/.env` 中的字符串）。使用 `required_credential_files` 用于 OAuth 令牌文件、客户端秘密、服务账户 JSON、证书或任何作为磁盘上文件的凭证。
:::

请参阅 `skills/productivity/google-workspace/SKILL.md` 获取同时使用两者的完整示例。

## 技能指南

### 无外部依赖

优先使用标准库 Python、curl 和现有的 Hermes 工具（`web_extract`、`terminal`、`read_file`）。如果需要依赖项，请在技能中记录安装步骤。

### 渐进式披露

将最常见的工作流放在首位。边缘情况和高级用法放在底部。这可以保持常见任务的令牌使用量低。

### 包含辅助脚本

对于 XML/JSON 解析或复杂逻辑，在 `scripts/` 中包含辅助脚本 — 不要期望 LLM 每次都内联编写解析器。

### 测试它

运行技能并验证代理是否正确遵循说明：

```bash
hermes chat --toolsets skills -q "Use the X skill to do Y"
```

## 技能应该放在哪里？

捆绑的技能（在 `skills/` 中）随每个 Hermes 安装一起提供。它们应该对**大多数用户广泛有用**：

- 文档处理、网络研究、常见开发工作流、系统管理
- 被广泛的人群定期使用

如果你的技能是官方的并且有用但不是普遍需要的（例如，付费服务集成、重量级依赖项），请将其放在**`optional-skills/`** 中 — 它随 repo 一起提供，可通过 `hermes skills browse` 发现（标记为"官方"），并以内置信任安装。

如果你的技能是专业的、社区贡献的或小众的，它更适合**技能中心** — 将其上传到注册表并通过 `hermes skills install` 共享。

## 发布技能

### 到技能中心

```bash
hermes skills publish skills/my-skill --to github --repo owner/repo
```

### 到自定义存储库

添加你的存储库作为 tap：

```bash
hermes skills tap add owner/repo
```

用户然后可以从你的存储库搜索和安装。

## 安全扫描

所有中心安装的技能都经过安全扫描，检查：

- 数据泄露模式
- 提示注入尝试
- 破坏性命令
- Shell 注入

信任级别：
- `builtin` — 随 Hermes 一起提供（始终受信任）
- `official` — 来自 repo 中的 `optional-skills/`（内置信任，无第三方警告）
- `trusted` — 来自 openai/skills、anthropics/skills
- `community` — 非危险发现可以用 `--force` 覆盖；`dangerous` 裁决仍然被阻止

Hermes 现在可以从多个外部发现模型使用第三方技能：
- 直接 GitHub 标识符（例如 `openai/skills/k8s`）
- `skills.sh` 标识符（例如 `skills-sh/vercel-labs/json-render/json-render-react`）
- 从 `/.well-known/skills/index.json` 提供的知名端点

如果你希望你的技能无需 GitHub 特定的安装程序即可被发现，考虑除了在存储库或市场中发布它们之外，还从知名端点提供它们。