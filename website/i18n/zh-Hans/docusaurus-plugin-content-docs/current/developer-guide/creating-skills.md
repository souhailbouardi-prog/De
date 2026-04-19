---
sidebar_position: 3
title: "创建技能"
description: "如何为 Hermes Agent 创建技能 — SKILL.md 格式、指南和发布"
---

# 创建技能

技能是为 Hermes Agent 添加新功能的首选方式。它们比工具更容易创建，不需要对智能体进行代码更改，并且可以与社区共享。

## 应该是技能还是工具？

在以下情况下将其设为**技能**：
- 该功能可以表示为指令 + shell 命令 + 现有工具
- 它包装了智能体可以通过 `terminal` 或 `web_extract` 调用的外部 CLI 或 API
- 它不需要自定义 Python 集成或内置到智能体中的 API 密钥管理
- 示例：arXiv 搜索、git 工作流、Docker 管理、PDF 处理、通过 CLI 工具的电子邮件

在以下情况下将其设为**工具**：
- 它需要与 API 密钥、认证流程或多组件配置进行端到端集成
- 它需要每次都必须精确执行的自定义处理逻辑
- 它处理二进制数据、流式处理或实时事件
- 示例：浏览器自动化、TTS、视觉分析

## 技能目录结构

捆绑的技能位于按类别组织的 `skills/` 中。官方可选技能在 `optional-skills/` 中使用相同的结构：

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
description: 简要描述（显示在技能搜索结果中）
version: 1.0.0
author: Your Name
license: MIT
platforms: [macos, linux]          # Optional — restrict to specific OS platforms
                                   #   Valid: macos, linux, windows
                                   #   Omit to load on all platforms (default)
metadata:
  hermes:
    tags: [Category, Subcategory, Keywords]
    related_skills: [other-skill-name]
    requires_toolsets: [web]            # Optional — only show when these toolsets are active
    requires_tools: [web_search]        # Optional — only show when these tools are available
    fallback_for_toolsets: [browser]    # Optional — hide when these toolsets are active
    fallback_for_tools: [browser_navigate]  # Optional — hide when these tools exist
    config:                              # Optional — config.yaml settings the skill needs
      - key: my.setting
        description: "What this setting controls"
        default: "sensible-default"
        prompt: "Display prompt for setup"
required_environment_variables:          # Optional — env vars the skill needs
  - name: MY_API_KEY
    prompt: "Enter your API key"
    help: "Get one at https://example.com"
    required_for: "API access"
---

# Skill Title

Brief intro.

## When to Use
Trigger conditions — when should the agent load this skill?

## Quick Reference
Table of common commands or API calls.

## Procedure
Step-by-step instructions the agent follows.

## Pitfalls
Known failure modes and how to handle them.

## Verification
How the agent confirms it worked.
```

### Platform-Specific Skills

Skills can restrict themselves to specific operating systems using the `platforms` field:

```yaml
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders)
platforms: [macos, linux]     # macOS and Linux
platforms: [windows]          # Windows only
```

When set, the skill is automatically hidden from the system prompt, `skills_list()`, and slash commands on incompatible platforms. If omitted or empty, the skill loads on all platforms (backward compatible).

### Conditional Skill Activation

Skills can declare dependencies on specific tools or toolsets. This controls whether the skill appears in the system prompt for a given session.

```yaml
metadata:
  hermes:
    requires_toolsets: [web]           # Hide if the web toolset is NOT active
    requires_tools: [web_search]       # Hide if web_search tool is NOT available
    fallback_for_toolsets: [browser]   # Hide if the browser toolset IS active
    fallback_for_tools: [browser_navigate]  # Hide if browser_navigate IS available
```

| Field | Behavior |
|-------|----------|
| `requires_toolsets` | Skill is **hidden** when ANY listed toolset is **not** available |
| `requires_tools` | Skill is **hidden** when ANY listed tool is **not** available |
| `fallback_for_toolsets` | Skill is **hidden** when ANY listed toolset **is** available |
| `fallback_for_tools` | Skill is **hidden** when ANY listed tool **is** available |

**Use case for `fallback_for_*`:** Create a skill that serves as a workaround when a primary tool isn't available. For example, a `duckduckgo-search` skill with `fallback_for_tools: [web_search]` only shows when the web search tool (which requires an API key) is not configured.

**Use case for `requires_*`:** Create a skill that only makes sense when certain tools are present. For example, a web scraping workflow skill with `requires_toolsets: [web]` won't clutter the prompt when web tools are disabled.

### Environment Variable Requirements

Skills can declare environment variables they need. When a skill is loaded via `skill_view`, its required vars are automatically registered for passthrough into sandboxed execution environments (terminal, execute_code).

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: "Tenor API key"               # Shown when prompting user
    help: "Get your key at https://tenor.com"  # Help text or URL
    required_for: "GIF search functionality"   # What needs this var
```

Each entry supports:
- `name` (required) — the environment variable name
- `prompt` (optional) — prompt text when asking the user for the value
- `help` (optional) — help text or URL for obtaining the value
- `required_for` (optional) — describes which feature needs this variable

Users can also manually configure passthrough variables in `config.yaml`:

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_VAR
    - ANOTHER_VAR
```

See `skills/apple/` for examples of macOS-only skills.

## Secure Setup on Load

Use `required_environment_variables` when a skill needs an API key or token. Missing values do **not** hide the skill from discovery. Instead, Hermes prompts for them securely when the skill is loaded in the local CLI.

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

The user can skip setup and keep loading the skill. Hermes never exposes the raw secret value to the model. Gateway and messaging sessions show local setup guidance instead of collecting secrets in-band.

:::tip Sandbox Passthrough
When your skill is loaded, any declared `required_environment_variables` that are set are **automatically passed through** to `execute_code` and `terminal` sandboxes — including remote backends like Docker and Modal. Your skill's scripts can access `$TENOR_API_KEY` (or `os.environ["TENOR_API_KEY"]` in Python) without the user needing to configure anything extra. See [Environment Variable Passthrough](/docs/user-guide/security#environment-variable-passthrough) for details.
:::

Legacy `prerequisites.env_vars` remains supported as a backward-compatible alias.

### Config Settings (config.yaml)

Skills can declare non-secret settings that are stored in `config.yaml` under the `skills.config` namespace. Unlike environment variables (which are secrets stored in `.env`), config settings are for paths, preferences, and other non-sensitive values.

```yaml
metadata:
  hermes:
    config:
      - key: wiki.path
        description: Path to the LLM Wiki knowledge base directory
        default: "~/wiki"
        prompt: Wiki directory path
      - key: wiki.domain
        description: Domain the wiki covers
        default: ""
        prompt: Wiki domain (e.g., AI/ML research)
```

Each entry supports:
- `key` (required) — dotpath for the setting (e.g., `wiki.path`)
- `description` (required) — explains what the setting controls
- `default` (optional) — default value if the user doesn't configure it
- `prompt` (optional) — prompt text shown during `hermes config migrate`; falls back to `description`

**How it works:**

1. **Storage:** Values are written to `config.yaml` under `skills.config.<key>`:
   ```yaml
   skills:
     config:
       wiki:
         path: ~/my-research
   ```

2. **Discovery:** `hermes config migrate` scans all enabled skills, finds unconfigured settings, and prompts the user. Settings also appear in `hermes config show` under "Skill Settings."

3. **Runtime injection:** When a skill loads, its config values are resolved and appended to the skill message:
   ```
   [Skill config (from ~/.hermes/config.yaml):
     wiki.path = /home/user/my-research
   ]
   ```
   The agent sees the configured values without needing to read `config.yaml` itself.

4. **Manual setup:** Users can also set values directly:
   ```bash
   hermes config set skills.config.wiki.path ~/my-wiki
   ```

:::tip When to use which
Use `required_environment_variables` for API keys, tokens, and other **secrets** (stored in `~/.hermes/.env`, never shown to the model). Use `config` for **paths, preferences, and non-sensitive settings** (stored in `config.yaml`, visible in config show).
:::

### Credential File Requirements (OAuth tokens, etc.)

Skills that use OAuth or file-based credentials can declare files that need to be mounted into remote sandboxes. This is for credentials stored as **files** (not env vars) — typically OAuth token files produced by a setup script.

```yaml
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials
```

Each entry supports:
- `path` (required) — file path relative to `~/.hermes/`
- `description` (optional) — explains what the file is and how it's created

When loaded, Hermes checks if these files exist. Missing files trigger `setup_needed`. Existing files are automatically:
- **Mounted into Docker** containers as read-only bind mounts
- **Synced into Modal** sandboxes (at creation + before each command, so mid-session OAuth works)
- Available on **local** backend without any special handling

:::tip When to use which
Use `required_environment_variables` for simple API keys and tokens (strings stored in `~/.hermes/.env`). Use `required_credential_files` for OAuth token files, client secrets, service account JSON, certificates, or any credential that's a file on disk.
:::

See the `skills/productivity/google-workspace/SKILL.md` for a complete example using both.

## Skill Guidelines

### No External Dependencies

Prefer stdlib Python, curl, and existing Hermes tools (`web_extract`, `terminal`, `read_file`). If a dependency is needed, document installation steps in the skill.

### Progressive Disclosure

Put the most common workflow first. Edge cases and advanced usage go at the bottom. This keeps token usage low for common tasks.

### Include Helper Scripts

For XML/JSON parsing or complex logic, include helper scripts in `scripts/` — don't expect the LLM to write parsers inline every time.

### Test It

Run the skill and verify the agent follows the instructions correctly:

```bash
hermes chat --toolsets skills -q "Use the X skill to do Y"
```

## Where Should the Skill Live?

Bundled skills (in `skills/`) ship with every Hermes install. They should be **broadly useful to most users**:

- Document handling, web research, common dev workflows, system administration
- Used regularly by a wide range of people

If your skill is official and useful but not universally needed (e.g., a paid service integration, a heavyweight dependency), put it in **`optional-skills/`** — it ships with the repo, is discoverable via `hermes skills browse` (labeled "official"), and installs with builtin trust.

If your skill is specialized, community-contributed, or niche, it's better suited for a **Skills Hub** — upload it to a registry and share it via `hermes skills install`.

## Publishing Skills

### To the Skills Hub

```bash
hermes skills publish skills/my-skill --to github --repo owner/repo
```

### To a Custom Repository

Add your repo as a tap:

```bash
hermes skills tap add owner/repo
```

Users can then search and install from your repository.

## Security Scanning

All hub-installed skills go through a security scanner that checks for:

- Data exfiltration patterns
- Prompt injection attempts
- Destructive commands
- Shell injection

Trust levels:
- `builtin` — ships with Hermes (always trusted)
- `official` — from `optional-skills/` in the repo (builtin trust, no third-party warning)
- `trusted` — from openai/skills, anthropics/skills
- `community` — non-dangerous findings can be overridden with `--force`; `dangerous` verdicts remain blocked

Hermes can now consume third-party skills from multiple external discovery models:
- direct GitHub identifiers (for example `openai/skills/k8s`)
- `skills.sh` identifiers (for example `skills-sh/vercel-labs/json-render/json-render-react`)
- well-known endpoints served from `/.well-known/skills/index.json`

If you want your skills to be discoverable without a GitHub-specific installer, consider serving them from a well-known endpoint in addition to publishing them in a repo or marketplace.