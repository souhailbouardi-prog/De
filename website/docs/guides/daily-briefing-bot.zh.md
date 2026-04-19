---
sidebar_position: 3
title: "教程：每日简报机器人"
description: "构建一个自动化的每日简报机器人，研究主题、总结发现并每天早上将其发送到Telegram或Discord"
---

# 教程：构建每日简报机器人

在本教程中，您将构建一个个人简报机器人，它每天早上醒来，研究您关心的主题，总结发现，并将简洁的简报直接发送到您的Telegram或Discord。

完成后，您将拥有一个结合**网络搜索**、**cron调度**、**委托**和**消息传递**的完全自动化工作流 — 无需代码。

## 我们正在构建什么

流程如下：

1. **早上8:00** — cron调度器触发您的作业
2. **Hermes启动**一个带有您提示的新代理会话
3. **网络搜索**获取关于您主题的最新新闻
4. **总结**将其提炼为干净的简报格式
5. **传递**将简报发送到您的Telegram或Discord

整个过程无需人工干预。您只需在早上喝咖啡时阅读简报。

## 先决条件

开始之前，请确保您有：

- **已安装Hermes Agent** — 请参阅[安装指南](/docs/getting-started/installation)
- **网关运行中** — 网关守护进程处理cron执行：
  ```bash
  hermes gateway install   # 作为用户服务安装
  sudo hermes gateway install --system   # Linux服务器：启动时系统服务
  # 或
  hermes gateway           # 在前台运行
  ```
- **Firecrawl API密钥** — 在环境中设置`FIRECRAWL_API_KEY`用于网络搜索
- **已配置消息传递**（可选但推荐）— [Telegram](/docs/user-guide/messaging/telegram)或Discord设置了主频道

:::tip 没有消息传递？没问题
您仍然可以使用`deliver: "local"`跟随本教程。简报将保存到`~/.hermes/cron/output/`，您可以随时阅读。
:::

## 步骤1：手动测试工作流

在自动化任何内容之前，让我们确保简报正常工作。启动聊天会话：

```bash
hermes
```

然后输入此提示：

```
搜索有关AI代理和开源LLM的最新新闻。
以简洁的简报格式总结前3个故事，包含链接。
```

Hermes将搜索网络，阅读结果，并生成类似以下内容：

```
☀️ 您的AI简报 — 2026年3月8日

1. Qwen 3发布，参数达235B
   阿里巴巴最新的开放权重模型在多个基准测试中与GPT-4.5匹配，同时保持完全开源。
   → https://qwenlm.github.io/blog/qwen3/

2. LangChain推出Agent Protocol标准
   一个新的代理到代理通信开放标准在第一周就获得了15个主要框架的采用。
   → https://blog.langchain.dev/agent-protocol/

3. EU AI Act开始对通用模型执行
   第一个合规截止日期到来，开源模型在10M参数阈值下获得豁免。
   → https://artificialintelligenceact.eu/updates/

---
3个故事 • 搜索来源：8个 • 由Hermes Agent生成
```

如果这有效，您就可以自动化它了。

:::tip 迭代格式
尝试不同的提示，直到获得您喜欢的输出。添加像"使用emoji标题"或"每个摘要保持在2句话以内"这样的指令。您最终确定的任何内容都将进入cron作业。
:::

## 步骤2：创建Cron作业

现在让我们安排这个每天早上自动运行。您可以通过两种方式做到这一点。

### 选项A：自然语言（在聊天中）

只需告诉Hermes您想要什么：

```
每天早上8点，搜索有关AI代理和开源LLM的最新新闻。
以简洁的简报格式总结前3个故事，包含链接。
使用友好、专业的语气。传递到telegram。
```

Hermes将使用统一的`cronjob`工具为您创建cron作业。

### 选项B：CLI斜杠命令

使用`/cron`命令获得更多控制：

```
/cron add "0 8 * * *" "Search the web for the latest news about AI agents and open source LLMs. Find at least 5 recent articles from the past 24 hours. Summarize the top 3 most important stories in a concise daily briefing format. For each story include: a clear headline, a 2-sentence summary, and the source URL. Use a friendly, professional tone. Format with emoji bullet points and end with a total story count."
```

### 黄金规则：自包含提示

:::warning 关键概念
Cron作业在**完全新鲜的会话**中运行 — 没有您以前对话的记忆，也没有关于您"之前设置"的上下文。您的提示必须包含**代理完成工作所需的一切**。
:::

**不良提示：**
```
做我通常的晨间简报。
```

**良好提示：**
```
搜索有关AI代理和开源LLM的最新新闻。
从过去24小时内找到至少5篇最近的文章。
以简洁的每日简报格式总结前3个最重要的故事。
每个故事包括：清晰的标题、2句话的摘要和源URL。
使用友好、专业的语气。
使用emoji项目符号格式。
```

良好的提示具体说明了**搜索什么**、**多少文章**、**什么格式**和**什么语气**。它一次性包含了代理所需的一切。

## 步骤3：自定义简报

一旦基本简报工作正常，您就可以发挥创意了。

### 多主题简报

在一个简报中涵盖多个领域：

```
/cron add "0 8 * * *" "创建涵盖三个主题的晨间简报。对于每个主题，搜索过去24小时的最新新闻，并总结前2个故事，包含链接。

主题：
1. AI和机器学习 — 关注开源模型和代理框架
2. 加密货币 — 关注比特币、以太坊和监管新闻
3. 太空探索 — 关注SpaceX、NASA和商业太空

格式为干净的简报，带有章节标题和emoji。以今天的日期和一句励志名言结束。"
```

### 使用委托进行并行研究

为了更快地获得简报，告诉Hermes将每个主题委托给子代理：

```
/cron add "0 8 * * *" "通过将研究委托给子代理来创建晨间简报。委托三个并行任务：

1. 委托：搜索过去24小时内的前2个AI/ML新闻故事，包含链接
2. 委托：搜索过去24小时内的前2个加密货币新闻故事，包含链接
3. 委托：搜索过去24小时内的前2个太空探索新闻故事，包含链接

收集所有结果并将它们组合成一个单一的干净简报，带有章节标题、emoji格式和源链接。将今天的日期作为标题添加。"
```

每个子代理独立并行搜索，然后主代理将所有内容组合成一个精心制作的简报。有关此工作原理的更多信息，请参阅[委托文档](/docs/user-guide/features/delegation)。

### 仅工作日调度

周末不需要简报？使用针对周一至周五的cron表达式：

```
/cron add "0 8 * * 1-5" "搜索最新的AI和科技新闻..."
```

### 每日两次简报

获取早晨概览和晚间回顾：

```
/cron add "0 8 * * *" "晨间简报：搜索过去12小时的AI新闻..."
/cron add "0 18 * * *" "晚间回顾：搜索过去12小时的AI新闻..."
```

### 使用内存添加个人上下文

如果您启用了[内存](/docs/user-guide/features/memory)，您可以存储跨会话持久的偏好。但请记住 — cron作业在没有对话记忆的新会话中运行。要添加个人上下文，请直接将其烘焙到提示中：

```
/cron add "0 8 * * *" "您正在为一位关心以下内容的高级ML工程师创建简报：PyTorch生态系统、Transformer架构、开放权重模型和欧盟的AI监管。跳过关于产品发布或融资轮次的故事，除非它们涉及开源。

搜索这些主题的最新新闻。总结前3个故事，包含链接。保持简洁和技术性 — 这位读者不需要基本解释。"
```

:::tip 定制角色
包含关于简报是**为谁**准备的详细信息会显著提高相关性。告诉代理您的角色、兴趣和要跳过的内容。
:::

## 步骤4：管理您的作业

### 列出所有计划作业

在聊天中：
```
/cron list
```

或从终端：
```bash
hermes cron list
```

您将看到类似以下的输出：

```
ID          | Name              | Schedule    | Next Run           | Deliver
------------|-------------------|-------------|--------------------|--------
a1b2c3d4    | Morning Briefing  | 0 8 * * *   | 2026-03-09 08:00   | telegram
e5f6g7h8    | Evening Recap     | 0 18 * * *  | 2026-03-08 18:00   | telegram
```

### 移除作业

在聊天中：
```
/cron remove a1b2c3d4
```

或对话式询问：
```
移除我的晨间简报cron作业。
```

Hermes将使用`cronjob(action="list")`找到它，并使用`cronjob(action="remove")`删除它。

### 检查网关状态

确保调度器实际运行：

```bash
hermes cron status
```

如果网关未运行，您的作业将不会执行。将其安装为后台服务以提高可靠性：

```bash
hermes gateway install
# 或在Linux服务器上
sudo hermes gateway install --system
```

## 更进一步

您已经构建了一个工作的每日简报机器人。以下是一些可以探索的方向：

- **[计划任务（Cron）](/docs/user-guide/features/cron)** — 完整参考，包括调度格式、重复限制和传递选项
- **[委托](/docs/user-guide/features/delegation)** — 深入了解并行子代理工作流
- **[消息平台](/docs/user-guide/messaging)** — 设置Telegram、Discord或其他传递目标
- **[内存](/docs/user-guide/features/memory)** — 跨会话的持久上下文
- **[提示与最佳实践](/docs/guides/tips)** — 更多提示工程建议

:::tip 您还可以调度什么？
简报机器人模式适用于任何事情：竞争对手监控、GitHub仓库摘要、天气预报、投资组合跟踪、服务器健康检查，甚至每日笑话。如果您可以在提示中描述它，您就可以调度它。
:::