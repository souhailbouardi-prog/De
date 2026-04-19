---
sidebar_position: 7
title: "将 SOUL.md 与 Hermes 一起使用"
description: "如何使用 SOUL.md 塑造 Hermes Agent 的默认声音，其中包含什么，以及它与 AGENTS.md 和 /personality 的区别"
---

# 将 SOUL.md 与 Hermes 一起使用

`SOUL.md` 是您的 Hermes 实例的**主要身份**。它是系统提示中的第一件事 — 它定义了代理是谁，如何说话，以及它避免什么。

如果您希望 Hermes 在每次与它交谈时都感觉像是同一个助手 — 或者如果您想用自己的身份完全替换 Hermes 角色 — 这就是要使用的文件。

## SOUL.md 的用途

使用 `SOUL.md` 用于：
- 语气
- 个性
- 沟通风格
- Hermes 应该多直接或多温暖
- Hermes 应该在风格上避免什么
- Hermes 应该如何处理不确定性、分歧和模糊性

简而言之：
- `SOUL.md` 关于 Hermes 是谁以及 Hermes 如何说话

## SOUL.md 不用于

不要将其用于：
- 特定于仓库的编码约定
- 文件路径
- 命令
- 服务端口
- 架构说明
- 项目工作流指令

这些属于 `AGENTS.md`。

一个好规则：
- 如果它应该适用于所有地方，将其放在 `SOUL.md` 中
- 如果它只属于一个项目，将其放在 `AGENTS.md` 中

## 它的位置

Hermes 现在只为当前实例使用全局 SOUL 文件：

```text
~/.hermes/SOUL.md
```

如果您使用自定义主目录运行 Hermes，它会变成：

```text
$HERMES_HOME/SOUL.md
```

## 首次运行行为

如果尚不存在，Hermes 会自动为您种子一个初始 `SOUL.md`。

这意味着大多数用户现在从一个可以立即阅读和编辑的真实文件开始。

重要：
- 如果您已经有 `SOUL.md`，Hermes 不会覆盖它
- 如果文件存在但为空，Hermes 不会从其中添加任何内容到提示中

## Hermes 如何使用它

当 Hermes 启动会话时，它从 `HERMES_HOME` 读取 `SOUL.md`，扫描它以查找提示注入模式，必要时截断它，并将其用作**代理身份** — 系统提示中的槽 #1。这意味着 SOUL.md 完全替换内置的默认身份文本。

如果 SOUL.md 缺失、为空或无法加载，Hermes 会回退到内置的默认身份。

文件周围不会添加包装语言。内容本身很重要 — 以您希望代理思考和说话的方式写作。

## 一个好的首次编辑

如果您不做其他事情，打开文件并只更改几行，使其感觉像您。

例如：

```markdown
You are direct, calm, and technically precise.
Prefer substance over politeness theater.
Push back clearly when an idea is weak.
Keep answers compact unless deeper detail is useful.
```

仅此一点就可以显著改变 Hermes 的感觉。

## 示例风格

### 1. 实用工程师

```markdown
You are a pragmatic senior engineer.
You care more about correctness and operational reality than sounding impressive.

## Style
- Be direct
- Be concise unless complexity requires depth
- Say when something is a bad idea
- Prefer practical tradeoffs over idealized abstractions

## Avoid
- Sycophancy
- Hype language
- Overexplaining obvious things
```

### 2. 研究伙伴

```markdown
You are a thoughtful research collaborator.
You are curious, honest about uncertainty, and excited by unusual ideas.

## Style
- Explore possibilities without pretending certainty
- Distinguish speculation from evidence
- Ask clarifying questions when the idea space is underspecified
- Prefer conceptual depth over shallow completeness
```

### 3. 教师 / 讲解员

```markdown
You are a patient technical teacher.
You care about understanding, not performance.

## Style
- Explain clearly
- Use examples when they help
- Do not assume prior knowledge unless the user signals it
- Build from intuition to details
```

### 4. 严格的审查者

```markdown
You are a rigorous reviewer.
You are fair, but you do not soften important criticism.

## Style
- Point out weak assumptions directly
- Prioritize correctness over harmony
- Be explicit about risks and tradeoffs
- Prefer blunt clarity to vague diplomacy
```

## 什么使 SOUL.md 强大？

强大的 `SOUL.md` 是：
- 稳定的
- 广泛适用的
- 声音具体的
- 不被临时指令过载

薄弱的 `SOUL.md` 是：
- 充满项目细节
- 矛盾的
- 试图微观管理每个响应形状
- 主要是通用填充物，如 "be helpful" 和 "be clear"

Hermes 已经尝试变得有帮助和清晰。`SOUL.md` 应该添加真实的个性和风格，而不是重述明显的默认值。

## 建议的结构

您不需要标题，但它们会有所帮助。

一个效果很好的简单结构：

```markdown
# Identity
Who Hermes is.

# Style
How Hermes should sound.

# Avoid
What Hermes should not do.

# Defaults
How Hermes should behave when ambiguity appears.
```

## SOUL.md vs /personality

这些是互补的。

使用 `SOUL.md` 作为您的持久基线。
使用 `/personality` 进行临时模式切换。

示例：
- 您的默认 SOUL 是务实和直接的
- 然后在一个会话中您使用 `/personality teacher`
- 稍后您切换回来，而不更改您的基础声音文件

## SOUL.md vs AGENTS.md

这是最常见的错误。

### 把这个放在 SOUL.md 中
- “Be direct.”
- “Avoid hype language.”
- “Prefer short answers unless depth helps.”
- “Push back when the user is wrong.”

### 把这个放在 AGENTS.md 中
- “Use pytest, not unittest.”
- “Frontend lives in `frontend/`.”
- “Never edit migrations directly.”
- “The API runs on port 8000.”

## 如何编辑它

```bash
nano ~/.hermes/SOUL.md
```

或

```bash
vim ~/.hermes/SOUL.md
```

然后重启 Hermes 或开始新会话。

## 实用工作流程

1. 从种子默认文件开始
2. 修剪任何不符合您想要的声音的内容
3. 添加 4–8 行，清楚地定义语气和默认值
4. 与 Hermes 交谈一段时间
5. 根据仍然感觉不对的地方进行调整

这种迭代方法比尝试一次性设计完美的个性更有效。

## 故障排除

### 我编辑了 SOUL.md 但 Hermes 听起来仍然一样

检查：
- 您编辑了 `~/.hermes/SOUL.md` 或 `$HERMES_HOME/SOUL.md`
- 不是某个本地仓库的 `SOUL.md`
- 文件不为空
- 您的会话在编辑后重新启动
- 没有 `/personality` 覆盖主导结果

### Hermes 忽略了我的 SOUL.md 的部分内容

可能的原因：
- 更高优先级的指令正在覆盖它
- 文件包含冲突的指导
- 文件太长并被截断
- 一些文本类似于提示注入内容，可能被扫描器阻止或更改

### 我的 SOUL.md 变得太特定于项目

将项目指令移动到 `AGENTS.md` 中，并保持 `SOUL.md` 专注于身份和风格。

## 相关文档

- [个性 & SOUL.md](/docs/user-guide/features/personality)
- [上下文文件](/docs/user-guide/features/context-files)
- [配置](/docs/user-guide/configuration)
- [提示和最佳实践](/docs/guides/tips)