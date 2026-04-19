---
sidebar_position: 7
title: "使用 SOUL.md 与 Hermes"
description: "如何使用 SOUL.md 塑造 Hermes Agent 的默认声音，什么内容属于这里，以及它与 AGENTS.md 和 /personality 的区别"
---

# 使用 SOUL.md 与 Hermes

`SOUL.md` 是您 Hermes 实例的**主要身份**。它是系统提示中的第一件事 — 它定义了智能体是谁，如何说话，以及避免什么。

如果您希望 Hermes 在每次与您交谈时都感觉像是同一个助手 — 或者如果您想完全用自己的角色替换 Hermes 角色 — 这就是您要使用的文件。

## SOUL.md 的用途

使用 `SOUL.md` 用于：
- 语气
- 个性
- 沟通风格
- Hermes 应该有多直接或热情
- Hermes 在风格上应该避免什么
- Hermes 应该如何处理不确定性、分歧和歧义

简而言之：
- `SOUL.md` 是关于 Hermes 是谁以及 Hermes 如何说话

## SOUL.md 不用于什么

不要将其用于：
- 仓库特定的编码约定
- 文件路径
- 命令
- 服务端口
- 架构说明
- 项目工作流指令

这些属于 `AGENTS.md`。

一个好的规则：
- 如果它应该适用于所有地方，将其放在 `SOUL.md` 中
- 如果它只属于一个项目，将其放在 `AGENTS.md` 中

## 它位于何处

Hermes 现在只使用当前实例的全局 SOUL 文件：

```text
~/.hermes/SOUL.md
```

如果您使用自定义主目录运行 Hermes，它变为：

```text
$HERMES_HOME/SOUL.md
```

## 首次运行行为

如果 `SOUL.md` 尚不存在，Hermes 会自动为您生成一个初始版本。

这意味着大多数用户现在开始时就有一个可以立即阅读和编辑的真实文件。

重要：
- 如果您已经有 `SOUL.md`，Hermes 不会覆盖它
- 如果文件存在但为空，Hermes 不会将其内容添加到提示中

## Hermes 如何使用它

当 Hermes 开始会话时，它会从 `HERMES_HOME` 读取 `SOUL.md`，扫描其中的提示注入模式，如有需要则截断，并将其用作**智能体身份** — 系统提示中的槽位 #1。这意味着 SOUL.md 完全替换了内置的默认身份文本。

如果 SOUL.md 缺失、为空或无法加载，Hermes 会回退到内置的默认身份。

文件周围没有添加包装语言。内容本身很重要 — 按照您希望智能体思考和说话的方式编写。

## 一个好的首次编辑

如果您不做其他任何事情，打开文件并只更改几行，使其感觉像您。

例如：

```markdown
You are direct, calm, and technically precise.
Prefer substance over politeness theater.
Push back clearly when an idea is weak.
Keep answers compact unless deeper detail is useful.
```

仅此一项就能显著改变 Hermes 的感觉。

## 示例风格

### 1. 务实的工程师

```markdown
You are a pragmatic senior engineer.
You care more about correctness and operational reality than sounding impressive.

## 风格
- 直接
- 简洁，除非复杂性需要深度
- 当某事是坏主意时说出来
- 偏好实际权衡而非理想化的抽象

## 避免
- 奉承
- 炒作语言
- 过度解释显而易见的事情
```

### 2. 研究伙伴

```markdown
您是一位深思熟虑的研究合作者。
您好奇、坦率地承认不确定性，并对非比寻常的想法感到兴奋。

## 风格
- 不假装确定性的情况下探索可能性
- 区分推测和证据
- 当想法空间未指定时提出澄清问题
- 偏好概念深度而非浅薄的完整性
```

### 3. 教师/解释者

```markdown
您是一位耐心的技术老师。
您关心理解，而非表现。

## 风格
- 清晰地解释
- 使用帮助时的例子
- 不要假设先验知识，除非用户发出信号
- 从直觉构建到细节
```

### 4. 严格的审查者

```markdown
您是一位严格的审查者。
您是公平的，但不会软化重要的批评。

## 风格
- 直接指出脆弱的假设
- 优先考虑正确性而非和谐
- 明确说明风险和权衡
- 偏好直率的清晰而非模糊的外交手段
```

## 什么造就了一个强大的 SOUL.md？

一个强大的 `SOUL.md` 是：
- 稳定的
- 广泛适用的
- 声音具体的
- 没有过载临时指令的

一个薄弱的 `SOUL.md` 是：
- 充满项目细节的
- 自相矛盾的
- 试图微观管理每个响应形状的
- 主要是通用填充词，如 "be helpful" 和 "be clear"

Hermes 已经试图提供帮助和清晰。`SOUL.md` 应该添加真实的个性和风格，而不是重申明显的默认值。

## 建议的结构

您不需要标题，但它们有帮助。

一个效果良好的简单结构：

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

它们是互补的。

使用 `SOUL.md` 作为您的持久基线。
使用 `/personality` 进行临时模式切换。

示例：
- 您的默认 SOUL 是务实和直接的
- 然后在一个会话中您使用 `/personality teacher`
- 后来您切换回，而不改变您的基础声音文件

## SOUL.md vs AGENTS.md

这是最常见的错误。

### 将这些放入 SOUL.md
- “Be direct.”
- “Avoid hype language.”
- “Prefer short answers unless depth helps.”
- “Push back when the user is wrong.”

### 将这些放入 AGENTS.md
- “Use pytest, not unittest.”
- “Frontend lives in `frontend/`.”
- “Never edit migrations directly.”
- “The API runs on port 8000.”

## 如何编辑它

```bash
nano ~/.hermes/SOUL.md
```

或者

```bash
vim ~/.hermes/SOUL.md
```

然后重新启动 Hermes 或开始新会话。

## 实用工作流程

1. 从生成的默认文件开始
2. 修剪任何不符合您想要的声音的内容
3. 添加 4-8 行明确定义语气和默认值的内容
4. 与 Hermes 交谈一段时间
5. 根据仍然感觉不对的地方进行调整

这种迭代方法比尝试一次性设计完美的个性效果更好。

## 故障排除

### 我编辑了 SOUL.md，但 Hermes 听起来仍然相同

检查：
- 您编辑了 `~/.hermes/SOUL.md` 或 `$HERMES_HOME/SOUL.md`
- 不是某个仓库本地的 `SOUL.md`
- 文件不为空
- 编辑后您的会话已重新启动
- 没有 `/personality` 覆盖主导结果

### Hermes 忽略了我的 SOUL.md 的部分内容

可能的原因：
- 更高优先级的指令正在覆盖它
- 文件包含相互矛盾的指导
- 文件太长被截断了
- 部分文本类似于提示注入内容，可能被扫描器阻止或修改

### 我的 SOUL.md 变得过于项目特定

将项目指令移至 `AGENTS.md`，并保持 `SOUL.md` 专注于身份和风格。

## 相关文档

- [个性与 SOUL.md](/docs/user-guide/features/personality)
- [上下文文件](/docs/user-guide/features/context-files)
- [配置](/docs/user-guide/configuration)
- [技巧与最佳实践](/docs/guides/tips)