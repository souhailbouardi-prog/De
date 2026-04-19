---
sidebar_position: 7
---

# 配置文件命令参考

本页面涵盖与 [Hermes 配置文件](../user-guide/profiles.zh.md) 相关的所有命令。有关一般 CLI 命令，请参阅 [CLI 命令参考](./cli-commands.zh.md)。

## `hermes profile`

```bash
hermes profile <subcommand>
```

管理配置文件的顶级命令。运行 `hermes profile` 而不带子命令会显示帮助信息。

| 子命令 | 描述 |
|--------|------|
| `list` | 列出所有配置文件。 |
| `use` | 设置活动（默认）配置文件。 |
| `create` | 创建新配置文件。 |
| `delete` | 删除配置文件。 |
| `show` | 显示配置文件的详细信息。 |
| `alias` | 重新生成配置文件的 shell 别名。 |
| `rename` | 重命名配置文件。 |
| `export` | 将配置文件导出到 tar.gz 归档。 |
| `import` | 从 tar.gz 归档导入配置文件。 |

## `hermes profile list`

```bash
hermes profile list
```

列出所有配置文件。当前活动的配置文件用 `*` 标记。

**示例：**

```bash
$ hermes profile list
  default
* work
  dev
  personal
```

无选项。

## `hermes profile use`

```bash
hermes profile use <name>
```

将 `<name>` 设置为活动配置文件。所有后续的 `hermes` 命令（不带 `-p`）将使用此配置文件。

| 参数 | 描述 |
|------|------|
| `<name>` | 要激活的配置文件名称。使用 `default` 返回基本配置文件。 |

**示例：**

```bash
hermes profile use work
hermes profile use default
```

## `hermes profile create`

```bash
hermes profile create <name> [options]
```

创建新配置文件。

| 参数 / 选项 | 描述 |
|-------------|------|
| `<name>` | 新配置文件的名称。必须是有效的目录名称（字母数字、连字符、下划线）。 |
| `--clone` | 从当前配置文件复制 `config.yaml`、`.env` 和 `SOUL.md`。 |
| `--clone-all` | 从当前配置文件复制所有内容（配置、记忆、技能、会话、状态）。 |
| `--clone-from <profile>` | 从特定配置文件而不是当前配置文件克隆。与 `--clone` 或 `--clone-all` 一起使用。 |
| `--no-alias` | 跳过包装脚本创建。 |

**示例：**

```bash
# 空白配置文件 — 需要完整设置
hermes profile create mybot

# 仅从当前配置文件克隆配置
hermes profile create work --clone

# 从当前配置文件克隆所有内容
hermes profile create backup --clone-all

# 从特定配置文件克隆配置
hermes profile create work2 --clone --clone-from work
```

## `hermes profile delete`

```bash
hermes profile delete <name> [options]
```

删除配置文件并移除其 shell 别名。

| 参数 / 选项 | 描述 |
|-------------|------|
| `<name>` | 要删除的配置文件。 |
| `--yes`, `-y` | 跳过确认提示。 |

**示例：**

```bash
hermes profile delete mybot
hermes profile delete mybot --yes
```

:::warning
这会永久删除配置文件的整个目录，包括所有配置、记忆、会话和技能。无法删除当前活动的配置文件。
:::

## `hermes profile show`

```bash
hermes profile show <name>
```

显示配置文件的详细信息，包括其主目录、配置的模型、网关状态、技能数量和配置文件状态。

| 参数 | 描述 |
|------|------|
| `<name>` | 要检查的配置文件。 |

**示例：**

```bash
$ hermes profile show work
Profile: work
Path:    ~/.hermes/profiles/work
Model:   anthropic/claude-sonnet-4 (anthropic)
Gateway: stopped
Skills:  12
.env:    exists
SOUL.md: exists
Alias:   ~/.local/bin/work
```

## `hermes profile alias`

```bash
hermes profile alias <name> [options]
```

重新生成 `~/.local/bin/<name>` 处的 shell 别名脚本。如果别名被意外删除或在移动 Hermes 安装后需要更新，这很有用。

| 参数 / 选项 | 描述 |
|-------------|------|
| `<name>` | 要为其创建/更新别名的配置文件。 |
| `--remove` | 移除包装脚本而不是创建它。 |
| `--name <alias>` | 自定义别名名称（默认：配置文件名称）。 |

**示例：**

```bash
hermes profile alias work
# 创建/更新 ~/.local/bin/work

hermes profile alias work --name mywork
# 创建 ~/.local/bin/mywork

hermes profile alias work --remove
# 移除包装脚本
```

## `hermes profile rename`

```bash
hermes profile rename <old-name> <new-name>
```

重命名配置文件。更新目录和 shell 别名。

| 参数 | 描述 |
|------|------|
| `<old-name>` | 当前配置文件名称。 |
| `<new-name>` | 新配置文件名称。 |

**示例：**

```bash
hermes profile rename mybot assistant
# ~/.hermes/profiles/mybot → ~/.hermes/profiles/assistant
# ~/.local/bin/mybot → ~/.local/bin/assistant
```

## `hermes profile export`

```bash
hermes profile export <name> [options]
```

将配置文件导出为压缩的 tar.gz 归档。

| 参数 / 选项 | 描述 |
|-------------|------|
| `<name>` | 要导出的配置文件。 |
| `-o`, `--output <path>` | 输出文件路径（默认：`<name>.tar.gz`）。 |

**示例：**

```bash
hermes profile export work
# 在当前目录创建 work.tar.gz

hermes profile export work -o ./work-2026-03-29.tar.gz
```

## `hermes profile import`

```bash
hermes profile import <archive> [options]
```

从 tar.gz 归档导入配置文件。

| 参数 / 选项 | 描述 |
|-------------|------|
| `<archive>` | 要导入的 tar.gz 归档的路径。 |
| `--name <name>` | 导入的配置文件的名称（默认：从归档推断）。 |

**示例：**

```bash
hermes profile import ./work-2026-03-29.tar.gz
# 从归档推断配置文件名称

hermes profile import ./work-2026-03-29.tar.gz --name work-restored
```

## `hermes -p` / `hermes --profile`

```bash
hermes -p <name> <command> [options]
hermes --profile <name> <command> [options]
```

全局标志，用于在特定配置文件下运行任何 Hermes 命令，而不更改粘性默认值。这会在命令持续期间覆盖活动配置文件。

| 选项 | 描述 |
|------|------|
| `-p <name>`, `--profile <name>` | 用于此命令的配置文件。 |

**示例：**

```bash
hermes -p work chat -q "Check the server status"
hermes --profile dev gateway start
hermes -p personal skills list
hermes -p work config edit
```

## `hermes completion`

```bash
hermes completion <shell>
```

生成 shell 补全脚本。包括配置文件名称和配置文件子命令的补全。

| 参数 | 描述 |
|------|------|
| `<shell>` | 要为其生成补全的 shell：`bash` 或 `zsh`。 |

**示例：**

```bash
# 安装补全
hermes completion bash >> ~/.bashrc
hermes completion zsh >> ~/.zshrc

# 重新加载 shell
source ~/.bashrc
```

安装后，标签补全适用于：
- `hermes profile <TAB>` — 子命令（list, use, create 等）
- `hermes profile use <TAB>` — 配置文件名称
- `hermes -p <TAB>` — 配置文件名称

## 另请参阅

- [配置文件用户指南](../user-guide/profiles.zh.md)
- [CLI 命令参考](./cli-commands.zh.md)
- [常见问题 — 配置文件部分](./faq.zh.md#profiles)