---
sidebar_position: 11
title: "使用 Cron 自动化一切"
description: "使用 Hermes cron 的真实世界自动化模式 — 监控、报告、管道和多技能工作流"
---

# 使用 Cron 自动化一切

[每日简报机器人教程](/docs/guides/daily-briefing-bot) 涵盖了基础知识。本指南更进一步 — 提供五个真实世界的自动化模式，您可以将其适应于自己的工作流程。

有关完整的功能参考，请参阅 [定时任务（Cron）](/docs/user-guide/features/cron)。

:::info 关键概念
Cron 作业在全新的智能体会话中运行，没有当前聊天的记忆。提示必须**完全自包含** — 包含智能体需要知道的一切。
:::

---

## 模式 1：网站变更监控

监控 URL 的变更，仅在有差异时通知您。

`script` 参数是这里的秘密武器。Python 脚本在每次执行前运行，其 stdout 成为智能体的上下文。脚本处理机械工作（获取、比较差异）；智能体处理推理（这个变更是否有趣？）。

创建监控脚本：

```bash
mkdir -p ~/.hermes/scripts
```

```python title="~/.hermes/scripts/watch-site.py"
import hashlib, json, os, urllib.request

URL = "https://example.com/pricing"
STATE_FILE = os.path.expanduser("~/.hermes/scripts/.watch-site-state.json")

# 获取当前内容
req = urllib.request.Request(URL, headers={"User-Agent": "Hermes-Monitor/1.0"})
content = urllib.request.urlopen(req, timeout=30).read().decode()
current_hash = hashlib.sha256(content.encode()).hexdigest()

# 加载之前的状态
prev_hash = None
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        prev_hash = json.load(f).get("hash")

# 保存当前状态
with open(STATE_FILE, "w") as f:
    json.dump({"hash": current_hash, "url": URL}, f)

# Output for agent
if prev_hash and prev_hash != current_hash:
    print(f"CHANGE DETECTED on {URL}")
    print(f"Previous hash: {prev_hash}")
    print(f"Current hash: {current_hash}")
    print(f"\nCurrent content (first 2000 chars):\n{content[:2000]}")
else:
    print("NO_CHANGE")
```

设置 cron 作业：

```bash
/cron add "every 1h" "如果脚本输出说 CHANGE DETECTED，总结页面上更改了什么以及为什么这可能很重要。如果它说 NO_CHANGE，仅用 [SILENT] 响应。" --script ~/.hermes/scripts/watch-site.py --name "定价监控" --deliver telegram
```

:::tip 技巧
当智能体的最终响应包含 `[SILENT]` 时，传递会被抑制。这意味着您只有在实际发生事情时才会收到通知 — 安静时段不会收到垃圾信息。
:::

---

## 模式 2：每周报告

从多个来源编译信息，形成格式化摘要。这每周运行一次并传递到您的主频道。

```bash
/cron add "0 9 * * 1" "生成涵盖以下内容的每周报告：

1. 搜索网络以查找过去一周的前 5 个 AI 新闻故事
2. 搜索 GitHub 以查找'machine-learning'主题中的趋势仓库
3. 检查 Hacker News 以查找讨论最多的 AI/ML 帖子

格式为每个来源都有章节的干净摘要。包含链接。
保持在 500 字以下 — 仅突出重要内容。" --name "每周 AI 摘要" --deliver telegram
```

从 CLI：

```bash
hermes cron create "0 9 * * 1" \
  "生成涵盖顶级 AI 新闻、趋势 ML GitHub 仓库和讨论最多的 HN 帖子的每周报告。格式包含章节，包含链接，保持在 500 字以下。" \
  --name "每周 AI 摘要" \
  --deliver telegram
```

`0 9 * * 1` 是标准的 cron 表达式：每周一上午 9:00。

---

## 模式 3：GitHub 仓库监控

监控仓库的新问题、PR 或发布。

```bash
/cron add "every 6h" "检查 GitHub 仓库 NousResearch/hermes-agent 以查找：
- 过去 6 小时内打开的新问题
- 过去 6 小时内打开或合并的新 PR
- 任何新发布

使用终端运行 gh 命令：
  gh issue list --repo NousResearch/hermes-agent --state open --json number,title,author,createdAt --limit 10
  gh pr list --repo NousResearch/hermes-agent --state all --json number,title,author,createdAt,mergedAt --limit 10

仅筛选过去 6 小时内的项目。如果没有新内容，用 [SILENT] 响应。
否则，提供活动的简洁摘要。" --name "仓库观察者" --deliver discord
```

:::warning 自包含提示
请注意，提示包含了确切的 `gh` 命令。cron 智能体没有之前运行的记忆或您的偏好 — 请详细说明一切。
:::

---

## 模式 4：数据收集管道

定期抓取数据，保存到文件，并随时间检测趋势。此模式结合了脚本（用于收集）和智能体（用于分析）。

```python title="~/.hermes/scripts/collect-prices.py"
import json, os, urllib.request
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.hermes/data/prices")
os.makedirs(DATA_DIR, exist_ok=True)

# 获取当前数据（示例：加密货币价格）
url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
data = json.loads(urllib.request.urlopen(url, timeout=30).read())

# 追加到历史文件
entry = {"timestamp": datetime.now().isoformat(), "prices": data}
history_file = os.path.join(DATA_DIR, "history.jsonl")
with open(history_file, "a") as f:
    f.write(json.dumps(entry) + "\n")

# 加载最近的历史记录进行分析
lines = open(history_file).readlines()
recent = [json.loads(l) for l in lines[-24:]]  # 最后 24 个数据点

# 智能体的输出
print(f"Current: BTC=${data['bitcoin']['usd']}, ETH=${data['ethereum']['usd']}")
print(f"Data points collected: {len(lines)} total, showing last {len(recent)}")
print(f"\nRecent history:")
for r in recent[-6:]:
    print(f"  {r['timestamp']}: BTC=${r['prices']['bitcoin']['usd']}, ETH=${r['prices']['ethereum']['usd']}")
```

```bash
/cron add "every 1h" "分析脚本输出的价格数据。报告：
1. 当前价格
2. 过去 6 个数据点的趋势方向（上升/下降/持平）
3. 任何显著移动（>5% 变化）

如果价格持平且没有显著内容，用 [SILENT] 响应。
如果有重大移动，解释发生了什么。" \
  --script ~/.hermes/scripts/collect-prices.py \
  --name "价格跟踪器" \
  --deliver telegram
```

脚本负责机械收集；智能体添加推理层。

---

## 模式 5：多技能工作流

将技能链接在一起以完成复杂的计划任务。技能在提示执行前按顺序加载。

```bash
# 使用 arxiv 技能查找论文，然后使用 obsidian 技能保存笔记
/cron add "0 8 * * *" "搜索 arXiv 以查找过去一天中关于'语言模型推理'的 3 篇最有趣的论文。对于每篇论文，创建一个 Obsidian 笔记，包含标题、作者、摘要摘要和关键贡献。" \
  --skill arxiv \
  --skill obsidian \
  --name "论文摘要"
```

直接从工具：

```python
cronjob(
    action="create",
    skills=["arxiv", "obsidian"],
    prompt="搜索 arXiv 以查找过去一天中关于'语言模型推理'的论文。将前 3 篇保存为 Obsidian 笔记。",
    schedule="0 8 * * *",
    name="论文摘要",
    deliver="local"
)
```

技能按顺序加载 — 首先是 `arxiv`（教智能体如何搜索论文），然后是 `obsidian`（教如何写笔记）。提示将它们联系在一起。

---

## 管理您的作业

```bash
# 列出所有活动作业
/cron list

# 立即触发作业（用于测试）
/cron run <job_id>

# 暂停作业而不删除它
/cron pause <job_id>

# 编辑运行中作业的计划或提示
/cron edit <job_id> --schedule "every 4h"
/cron edit <job_id> --prompt "更新的任务描述"

# 向现有作业添加或删除技能
/cron edit <job_id> --skill arxiv --skill obsidian
/cron edit <job_id> --clear-skills

# 永久删除作业
/cron remove <job_id>
```

---

## 传递目标

`--deliver` 标志控制结果的去向：

| 目标 | 示例 | 使用场景 |
|--------|---------|----------|
| `origin` | `--deliver origin` | 创建作业的同一聊天（默认） |
| `local` | `--deliver local` | 仅保存到本地文件 |
| `telegram` | `--deliver telegram` | 您的 Telegram 主频道 |
| `discord` | `--deliver discord` | 您的 Discord 主频道 |
| `slack` | `--deliver slack` | 您的 Slack 主频道 |
| 特定聊天 | `--deliver telegram:-1001234567890` | 特定的 Telegram 群组 |
| 线程 | `--deliver telegram:-1001234567890:17585` | 特定的 Telegram 主题线程 |

---

## 提示

**使提示自包含。** cron 作业中的智能体没有您对话的记忆。在提示中直接包含 URL、仓库名称、格式偏好和传递指令。

**自由使用 [SILENT]。** 对于监控作业，始终包含诸如"如果没有变更，用 [SILENT] 响应。"这样的指令。这可以防止通知噪音。

**使用脚本进行数据收集。** `script` 参数让 Python 脚本处理枯燥的部分（HTTP 请求、文件 I/O、状态跟踪）。智能体只看到脚本的 stdout 并对其应用推理。这比让智能体自己进行获取更便宜、更可靠。

**使用 `/cron run` 进行测试。** 在等待计划触发之前，使用 `/cron run <job_id>` 立即执行并验证输出是否正确。

**计划表达式。** 支持的格式：相对延迟（`30m`）、间隔（`every 2h`）、标准 cron 表达式（`0 9 * * *`）和 ISO 时间戳（`2025-06-15T09:00:00`）。不支持 `daily at 9am` 这样的自然语言 — 请改用 `0 9 * * *`。

---

*有关完整的 cron 参考 — 所有参数、边缘情况和内部机制 — 请参阅[计划任务（Cron）](/docs/user-guide/features/cron)。*