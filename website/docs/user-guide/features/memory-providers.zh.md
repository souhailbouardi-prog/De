---
sidebar_position: 4
title: "内存提供商"
description: "外部内存提供商插件 — Honcho、OpenViking、Mem0、Hindsight、Holographic、RetainDB、ByteRover、Supermemory"
---

# 内存提供商

Hermes Agent 附带 8 个外部内存提供商插件，为智能体提供持久的、跨会话的知识，超越内置的 MEMORY.md 和 USER.md。一次只能激活**一个**外部提供商 — 内置内存始终与它一起激活。

## 快速开始

```bash
hermes memory setup      # 交互式选择器 + 配置
hermes memory status     # 检查当前激活的提供商
hermes memory off        # 禁用外部提供商
```

您也可以通过 `hermes plugins` → Provider Plugins → Memory Provider 选择活跃的内存提供商。

或在 `~/.hermes/config.yaml` 中手动设置：

```yaml
memory:
  provider: openviking   # 或 honcho, mem0, hindsight, holographic, retaindb, byterover, supermemory
```

## 工作原理

当内存提供商激活时，Hermes 会自动：

1. **注入提供商上下文**到系统提示中（提供商知道的内容）
2. **在每个回合前预取相关记忆**（后台，非阻塞）
3. **在每次响应后同步对话回合**到提供商
4. **在会话结束时提取记忆**（对于支持的提供商）
5. **将内置内存写入镜像**到外部提供商
6. **添加提供商特定工具**，以便智能体可以搜索、存储和管理记忆

内置内存（MEMORY.md / USER.md）继续像以前一样工作。外部提供商是附加的。

## 可用提供商

### Honcho

AI 原生跨会话用户建模，具有辩证推理、会话范围上下文注入、语义搜索和持久结论。基础上下文现在包括会话摘要以及用户表示和对等卡，让智能体了解已经讨论过的内容。

| | |
|---|---|
| **最适合** | 具有跨会话上下文、用户-智能体对齐的多智能体系统 |
| **要求** | `pip install honcho-ai` + [API 密钥](https://app.honcho.dev) 或自托管实例 |
| **数据存储** | Honcho 云或自托管 |
| **成本** | Honcho 定价（云）/ 免费（自托管） |

**工具（5 个）：** `honcho_profile`（读取/更新对等卡）、`honcho_search`（语义搜索）、`honcho_context`（会话上下文 — 摘要、表示、卡片、消息）、`honcho_reasoning`（LLM 合成）、`honcho_conclude`（创建/删除结论）

**架构：** 两层上下文注入 — 基础层（会话摘要 + 表示 + 对等卡，在 `contextCadence` 上刷新）加上辩证补充（LLM 推理，在 `dialecticCadence` 上刷新）。辩证会根据是否存在基础上下文自动选择冷启动提示（一般用户事实）与热提示（会话范围上下文）。

**三个正交配置旋钮**独立控制成本和深度：

- `contextCadence` — 基础层刷新频率（API 调用频率）
- `dialecticCadence` — 辩证 LLM 触发频率（LLM 调用频率）
- `dialecticDepth` — 每次辩证调用的 `.chat()` 传递次数（1–3，推理深度）

**设置向导：**
```bash
hermes honcho setup        # (传统命令) 
# 或
hermes memory setup        # 选择 "honcho"
```

**配置：** `$HERMES_HOME/honcho.json`（配置文件本地）或 `~/.honcho/config.json`（全局）。解析顺序：`$HERMES_HOME/honcho.json` > `~/.hermes/honcho.json` > `~/.honcho/config.json`。请参阅 [配置参考](https://github.com/hermes-ai/hermes-agent/blob/main/plugins/memory/honcho/README.md) 和 [Honcho 集成指南](https://docs.honcho.dev/v3/guides/integrations/hermes)。

<details>
<summary>完整配置参考</summary>

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `apiKey` | -- | 来自 [app.honcho.dev](https://app.honcho.dev) 的 API 密钥 |
| `baseUrl` | -- | 自托管 Honcho 的基础 URL |
| `peerName` | -- | 用户对等身份 |
| `aiPeer` | host key | AI 对等身份（每个配置文件一个） |
| `workspace` | host key | 共享工作区 ID |
| `contextTokens` | `null`（无上限） | 每回合自动注入上下文的令牌预算。在词边界处截断 |
| `contextCadence` | `1` | `context()` API 调用之间的最小回合数（基础层刷新） |
| `dialecticCadence` | `3` | `peer.chat()` LLM 调用之间的最小回合数。仅适用于 `hybrid`/`context` 模式 |
| `dialecticDepth` | `1` | 每次辩证调用的 `.chat()` 传递次数。限制为 1–3。传递 0：冷/热提示，传递 1：自我审计，传递 2：调和 |
| `dialecticDepthLevels` | `null` | 每次传递的可选推理级别数组，例如 `["minimal", "low", "medium"]`。覆盖比例默认值 |
| `dialecticReasoningLevel` | `'low'` | 基础推理级别：`minimal`、`low`、`medium`、`high`、`max` |
| `dialecticDynamic` | `true` | 当为 `true` 时，模型可以通过工具参数覆盖每次调用的推理级别 |
| `dialecticMaxChars` | `600` | 注入到系统提示中的辩证结果的最大字符数 |
| `recallMode` | `'hybrid'` | `hybrid`（自动注入 + 工具）、`context`（仅注入）、`tools`（仅工具） |
| `writeFrequency` | `'async'` | 何时刷新消息：`async`（后台线程）、`turn`（同步）、`session`（会话结束批处理）或整数 N |
| `saveMessages` | `true` | 是否将消息持久化到 Honcho API |
| `observationMode` | `'directional'` | `directional`（全部开启）或 `unified`（共享池）。使用 `observation` 对象覆盖 |
| `messageMaxChars` | `25000` | 每条消息的最大字符数（超过则分块） |
| `dialecticMaxInputChars` | `10000` | 传递给 `peer.chat()` 的辩证查询输入的最大字符数 |
| `sessionStrategy` | `'per-directory'` | `per-directory`、`per-repo`、`per-session`、`global` |

</details>

<details>
<summary>最小 honcho.json（云）</summary>

```json
{
  "apiKey": "your-key-from-app.honcho.dev",
  "hosts": {
    "hermes": {
      "enabled": true,
      "aiPeer": "hermes",
      "peerName": "your-name",
      "workspace": "hermes"
    }
  }
}
```

</details>

<details>
<summary>最小 honcho.json（自托管）</summary>

```json
{
  "baseUrl": "http://localhost:8000",
  "hosts": {
    "hermes": {
      "enabled": true,
      "aiPeer": "hermes",
      "peerName": "your-name",
      "workspace": "hermes"
    }
  }
}
```

</details>

:::tip 从 `hermes honcho` 迁移
如果您之前使用 `hermes honcho setup`，您的配置和所有服务器端数据都保持不变。只需通过设置向导再次启用或手动设置 `memory.provider: honcho` 以通过新系统重新激活。
:::

**多智能体 / 配置文件：**

每个 Hermes 配置文件获得自己的 Honcho AI 对等体，同时共享同一个工作区 — 所有配置文件看到相同的用户表示，但每个智能体构建自己的身份和观察。

```bash
hermes profile create coder --clone   # 创建 honcho 对等体 "coder"，从默认继承配置
```

`--clone` 的作用：在 `honcho.json` 中创建 `hermes.coder` 主机块，其中 `aiPeer: "coder"`，共享 `workspace`，继承 `peerName`、`recallMode`、`writeFrequency`、`observation` 等。对等体在 Honcho 中急切创建，因此它在第一条消息之前就存在。

对于在设置 Honcho 之前创建的配置文件：

```bash
hermes honcho sync   # 扫描所有配置文件，为任何缺失的配置文件创建主机块
```

这从默认的 `hermes` 主机块继承设置，并为每个配置文件创建新的 AI 对等体。幂等 — 跳过已经有主机块的配置文件。

<details>
<summary>完整 honcho.json 示例（多配置文件）</summary>

```json
{
  "apiKey": "your-key",
  "workspace": "hermes",
  "peerName": "eri",
  "hosts": {
    "hermes": {
      "enabled": true,
      "aiPeer": "hermes",
      "workspace": "hermes",
      "peerName": "eri",
      "recallMode": "hybrid",
      "writeFrequency": "async",
      "sessionStrategy": "per-directory",
      "observation": {
        "user": { "observeMe": true, "observeOthers": true },
        "ai": { "observeMe": true, "observeOthers": true }
      },
      "dialecticReasoningLevel": "low",
      "dialecticDynamic": true,
      "dialecticCadence": 3,
      "dialecticDepth": 1,
      "dialecticMaxChars": 600,
      "contextCadence": 1,
      "messageMaxChars": 25000,
      "saveMessages": true
    },
    "hermes.coder": {
      "enabled": true,
      "aiPeer": "coder",
      "workspace": "hermes",
      "peerName": "eri",
      "recallMode": "tools",
      "observation": {
        "user": { "observeMe": true, "observeOthers": false },
        "ai": { "observeMe": true, "observeOthers": true }
      }
    },
    "hermes.writer": {
      "enabled": true,
      "aiPeer": "writer",
      "workspace": "hermes",
      "peerName": "eri"
    }
  },
  "sessions": {
    "/home/user/myproject": "myproject-main"
  }
}
```

</details>

请参阅 [配置参考](https://github.com/hermes-ai/hermes-agent/blob/main/plugins/memory/honcho/README.md) 和 [Honcho 集成指南](https://docs.honcho.dev/v3/guides/integrations/hermes)。


---

### OpenViking

火山引擎（字节跳动）的上下文数据库，具有文件系统式知识层次结构、分层检索和自动记忆提取为 6 个类别。

| | |
|---|---|
| **最适合** | 具有结构化浏览的自托管知识管理 |
| **要求** | `pip install openviking` + 运行服务器 |
| **数据存储** | 自托管（本地或云） |
| **成本** | 免费（开源，AGPL-3.0） |

**工具：** `viking_search`（语义搜索）、`viking_read`（分层：摘要/概览/完整）、`viking_browse`（文件系统导航）、`viking_remember`（存储事实）、`viking_add_resource`（摄取 URL/文档）

**设置：**
```bash
# 先启动 OpenViking 服务器
pip install openviking
openviking-server

# 然后配置 Hermes
hermes memory setup    # 选择 "openviking"
# 或手动：
hermes config set memory.provider openviking
echo "OPENVIKING_ENDPOINT=http://localhost:1933" >> ~/.hermes/.env
```

**关键特性：**
- 分层上下文加载：L0（约 100 个令牌）→ L1（约 2k）→ L2（完整）
- 会话提交时自动记忆提取（配置文件、偏好、实体、事件、案例、模式）
- `viking://` URI 方案用于层次化知识浏览

---

### Mem0

服务器端 LLM 事实提取，具有语义搜索、重排序和自动去重。

| | |
|---|---|
| **最适合** | 无需干预的内存管理 — Mem0 自动处理提取 |
| **要求** | `pip install mem0ai` + API 密钥 |
| **数据存储** | Mem0 云 |
| **成本** | Mem0 定价 |

**工具：** `mem0_profile`（所有存储的记忆）、`mem0_search`（语义搜索 + 重排序）、`mem0_conclude`（存储逐字事实）

**设置：**
```bash
hermes memory setup    # 选择 "mem0"
# 或手动：
hermes config set memory.provider mem0
echo "MEM0_API_KEY=your-key" >> ~/.hermes/.env
```

**配置：** `$HERMES_HOME/mem0.json`

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `user_id` | `hermes-user` | 用户标识符 |
| `agent_id` | `hermes` | 智能体标识符 |

---

### Hindsight

具有知识图谱、实体解析和多策略检索的长期记忆。`hindsight_reflect` 工具提供其他提供商没有的跨记忆合成。自动保留完整的对话回合（包括工具调用），带有会话级文档跟踪。

| | |
|---|---|
| **最适合** | 基于知识图谱的回忆，带有实体关系 |
| **要求** | 云：来自 [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io) 的 API 密钥。本地：LLM API 密钥（OpenAI、Groq、OpenRouter 等） |
| **数据存储** | Hindsight 云或本地嵌入式 PostgreSQL |
| **成本** | Hindsight 定价（云）或免费（本地） |

**工具：** `hindsight_retain`（带实体提取的存储）、`hindsight_recall`（多策略搜索）、`hindsight_reflect`（跨记忆合成）

**设置：**
```bash
hermes memory setup    # 选择 "hindsight"
# 或手动：
hermes config set memory.provider hindsight
echo "HINDSIGHT_API_KEY=your-key" >> ~/.hermes/.env
```

设置向导会自动安装依赖项，并且只安装所选模式所需的依赖项（云模式需要 `hindsight-client`，本地模式需要 `hindsight-all`）。需要 `hindsight-client >= 0.4.22`（如果过时，会话开始时会自动升级）。

**本地模式 UI：** `hindsight-embed -p hermes ui start`

**配置：** `$HERMES_HOME/hindsight/config.json`

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `mode` | `cloud` | `cloud` 或 `local` |
| `bank_id` | `hermes` | 记忆库标识符 |
| `recall_budget` | `mid` | 回忆彻底性：`low` / `mid` / `high` |
| `memory_mode` | `hybrid` | `hybrid`（上下文 + 工具）、`context`（仅自动注入）、`tools`（仅工具） |
| `auto_retain` | `true` | 自动保留对话回合 |
| `auto_recall` | `true` | 每个回合前自动回忆记忆 |
| `retain_async` | `true` | 在服务器上异步处理保留 |
| `tags` | — | 存储记忆时应用的标签 |
| `recall_tags` | — | 回忆时过滤的标签 |

请参阅 [插件 README](https://github.com/NousResearch/hermes-agent/blob/main/plugins/memory/hindsight/README.md) 获取完整的配置参考。

---

### Holographic

本地 SQLite 事实存储，具有 FTS5 全文搜索、信任评分和 HRR（全息约简表示）用于组合代数查询。

| | |
|---|---|
| **最适合** | 具有高级检索的本地仅内存，无外部依赖 |
| **要求** | 无（SQLite 始终可用）。NumPy 可选用于 HRR 代数。 |
| **数据存储** | 本地 SQLite |
| **成本** | 免费 |

**工具：** `fact_store`（9 个操作：添加、搜索、探测、相关、推理、矛盾、更新、删除、列出）、`fact_feedback`（有帮助/无帮助评分，训练信任评分）

**设置：**
```bash
hermes memory setup    # 选择 "holographic"
# 或手动：
hermes config set memory.provider holographic
```

**配置：** `config.yaml` 中的 `plugins.hermes-memory-store`

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `db_path` | `$HERMES_HOME/memory_store.db` | SQLite 数据库路径 |
| `auto_extract` | `false` | 会话结束时自动提取事实 |
| `default_trust` | `0.5` | 默认信任评分（0.0–1.0） |

**独特功能：**
- `probe` — 特定实体的代数回忆（关于某人/某事的所有事实）
- `reason` — 跨多个实体的组合 AND 查询
- `contradict` — 冲突事实的自动检测
- 信任评分，带有不对称反馈（+0.05 有帮助 / -0.10 无帮助）

---

### RetainDB

云内存 API，具有混合搜索（向量 + BM25 + 重排序）、7 种内存类型和增量压缩。

| | |
|---|---|
| **最适合** | 已经使用 RetainDB 基础设施的团队 |
| **要求** | RetainDB 账户 + API 密钥 |
| **数据存储** | RetainDB 云 |
| **成本** | $20/月 |

**工具：** `retaindb_profile`（用户配置文件）、`retaindb_search`（语义搜索）、`retaindb_context`（任务相关上下文）、`retaindb_remember`（带类型 + 重要性的存储）、`retaindb_forget`（删除记忆）

**设置：**
```bash
hermes memory setup    # 选择 "retaindb"
# 或手动：
hermes config set memory.provider retaindb
echo "RETAINDB_API_KEY=your-key" >> ~/.hermes/.env
```

---

### ByteRover

通过 `brv` CLI 实现的持久内存 — 分层知识树，具有分层检索（模糊文本 → LLM 驱动搜索）。本地优先，可选云同步。

| | |
|---|---|
| **最适合** | 希望拥有可移植、本地优先内存和 CLI 的开发人员 |
| **要求** | ByteRover CLI（`npm install -g byterover-cli` 或 [安装脚本](https://byterover.dev)） |
| **数据存储** | 本地（默认）或 ByteRover 云（可选同步） |
| **成本** | 免费（本地）或 ByteRover 定价（云） |

**工具：** `brv_query`（搜索知识树）、`brv_curate`（存储事实/决策/模式）、`brv_status`（CLI 版本 + 树统计）

**设置：**
```bash
# 先安装 CLI
curl -fsSL https://byterover.dev/install.sh | sh

# 然后配置 Hermes
hermes memory setup    # 选择 "byterover"
# 或手动：
hermes config set memory.provider byterover
```

**关键特性：**
- 自动预压缩提取（在上下文压缩丢弃洞察之前保存它们）
- 知识树存储在 `$HERMES_HOME/byterover/`（配置文件范围）
- SOC2 Type II 认证的云同步（可选）

---

### Supermemory

语义长期记忆，具有配置文件回忆、语义搜索、显式记忆工具和通过 Supermemory 图谱 API 进行会话结束对话摄取。

| | |
|---|---|
| **最适合** | 具有用户分析和会话级图谱构建的语义回忆 |
| **要求** | `pip install supermemory` + [API 密钥](https://supermemory.ai) |
| **数据存储** | Supermemory 云 |
| **成本** | Supermemory 定价 |

**工具：** `supermemory_store`（保存显式记忆）、`supermemory_search`（语义相似性搜索）、`supermemory_forget`（按 ID 或最佳匹配查询忘记）、`supermemory_profile`（持久配置文件 + 最近上下文）

**设置：**
```bash
hermes memory setup    # 选择 "supermemory"
# 或手动：
hermes config set memory.provider supermemory
echo 'SUPERMEMORY_API_KEY=***' >> ~/.hermes/.env
```

**配置：** `$HERMES_HOME/supermemory.json`

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `container_tag` | `hermes` | 用于搜索和写入的容器标签。支持 `{identity}` 模板用于配置文件范围标签。 |
| `auto_recall` | `true` | 回合前注入相关记忆上下文 |
| `auto_capture` | `true` | 每次响应后存储清理的用户-助手回合 |
| `max_recall_results` | `10` | 格式化到上下文中的最大回忆项数 |
| `profile_frequency` | `50` | 第一回合和每 N 回合包含配置文件事实 |
| `capture_mode` | `all` | 默认跳过微小或琐碎的回合 |
| `search_mode` | `hybrid` | 搜索模式：`hybrid`、`memories` 或 `documents` |
| `api_timeout` | `5.0` | SDK 和摄取请求的超时 |

**环境变量：** `SUPERMEMORY_API_KEY`（必需）、`SUPERMEMORY_CONTAINER_TAG`（覆盖配置）。

**关键特性：**
- 自动上下文围栏 — 从捕获的回合中剥离回忆的记忆，防止递归记忆污染
- 会话结束对话摄取，用于更丰富的图谱级知识构建
- 配置文件事实在第一回合和可配置的间隔注入
- 琐碎消息过滤（跳过 "ok"、"thanks" 等）
- **配置文件范围容器** — 在 `container_tag` 中使用 `{identity}`（例如 `hermes-{identity}` → `hermes-coder`）以隔离每个 Hermes 配置文件的记忆
- **多容器模式** — 启用 `enable_custom_container_tags` 并使用 `custom_containers` 列表让智能体在命名容器之间读写。自动操作（同步、预取）保留在主容器上。

<details>
<summary>多容器示例</summary>

```json
{
  "container_tag": "hermes",
  "enable_custom_container_tags": true,
  "custom_containers": ["project-alpha", "shared-knowledge"],
  "custom_container_instructions": "Use project-alpha for coding context."
}
```

</details>

**支持：** [Discord](https://supermemory.link/discord) · [support@supermemory.com](mailto:support@supermemory.com)

---

## 提供商比较

| 提供商 | 存储 | 成本 | 工具 | 依赖项 | 独特功能 |
|----------|---------|------|-------|-------------|----------------|
| **Honcho** | 云 | 付费 | 5 | `honcho-ai` | 辩证用户建模 + 会话范围上下文 |
| **OpenViking** | 自托管 | 免费 | 5 | `openviking` + 服务器 | 文件系统层次结构 + 分层加载 |
| **Mem0** | 云 | 付费 | 3 | `mem0ai` | 服务器端 LLM 提取 |
| **Hindsight** | 云/本地 | 免费/付费 | 3 | `hindsight-client` | 知识图谱 + 反射合成 |
| **Holographic** | 本地 | 免费 | 2 | 无 | HRR 代数 + 信任评分 |
| **RetainDB** | 云 | $20/月 | 5 | `requests` | 增量压缩 |
| **ByteRover** | 本地/云 | 免费/付费 | 3 | `brv` CLI | 预压缩提取 |
| **Supermemory** | 云 | 付费 | 4 | `supermemory` | 上下文围栏 + 会话图谱摄取 + 多容器 |

## 配置文件隔离

每个提供商的数据按 [配置文件](/docs/user-guide/profiles) 隔离：

- **本地存储提供商**（Holographic、ByteRover）使用 `$HERMES_HOME/` 路径，每个配置文件不同
- **配置文件提供商**（Honcho、Mem0、Hindsight、Supermemory）将配置存储在 `$HERMES_HOME/` 中，因此每个配置文件有自己的凭据
- **云提供商**（RetainDB）自动派生配置文件范围的项目名称
- **环境变量提供商**（OpenViking）通过每个配置文件的 `.env` 文件配置

## 构建内存提供商

请参阅 [开发者指南：内存提供商插件](/docs/developer-guide/memory-provider-plugin) 了解如何创建自己的内存提供商。