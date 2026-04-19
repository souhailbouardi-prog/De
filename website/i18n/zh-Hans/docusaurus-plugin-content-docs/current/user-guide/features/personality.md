---
sidebar_position: 9
title: "个性与 SOUL.md"
description: "使用全局 SOUL.md、内置个性和自定义角色定义来自定义 Hermes Agent 的个性"
---

# 个性与 SOUL.md

Hermes Agent 的个性是完全可定制的。`SOUL.md` 是**主要身份** — 它是系统提示中的第一件事，定义了智能体是谁。

- `SOUL.md` — 一个持久的角色文件，位于 `HERMES_HOME` 中，作为智能体的身份（系统提示中的槽位 #1）
- 内置或自定义 `/personality` 预设 — 会话级系统提示覆盖

如果您想更改 Hermes 的身份 — 或用完全不同的智能体角色替换它 — 请编辑 `SOUL.md`。

## SOUL.md 现在的工作方式

Hermes 现在会自动在以下位置生成默认的 `SOUL.md`：

```text
~/.hermes/SOUL.md
```

更准确地说，它使用当前实例的 `HERMES_HOME`，所以如果您使用自定义主目录运行 Hermes，它会使用：

```text
$HERMES_HOME/SOUL.md
```

### 重要行为

- **SOUL.md 是智能体的主要身份。** 它占据系统提示中的槽位 #1，替换硬编码的默认身份。
- 如果 `SOUL.md` 尚不存在，Hermes 会自动创建一个初始版本
- 现有的用户 `SOUL.md` 文件永远不会被覆盖
- Hermes 只从 `HERMES_HOME` 加载 `SOUL.md`
- Hermes 不会在当前工作目录中查找 `SOUL.md`
- 如果 `SOUL.md` 存在但为空，或无法加载，Hermes 会回退到内置的默认身份
- 如果 `SOUL.md` 有内容，该内容会在安全扫描和截断后逐字注入
- SOUL.md **不会**在上下文文件部分重复 — 它只出现一次，作为身份

这使得 `SOUL.md` 成为真正的每用户或每实例身份，而不仅仅是一个附加层。

## 为什么采用这种设计

这使个性保持可预测性。

如果 Hermes 从您碰巧启动它的任何目录加载 `SOUL.md`，您的个性可能会在项目之间意外更改。通过仅从 `HERMES_HOME` 加载，个性属于 Hermes 实例本身。

这也使向用户传授变得更容易：
- "编辑 `~/.hermes/SOUL.md` 以更改 Hermes 的默认个性。"

## 在哪里编辑它

对于大多数用户：

```bash
~/.hermes/SOUL.md
```

如果您使用自定义主目录：

```bash
$HERMES_HOME/SOUL.md
```

## SOUL.md 中应该包含什么？

使用它来提供持久的声音和个性指导，例如：
- 语气
- 沟通风格
- 直接程度
- 默认互动风格
- 风格上应该避免的内容
- Hermes 应如何处理不确定性、分歧或歧义

较少用于：
- 一次性项目说明
- 文件路径
- 仓库约定
- 临时工作流详细信息

这些属于 `AGENTS.md`，而不是 `SOUL.md`。

## 良好的 SOUL.md 内容

一个好的 SOUL 文件应该：
- 在不同上下文中保持稳定
- 足够广泛，适用于许多对话
- 足够具体，能够实质性地塑造声音
- 专注于沟通和身份，而不是特定任务的指令

### 示例

```markdown
# Personality

您是一位务实的高级工程师，有着强烈的品味。
您追求真理、清晰和实用，而不是礼貌的客套。

## 风格
- 直接但不冷漠
- 注重实质而非客套
- 当某事是坏主意时提出反对
- 坦率地承认不确定性
- 除非深度有用，否则保持解释简洁

## 应该避免的
- 奉承
- 炒作语言
- 如果用户的框架是错误的，不要重复它
- 过度解释显而易见的事情

## 技术姿态
- 偏好简单的系统而非复杂的系统
- 关心实际操作现实，而非理想化的架构
- 将边缘情况视为设计的一部分，而非后续清理
```

## Hermes 如何将内容注入到提示中

`SOUL.md` 内容直接进入系统提示的槽位 #1 — 智能体身份位置。它周围不会添加任何包装语言。

内容会经过：
- 提示注入扫描
- 如果内容太大则截断

如果文件为空、仅包含空白或无法读取，Hermes 会回退到内置的默认身份（"You are Hermes Agent, an intelligent AI assistant created by Nous Research..."）。当设置了 `skip_context_files` 时（例如在子智能体/委托上下文中），此回退也适用。

## 安全扫描

`SOUL.md` 像其他承载上下文的文件一样，在包含之前会扫描提示注入模式。

这意味着您仍然应该将其重点放在角色/声音上，而不是尝试偷偷加入奇怪的元指令。

## SOUL.md 与 AGENTS.md 的区别

这是最重要的区别。

### SOUL.md
用于：
- 身份
- 语气
- 风格
- 沟通默认值
- 个性级行为

### AGENTS.md
用于：
- 项目架构
- 编码约定
- 工具偏好
- 仓库特定工作流
- 命令、端口、路径、部署说明

一个有用的规则：
- 如果它应该跟随您到任何地方，它属于 `SOUL.md`
- 如果它属于项目，它属于 `AGENTS.md`

## SOUL.md 与 `/personality` 的区别

`SOUL.md` 是您持久的默认个性。

`/personality` 是会话级覆盖，用于更改或补充当前系统提示。

因此：
- `SOUL.md` = 基线声音
- `/personality` = 临时模式切换

示例：
- 保持实用的默认 SOUL，然后使用 `/personality teacher` 进行辅导对话
- 保持简洁的 SOUL，然后使用 `/personality creative` 进行头脑风暴

## 内置个性

Hermes 附带内置个性，您可以使用 `/personality` 切换到这些个性。

| 名称 | 描述 |
|------|-------------|
| **helpful** | 友好的通用助手 |
| **concise** | 简洁、直接的回应 |
| **technical** | 详细、准确的技术专家 |
| **creative** | 创新、跳出框框的思维 |
| **teacher** | 耐心的教育者，有清晰的例子 |
| **kawaii** | 可爱的表达、闪光和热情 ★ |
| **catgirl** | 猫耳女孩，带有猫一样的表达，nya~ |
| **pirate** | Hermes 船长，精通技术的海盗 |
| **shakespeare** | 具有戏剧性 flair 的吟游诗人散文 |
| **surfer** | 完全放松的兄弟氛围 |
| **noir** | 硬汉侦探叙事 |
| **uwu** |  maximum 可爱的 uwu 语言 |
| **philosopher** | 对每个查询进行深度思考 |
| **hype** | 最大能量和热情!!! |

## 使用命令切换个性

### CLI

```text
/personality
/personality concise
/personality technical
```

### 消息平台

```text
/personality teacher
```

这些是方便的覆盖，但您的全局 `SOUL.md` 仍然为 Hermes 提供持久的默认个性，除非覆盖有意义地改变了它。

## 配置中的自定义个性

您还可以在 `~/.hermes/config.yaml` 的 `agent.personalities` 下定义命名的自定义个性。

```yaml
agent:
  personalities:
    codereviewer: >
      You are a meticulous code reviewer. Identify bugs, security issues,
      performance concerns, and unclear design choices. Be precise and constructive.
```

然后使用以下命令切换到它：

```text
/personality codereviewer
```

## 推荐工作流

一个强大的默认设置是：

1. 在 `~/.hermes/SOUL.md` 中保持深思熟虑的全局 `SOUL.md`
2. 将项目说明放在 `AGENTS.md` 中
3. 仅在需要临时模式转变时使用 `/personality`

这给您：
- 稳定的声音
- 项目特定行为在其所属的地方
- 需要时的临时控制

## 个性如何与完整提示交互

在高层次上，提示堆栈包括：
1. **SOUL.md**（智能体身份 — 如果 SOUL.md 不可用，则为内置回退）
2. 工具感知行为指导
3. 记忆/用户上下文
4. 技能指导
5. 上下文文件（`AGENTS.md`、`.cursorrules`）
6. 时间戳
7. 平台特定格式提示
8. 可选的系统提示覆盖，如 `/personality`

`SOUL.md` 是基础 — 其他一切都建立在它之上。

## 相关文档

- [上下文文件](/docs/user-guide/features/context-files)
- [配置](/docs/user-guide/configuration)
- [提示与最佳实践](/docs/guides/tips)
- [SOUL.md 指南](/docs/guides/use-soul-with-hermes)

## CLI 外观与对话个性

对话个性和 CLI 外观是分开的：

- `SOUL.md`、`agent.system_prompt` 和 `/personality` 影响 Hermes 的说话方式
- `display.skin` 和 `/skin` 影响 Hermes 在终端中的外观

有关终端外观，请参阅 [皮肤与主题](./skins.md)。