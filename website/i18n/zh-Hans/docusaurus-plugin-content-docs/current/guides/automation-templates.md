---
sidebar_position: 15
title: "自动化模板"
description: "即用型自动化配方 — 定时任务、GitHub 事件触发器、API webhook 和多技能工作流"
---

# 自动化模板

常见自动化模式的复制粘贴配方。每个模板都使用 Hermes 内置的 [cron 调度器](/docs/user-guide/features/cron) 进行基于时间的触发器，以及 [webhook 平台](/docs/user-guide/messaging/webhooks) 进行事件驱动的触发器。

每个模板都适用于**任何模型** — 不锁定到单一提供商。

:::tip 三种触发器类型
| 触发器 | 方式 | 工具 |
|---------|-----|------|
| **定时** | 按节奏运行（每小时、每晚、每周） | `cronjob` 工具或 `/cron` 斜杠命令 |
| **GitHub 事件** | 在 PR 打开、推送、问题、CI 结果时触发 | Webhook 平台 (`hermes webhook subscribe`) |
| **API 调用** | 外部服务向您的端点 POST JSON | Webhook 平台 (config.yaml 路由或 `hermes webhook subscribe`) |

所有三种都支持发送到 Telegram、Discord、Slack、SMS、电子邮件、GitHub 评论或本地文件。
:::

---

## 开发工作流

### 夜间待办事项分类

每晚标记、优先级排序和总结新问题。向您的团队频道发送摘要。

**触发器：** 定时（每晚）

```bash
hermes cron create "0 2 * * *" \
  "您是一个项目管理者，正在对 NousResearch/hermes-agent GitHub 仓库的问题进行分类。

1. 运行：gh issue list --repo NousResearch/hermes-agent --state open --json number,title,labels,author,createdAt --limit 30
2. 识别过去 24 小时内打开的问题
3. 对于每个新问题：
   - 建议一个优先级标签（P0-关键、P1-高、P2-中、P3-低）
   - 建议一个类别标签（bug、feature、docs、security）
   - 写一行分类说明
4. 总结：总开放问题数、今日新增、按优先级细分

格式化为干净的摘要。如果没有新问题，用 [SILENT] 响应。" \
  --name "夜间待办事项分类" \
  --deliver telegram
```

### 自动 PR 代码审查

在打开时自动审查每个拉取请求。直接在 PR 上发布审查评论。

**触发器：** GitHub webhook

**选项 A — 动态订阅 (CLI):**

```bash
hermes webhook subscribe github-pr-review \
  --events "pull_request" \
  --prompt "审查此拉取请求：
仓库：{repository.full_name}
PR #{pull_request.number}：{pull_request.title}
作者：{pull_request.user.login}
操作：{action}
差异 URL：{pull_request.diff_url}

使用以下命令获取差异：curl -sL {pull_request.diff_url}

审查以下内容：
- 安全问题（注入、身份验证绕过、代码中的密钥）
- 性能问题（N+1 查询、无限循环、内存泄漏）
- 代码质量（命名、重复、错误处理）
- 新行为缺少测试

发布简洁的审查。如果 PR 是微不足道的文档/拼写错误更改，请简要说明。" \
  --skills "github-code-review" \
  --deliver github_comment
```

**选项 B — 静态路由 (config.yaml):**

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "your-global-secret"
      routes:
        github-pr-review:
          events: ["pull_request"]
          secret: "github-webhook-secret"
          prompt: |
            审查 PR #{pull_request.number}：{pull_request.title}
            仓库：{repository.full_name}
            作者：{pull_request.user.login}
            差异 URL：{pull_request.diff_url}
            审查安全性、性能和代码质量。
          skills: ["github-code-review"]
          deliver: "github_comment"
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{pull_request.number}"
```

然后在 GitHub 中：**设置 → Webhooks → 添加 webhook** → Payload URL：`http://your-server:8644/webhooks/github-pr-review`，内容类型：`application/json`，密钥：`github-webhook-secret`，事件：**Pull requests**。

### 文档漂移检测

每周扫描已合并的 PR，以查找需要文档更新的 API 更改。

**触发器：** 定时（每周）

```bash
hermes cron create "0 9 * * 1" \
  "扫描 NousResearch/hermes-agent 仓库以查找文档漂移。

1. 运行：gh pr list --repo NousResearch/hermes-agent --state merged --json number,title,files,mergedAt --limit 30
2. 筛选过去 7 天内合并的 PR
3. 对于每个合并的 PR，检查它是否修改了：
   - 工具架构（tools/*.py）— 可能需要 docs/reference/tools-reference.md 更新
   - CLI 命令（hermes_cli/commands.py、hermes_cli/main.py）— 可能需要 docs/reference/cli-commands.md 更新
   - 配置选项（hermes_cli/config.py）— 可能需要 docs/user-guide/configuration.md 更新
   - 环境变量 — 可能需要 docs/reference/environment-variables.md 更新
4. 交叉引用：对于每个代码更改，检查相应的文档页面是否也在同一 PR 中更新

报告代码更改但文档未更新的任何差距。如果一切同步，用 [SILENT] 响应。" \
  --name "文档漂移检测" \
  --deliver telegram
```

### 依赖安全审计

每日扫描项目依赖项中的已知漏洞。

**触发器：** 定时（每日）

```bash
hermes cron create "0 6 * * *" \
  "对 hermes-agent 项目运行依赖安全审计。

1. cd ~/.hermes/hermes-agent && source .venv/bin/activate
2. 运行：pip audit --format json 2>/dev/null || pip audit 2>&1
3. 运行：npm audit --json 2>/dev/null（如果 website/ 目录存在）
4. 检查任何 CVSS 分数 >= 7.0 的 CVE

如果发现漏洞：
- 列出每个漏洞的包名称、版本、CVE ID、严重性
- 检查是否有可用升级
- 注意它是直接依赖还是传递依赖

如果没有漏洞，用 [SILENT] 响应。" \
  --name "依赖审计" \
  --deliver telegram
```

---

## DevOps & 监控

### 部署验证

在每次部署后触发冒烟测试。您的 CI/CD 管道在部署完成时向 webhook POST。

**触发器：** API 调用 (webhook)

```bash
hermes webhook subscribe deploy-verify \
  --events "deployment" \
  --prompt "部署刚刚完成：
服务：{service}
环境：{environment}
版本：{version}
部署者：{deployer}

运行这些验证步骤：
1. 检查服务是否响应：curl -s -o /dev/null -w '%{http_code}' {health_url}
2. 搜索最近的日志以查找错误：检查部署负载中是否有任何错误指示符
3. 验证版本匹配：curl -s {health_url}/version

报告：部署状态（健康/降级/失败）、响应时间、发现的任何错误。
如果健康，请保持简短。如果降级或失败，请提供详细诊断。" \
  --deliver telegram
```

您的 CI/CD 管道触发它：

```bash
curl -X POST http://your-server:8644/webhooks/deploy-verify \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$(echo -n '{"service":"api","environment":"prod","version":"2.1.0","deployer":"ci","health_url":"https://api.example.com/health"}' | openssl dgst -sha256 -hmac 'your-secret' | cut -d' ' -f2)" \
  -d '{"service":"api","environment":"prod","version":"2.1.0","deployer":"ci","health_url":"https://api.example.com/health"}'
```

### 警报分类

将监控警报与最近的更改相关联，以起草响应。适用于 Datadog、PagerDuty、Grafana 或任何可以 POST JSON 的警报系统。

**触发器：** API 调用 (webhook)

```bash
hermes webhook subscribe alert-triage \
  --prompt "收到监控警报：
警报：{alert.name}
严重性：{alert.severity}
服务：{alert.service}
消息：{alert.message}
时间戳：{alert.timestamp}

调查：
1. 搜索网络以查找此错误模式的已知问题
2. 检查这是否与最近的部署或配置更改相关
3. 起草分类摘要，包括：
   - 可能的根本原因
   - 建议的第一响应步骤
   - 升级建议（P1-P4）

保持简洁。这将发送到值班频道。" \
  --deliver slack
```

### 正常运行时间监控

每 30 分钟检查端点。仅在出现问题时通知。

**触发器：** 定时（每 30 分钟）

```python title="~/.hermes/scripts/check-uptime.py"
import urllib.request, json, time

ENDPOINTS = [
    {"name": "API", "url": "https://api.example.com/health"},
    {"name": "Web", "url": "https://www.example.com"},
    {"name": "Docs", "url": "https://docs.example.com"},
]

results = []
for ep in ENDPOINTS:
    try:
        start = time.time()
        req = urllib.request.Request(ep["url"], headers={"User-Agent": "Hermes-Monitor/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        elapsed = round((time.time() - start) * 1000)
        results.append({"name": ep["name"], "status": resp.getcode(), "ms": elapsed})
    except Exception as e:
        results.append({"name": ep["name"], "status": "DOWN", "error": str(e)})

down = [r for r in results if r.get("status") == "DOWN" or (isinstance(r.get("status"), int) and r["status"] >= 500)]
if down:
    print("OUTAGE DETECTED")
    for r in down:
        print(f"  {r['name']}: {r.get('error', f'HTTP {r[\"status\"]}')} ")
    print(f"\nAll results: {json.dumps(results, indent=2)}")
else:
    print("NO_ISSUES")
```

```bash
hermes cron create "every 30m" \
  "如果脚本报告 OUTAGE DETECTED，总结哪些服务已关闭并建议可能的原因。如果 NO_ISSUES，用 [SILENT] 响应。" \
  --script ~/.hermes/scripts/check-uptime.py \
  --name "正常运行时间监控" \
  --deliver telegram
```

---

## 研究与智能

### 竞争对手仓库侦察

监控竞争对手仓库以查找有趣的 PR、功能和架构决策。

**触发器：** 定时（每日）

```bash
hermes cron create "0 8 * * *" \
  "侦察这些 AI 智能体仓库在过去 24 小时内的显著活动：

要检查的仓库：
- anthropics/claude-code
- openai/codex
- All-Hands-AI/OpenHands
- Aider-AI/aider

对于每个仓库：
1. gh pr list --repo <repo> --state all --json number,title,author,createdAt,mergedAt --limit 15
2. gh issue list --repo <repo> --state open --json number,title,labels,createdAt --limit 10

重点关注：
- 正在开发的新功能
- 架构更改
- 我们可以学习的集成模式
- 可能影响我们的安全修复

跳过常规依赖升级和 CI 修复。如果没有显著内容，用 [SILENT] 响应。
如果有发现，请按仓库组织，并对每个项目进行简要分析。" \
  --skills "competitive-pr-scout" \
  --name "竞争对手侦察" \
  --deliver telegram
```

### AI 新闻摘要

每周 AI/ML 发展的汇总。

**触发器：** 定时（每周）

```bash
hermes cron create "0 9 * * 1" \
  "生成涵盖过去 7 天的每周 AI 新闻摘要：

1. 搜索网络以查找主要的 AI 公告、模型发布和研究突破
2. 搜索 GitHub 上趋势中的 ML 仓库
3. 检查 arXiv 上关于语言模型和智能体的高引用论文

结构：
## 标题（3-5 个主要故事）
## 值得注意的论文（2-3 篇论文，附带一句话摘要）
## 开源（有趣的新仓库或主要发布）
## 行业动态（资金、收购、发布）

将每个项目保持在 1-2 句话。包含链接。总共不超过 600 字。" \
  --name "每周 AI 摘要" \
  --deliver telegram
```

### 带笔记的论文摘要

每日 arXiv 扫描，将摘要保存到您的笔记系统。

**触发器：** 定时（每日）

```bash
hermes cron create "0 8 * * *" \
  "搜索 arXiv 以查找过去一天中关于'语言模型推理'或'工具使用智能体'的 3 篇最有趣的论文。对于每篇论文，创建一个 Obsidian 笔记，包含标题、作者、摘要摘要、关键贡献以及对 Hermes Agent 开发的潜在相关性。" \
  --skills "arxiv,obsidian" \
  --name "论文摘要" \
  --deliver local
```

---

## GitHub 事件自动化

### 问题自动标记

自动标记并响应新问题。

**触发器：** GitHub webhook

```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "收到新的 GitHub 问题：
仓库：{repository.full_name}
问题 #{issue.number}：{issue.title}
作者：{issue.user.login}
操作：{action}
正文：{issue.body}
标签：{issue.labels}

如果这是一个新问题（action=opened）：
1. 仔细阅读问题标题和正文
2. 建议适当的标签（bug、feature、docs、security、question）
3. 如果是错误报告，检查您是否可以从描述中识别受影响的组件
4. 发布有帮助的初始响应以确认问题

如果这是标签或分配更改，用 [SILENT] 响应。" \
  --deliver github_comment
```

### CI 失败分析

分析 CI 失败并在 PR 上发布诊断。

**触发器：** GitHub webhook

```yaml
# config.yaml 路由
platforms:
  webhook:
    enabled: true
    extra:
      routes:
        ci-failure:
          events: ["check_run"]
          secret: "ci-secret"
          prompt: |
            CI 检查失败：
            仓库：{repository.full_name}
            检查：{check_run.name}
            状态：{check_run.conclusion}
            PR：#{check_run.pull_requests.0.number}
            详细信息 URL：{check_run.details_url}

            如果结论是"failure"：
            1. 如果可访问，从详细信息 URL 获取日志
            2. 识别可能的失败原因
            3. 建议修复方法
            如果结论是"success"，用 [SILENT] 响应。
          deliver: "github_comment"
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{check_run.pull_requests.0.number}"
```

### 跨仓库自动移植更改

当一个 PR 在一个仓库中合并时，自动将等效更改移植到另一个仓库。

**触发器：** GitHub webhook

```bash
hermes webhook subscribe auto-port \
  --events "pull_request" \
  --prompt "PR 在源仓库中合并：
仓库：{repository.full_name}
PR #{pull_request.number}：{pull_request.title}
作者：{pull_request.user.login}
操作：{action}
合并提交：{pull_request.merge_commit_sha}

如果操作是 'closed' 且 pull_request.merged 为 true：
1. 获取差异：curl -sL {pull_request.diff_url}
2. 分析更改了什么
3. 确定此更改是否需要移植到 Go SDK 等效项
4. 如果是，创建分支，应用等效更改，并在目标仓库上打开 PR
5. 在新 PR 描述中引用原始 PR

如果操作不是 'closed' 或未合并，用 [SILENT] 响应。" \
  --skills "github-pr-workflow" \
  --deliver log
```

---

## 业务运营

### Stripe 支付监控

跟踪支付事件并获取失败摘要。

**触发器：** API 调用 (webhook)

```bash
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed,charge.dispute.created" \
  --prompt "收到 Stripe 事件：
事件类型：{type}
金额：{data.object.amount} 分（{data.object.currency}）
客户：{data.object.customer}
状态：{data.object.status}

对于 payment_intent.payment_failed：
- 从 {data.object.last_payment_error} 识别失败原因
- 建议这是临时问题（重试）还是永久问题（联系客户）

对于 charge.dispute.created：
- 标记为紧急
- 总结争议详情

对于 payment_intent.succeeded：
- 仅简要确认

为运营频道保持响应简洁。" \
  --deliver slack
```

### 每日收入摘要

每天早上编译关键业务指标。

**触发器：** 定时（每日）

```bash
hermes cron create "0 8 * * *" \
  "生成早间业务指标摘要。

搜索网络以查找：
1. 当前比特币和以太坊价格
2. 标准普尔 500 指数状态（盘前或前收盘）
3. 过去 12 小时内任何主要科技/AI 行业新闻

格式为简短的早间简报，最多 3-4 个要点。
作为干净、可扫描的消息交付。" \
  --name "早间简报" \
  --deliver telegram
```

---

## 多技能工作流

### 安全审计管道

结合多个技能进行全面的每周安全审查。

**触发器：** 定时（每周）

```bash
hermes cron create "0 3 * * 0" \
  "对 hermes-agent 代码库进行全面安全审计。

1. 检查依赖漏洞（pip audit、npm audit）
2. 搜索代码库以查找常见安全反模式：
   - 硬编码的密钥或 API 密钥
   - SQL 注入向量（查询中的字符串格式化）
   - 路径遍历风险（文件路径中的用户输入未经验证）
   - 不安全的反序列化（pickle.loads、不带 SafeLoader 的 yaml.load）
3. 审查最近的提交（过去 7 天）以查找安全相关更改
4. 检查是否添加了任何新的环境变量而未记录

编写安全报告，按严重性（关键、高、中、低）分类发现。
如果未发现任何内容，报告健康状况良好。" \
  --skills "codebase-security-audit" \
  --name "每周安全审计" \
  --deliver telegram
```

### 内容管道

按计划研究、起草和准备内容。

**触发器：** 定时（每周）

```bash
hermes cron create "0 10 * * 3" \
  "研究并起草关于 AI 智能体中热门主题的技术博客文章大纲。

1. 搜索网络以查找本周讨论最多的 AI 智能体主题
2. 选择与开源 AI 智能体相关的最有趣的一个
3. 创建大纲，包括：
   - 钩子/介绍角度
   - 3-4 个关键部分
   - 适合开发人员的技术深度
   - 带有可操作要点的结论
4. 将大纲保存到 ~/drafts/blog-$(date +%Y%m%d).md

将大纲保持在约 300 字。这是一个起点，而不是完成的帖子。" \
  --name "博客大纲" \
  --deliver local
```

---

## 快速参考

### Cron 计划语法

| 表达式 | 含义 |
|-----------|---------|
| `every 30m` | 每 30 分钟 |
| `every 2h` | 每 2 小时 |
| `0 2 * * *` | 每天凌晨 2:00 |
| `0 9 * * 1` | 每周一上午 9:00 |
| `0 9 * * 1-5` | 工作日上午 9:00 |
| `0 3 * * 0` | 每周日凌晨 3:00 |
| `0 */6 * * *` | 每 6 小时 |

### 交付目标

| 目标 | 标志 | 说明 |
|--------|------|-------|
| 同一聊天 | `--deliver origin` | 默认 — 交付到创建作业的位置 |
| 本地文件 | `--deliver local` | 保存输出，无通知 |
| Telegram | `--deliver telegram` | 家庭频道，或 `telegram:CHAT_ID` 用于特定频道 |
| Discord | `--deliver discord` | 家庭频道，或 `discord:CHANNEL_ID` |
| Slack | `--deliver slack` | 家庭频道 |
| SMS | `--deliver sms:+15551234567` | 直接到电话号码 |
| 特定线程 | `--deliver telegram:-100123:456` | Telegram 论坛主题 |

### Webhook 模板变量

| 变量 | 说明 |
|----------|-------------|
| `{pull_request.title}` | PR 标题 |
| `{issue.number}` | 问题编号 |
| `{repository.full_name}` | `owner/repo` |
| `{action}` | 事件操作（opened、closed 等） |
| `{__raw__}` | 完整 JSON 负载（在 4000 字符处截断） |
| `{sender.login}` | 触发事件的 GitHub 用户 |

### [SILENT] 模式

当 cron 作业的响应包含 `[SILENT]` 时，交付被抑制。使用此模式可以在安静运行时避免通知垃圾邮件：

```
如果没有发生值得注意的事情，用 [SILENT] 响应。
```

这意味着您仅在智能体有内容要报告时才会收到通知。