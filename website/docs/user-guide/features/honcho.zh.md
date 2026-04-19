---
sidebar_position: 99
title: "Honcho 记忆"
description: "通过 Honcho 实现 AI 原生持久记忆 — 辩证推理、多代理用户建模和深度个性化"
---

# Honcho 记忆

[Honcho](https://github.com/plastic-labs/honcho) 是一个 AI 原生的内存后端，在 Hermes 的内置内存系统之上添加了辩证推理和深度用户建模。Honcho 不是简单的键值存储，而是通过在对话结束后对其进行推理，维护一个关于用户是谁的运行模型 — 他们的偏好、沟通风格、目标和模式。

:::info Honcho 是一个内存提供者插件
Honcho 集成到 [内存提供者](./memory-providers.zh.md) 系统中。以下所有功能都通过统一的内存提供者接口提供。
:::

## Honcho 添加的功能

| 功能 | 内置内存 | Honcho |
|------|---------|--------|
| 跨会话持久性 | ✔ 基于文件的 MEMORY.md/USER.md | ✔ 带 API 的服务器端 |
| 用户配置文件 | ✔ 手动代理管理 | ✔ 自动辩证推理 |
| 会话摘要 | — | ✔ 会话范围的上下文注入 |
| 多代理隔离 | — | ✔ 每对等配置文件分离 |
| 观察模式 | — | ✔ 统一或定向观察 |
| 结论（派生见解） | — | ✔ 关于模式的服务器端推理 |
| 跨历史搜索 | ✔ FTS5 会话搜索 | ✔ 关于结论的语义搜索 |

**辩证推理**：在每个对话轮次后（由 `dialecticCadence` 控制），Honcho 分析交换内容并得出关于用户偏好、习惯和目标的见解。这些随着时间积累，使代理对用户有更深入的理解，超越用户明确陈述的内容。辩证支持多轮深度（1-3 轮），带有自动冷/热提示选择 — 冷启动查询关注一般用户事实，而热查询优先考虑会话范围的上下文。

**会话范围的上下文**：基本上下文现在包括会话摘要以及用户表示和对等卡。这使代理了解当前会话中已经讨论的内容，减少重复并实现连续性。

**多代理配置文件**：当多个 Hermes 实例与同一用户交谈时（例如，编码助手和个人助手），Honcho 维护单独的"对等"配置文件。每个对等方只能看到自己的观察和结论，防止上下文交叉污染。

## 设置

```bash
hermes memory setup    # 从提供者列表中选择 "honcho"
```

或手动配置：

```yaml
# ~/.hermes/config.yaml
memory:
  provider: honcho
```

```bash
echo "HONCHO_API_KEY=*** >> ~/.hermes/.env
```

在 [honcho.dev](https://honcho.dev) 获取 API 密钥。

## 架构

### 两层上下文注入

在每个轮次（在 `hybrid` 或 `context` 模式下），Honcho 组装两层注入到系统提示的上下文：

1. **基本上下文** — 会话摘要、用户表示、用户对等卡、AI 自我表示和 AI 身份卡。在 `contextCadence` 上刷新。这是"这个用户是谁"层。
2. **辩证补充** — LLM 合成的关于用户当前状态和需求的推理。在 `dialecticCadence` 上刷新。这是"现在什么重要"层。

两层都被连接并截断到 `contextTokens` 预算（如果设置）。

### 冷/热提示选择

辩证自动在两种提示策略之间选择：

- **冷启动**（尚未有基本上下文）：一般查询 — "这个人是谁？他们的偏好、目标和工作风格是什么？"
- **热会话**（存在基本上下文）：会话范围的查询 — "考虑到本次会话到目前为止讨论的内容，关于这个用户的什么上下文最相关？"

这根据基本上下文是否已填充自动发生。

### 三个正交配置旋钮

成本和深度由三个独立的旋钮控制：

| 旋钮 | 控制 | 默认值 |
|------|------|--------|
| `contextCadence` | `context()` API 调用之间的轮次（基础层刷新） | `1` |
| `dialecticCadence` | `peer.chat()` LLM 调用之间的轮次（辩证层刷新） | `3` |
| `dialecticDepth` | 每次辩证调用的 `.chat()` 轮次数（1-3） | `1` |

这些是正交的 — 您可以频繁刷新上下文但很少进行辩证，或者以低频率进行深度多轮辩证。示例：`contextCadence: 1, dialecticCadence: 5, dialecticDepth: 2` 每轮刷新基本上下文，每 5 轮运行辩证，每次辩证运行进行 2 轮。

### 辩证深度（多轮）

当 `dialecticDepth` > 1 时，每次辩证调用运行多个 `.chat()` 轮次：

- **轮次 0**：冷或热提示（见上文）
- **轮次 1**：自我审计 — 识别初始评估中的差距并从最近会话中综合证据
- **轮次 2**：调和 — 检查先前轮次之间的矛盾并产生最终综合

每个轮次使用成比例的推理级别（早期轮次较轻，主轮次为基础级别）。使用 `dialecticDepthLevels` 覆盖每轮级别 — 例如，深度 3 运行的 `["minimal", "medium", "high"]`。

如果先前轮次返回强信号（长而结构化的输出），轮次会提前退出，因此深度 3 并不总是意味着 3 次 LLM 调用。

## 配置选项

Honcho 在 `~/.honcho/config.json`（全局）或 `$HERMES_HOME/honcho.json`（配置文件本地）中配置。设置向导会为您处理这一点。

### 完整配置参考

| 键 | 默认值 | 描述 |
|-----|---------|---------|
| `contextTokens` | `null`（无上限） | 每轮自动注入上下文的令牌预算。设置为整数（例如 1200）以限制。在词边界处截断 |
| `contextCadence` | `1` | `context()` API 调用之间的最小轮次（基础层刷新） |
| `dialecticCadence` | `3` | `peer.chat()` LLM 调用之间的最小轮次（辩证层）。在 `tools` 模式下无关 — 模型显式调用 |
| `dialecticDepth` | `1` | 每次辩证调用的 `.chat()` 轮次数。限制在 1-3 之间 |
| `dialecticDepthLevels` | `null` | 每轮推理级别的可选数组，例如 `["minimal", "low", "medium"]`。覆盖成比例的默认值 |
| `dialecticReasoningLevel` | `'low'` | 基础推理级别：`minimal`、`low`、`medium`、`high`、`max` |
| `dialecticDynamic` | `true` | 当为 `true` 时，模型可以通过工具参数每次调用覆盖推理级别 |
| `dialecticMaxChars` | `600` | 注入到系统提示的辩证结果的最大字符数 |
| `recallMode` | `'hybrid'` | `hybrid`（自动注入 + 工具）、`context`（仅注入）、`tools`（仅工具） |
| `writeFrequency` | `'async'` | 何时刷新消息：`async`（后台线程）、`turn`（同步）、`session`（结束时批处理）或整数 N |
| `saveMessages` | `true` | 是否将消息持久化到 Honcho API |
| `observationMode` | `'directional'` | `directional`（全部开启）或 `unified`（共享池）。使用 `observation` 对象覆盖以进行粒度控制 |
| `messageMaxChars` | `25000` | 通过 `add_messages()` 发送的每条消息的最大字符数。如果超过则分块 |
| `dialecticMaxInputChars` | `10000` | 发送到 `peer.chat()` 的辩证查询输入的最大字符数 |
| `sessionStrategy` | `'per-directory'` | `per-directory`、`per-repo`、`per-session` 或 `global` |

**会话策略** 控制 Honcho 会话如何映射到您的工作：
- `per-session` — 每次 `hermes` 运行获得一个新会话。干净的开始，通过工具使用内存。推荐给新用户。
- `per-directory` — 每个工作目录一个 Honcho 会话。上下文在运行之间累积。
- `per-repo` — 每个 git 仓库一个会话。
- `global` — 所有目录共享一个会话。

**回忆模式** 控制内存如何流入对话：
- `hybrid` — 上下文自动注入系统提示 AND 工具可用（模型决定何时查询）。
- `context` — 仅自动注入，工具隐藏。
- `tools` — 仅工具，无自动注入。代理必须显式调用 `honcho_reasoning`、`honcho_search` 等。

**每种回忆模式的设置：**

| 设置 | `hybrid` | `context` | `tools` |
|------|----------|-----------|---------|
| `writeFrequency` | 刷新消息 | 刷新消息 | 刷新消息 |
| `contextCadence` | 控制基础上下文刷新 | 控制基础上下文刷新 | 无关 — 无注入 |
| `dialecticCadence` | 控制自动 LLM 调用 | 控制自动 LLM 调用 | 无关 — 模型显式调用 |
| `dialecticDepth` | 每次调用多轮 | 每次调用多轮 | 无关 — 模型显式调用 |
| `contextTokens` | 限制注入 | 限制注入 | 无关 — 无注入 |
| `dialecticDynamic` | 控制模型覆盖 | N/A（无工具） | 控制模型覆盖 |

在 `tools` 模式下，模型完全控制 — 它在需要时调用 `honcho_reasoning`，使用它选择的任何 `reasoning_level`。节奏和预算设置仅适用于具有自动注入的模式（`hybrid` 和 `context`）。

## 工具

当 Honcho 作为内存提供者激活时，五个工具可用：

| 工具 | 用途 |
|------|------|
| `honcho_profile` | 读取或更新对等卡 — 传递 `card`（事实列表）进行更新，省略以读取 |
| `honcho_search` | 上下文的语义搜索 — 原始摘录，无 LLM 合成 |
| `honcho_context` | 完整会话上下文 — 摘要、表示、卡、最近消息 |
| `honcho_reasoning` | 来自 Honcho LLM 的合成答案 — 传递 `reasoning_level`（minimal/low/medium/high/max）控制深度 |
| `honcho_conclude` | 创建或删除结论 — 传递 `conclusion` 创建，`delete_id` 删除（仅 PII） |

## CLI 命令

```bash
hermes honcho status          # 连接状态、配置和关键设置
hermes honcho setup           # 交互式设置向导
hermes honcho strategy        # 显示或设置会话策略
hermes honcho peer            # 为多代理设置更新对等名称
hermes honcho mode            # 显示或设置回忆模式
hermes honcho tokens          # 显示或设置上下文令牌预算
hermes honcho identity        # 显示 Honcho 对等身份
hermes honcho sync            # 同步所有配置文件的主机块
hermes honcho enable          # 启用 Honcho
hermes honcho disable         # 禁用 Honcho
```

## 从 `hermes honcho` 迁移

如果您之前使用独立的 `hermes honcho setup`：

1. 您现有的配置（`honcho.json` 或 `~/.honcho/config.json`）被保留
2. 您的服务器端数据（记忆、结论、用户配置文件）完好无损
3. 在 config.yaml 中设置 `memory.provider: honcho` 以重新激活

无需重新登录或重新设置。运行 `hermes memory setup` 并选择 "honcho" — 向导会检测您现有的配置。

## 完整文档

请参阅 [内存提供者 — Honcho](./memory-providers.zh.md#honcho) 获取完整参考。