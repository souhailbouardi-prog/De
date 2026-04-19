# Hermes Agent v0.4.0 (v2026.3.23)

**发布日期:** 2026年3月23日

> 平台扩展发布 — OpenAI兼容的API服务器、6个新的消息适配器、4个新的推理提供商、带有OAuth 2.1的MCP服务器管理、@上下文引用、网关提示缓存、默认启用流式传输，以及包含200+错误修复的全面可靠性改进。

---

## ✨ 亮点

- **OpenAI兼容的API服务器** — 将Hermes暴露为`/v1/chat/completions`端点，带有新的`/api/jobs` REST API用于cron作业管理，通过输入限制、字段白名单、SQLite支持的响应持久化和CORS源保护进行加固 ([#1756](https://github.com/NousResearch/hermes-agent/pull/1756), [#2450](https://github.com/NousResearch/hermes-agent/pull/2450), [#2456](https://github.com/NousResearch/hermes-agent/pull/2456), [#2451](https://github.com/NousResearch/hermes-agent/pull/2451), [#2472](https://github.com/NousResearch/hermes-agent/pull/2472))

- **6个新的消息平台适配器** — Signal、钉钉、SMS（Twilio）、Mattermost、Matrix和Webhook适配器加入Telegram、Discord和WhatsApp。网关使用指数退避自动重新连接失败的平台 ([#2206](https://github.com/NousResearch/hermes-agent/pull/2206), [#1685](https://github.com/NousResearch/hermes-agent/pull/1685), [#1688](https://github.com/NousResearch/hermes-agent/pull/1688), [#1683](https://github.com/NousResearch/hermes-agent/pull/1683), [#2166](https://github.com/NousResearch/hermes-agent/pull/2166), [#2584](https://github.com/NousResearch/hermes-agent/pull/2584))

- **@ 上下文引用** — Claude Code风格的`@file`和`@url`上下文注入，在CLI中支持制表符补全 ([#2343](https://github.com/NousResearch/hermes-agent/pull/2343), [#2482](https://github.com/NousResearch/hermes-agent/pull/2482))

- **4个新的推理提供商** — GitHub Copilot（OAuth + 令牌验证）、阿里云/DashScope、Kilo Code和OpenCode Zen/Go ([#1924](https://github.com/NousResearch/hermes-agent/pull/1924), [#1879](https://github.com/NousResearch/hermes-agent/pull/1879) 由@mchzimm提供, [#1673](https://github.com/NousResearch/hermes-agent/pull/1673), [#1666](https://github.com/NousResearch/hermes-agent/pull/1666), [#1650](https://github.com/NousResearch/hermes-agent/pull/1650))

- **MCP服务器管理CLI** — `hermes mcp`命令用于安装、配置和认证MCP服务器，支持完整的OAuth 2.1 PKCE流程 ([#2465](https://github.com/NousResearch/hermes-agent/pull/2465))

- **网关提示缓存** — 每个会话缓存AIAgent实例，在回合之间保留Anthropic提示缓存，大幅减少长对话的成本 ([#2282](https://github.com/NousResearch/hermes-agent/pull/2282), [#2284](https://github.com/NousResearch/hermes-agent/pull/2284), [#2361](https://github.com/NousResearch/hermes-agent/pull/2361))

- **上下文压缩全面改革** — 结构化摘要与迭代更新、令牌预算尾部保护、可配置的摘要端点和回退模型支持 ([#2323](https://github.com/NousResearch/hermes-agent/pull/2323), [#1727](https://github.com/NousResearch/hermes-agent/pull/1727), [#2224](https://github.com/NousResearch/hermes-agent/pull/2224))

- **默认启用流式传输** — CLI默认启用流式传输，在流式传输模式下正确显示 spinner/工具进度，以及广泛的换行和连接修复 ([#2340](https://github.com/NousResearch/hermes-agent/pull/2340), [#2161](https://github.com/NousResearch/hermes-agent/pull/2161), [#2258](https://github.com/NousResearch/hermes-agent/pull/2258))

---

## 🖥️ CLI & 用户体验

### 新命令与交互
- **@ 上下文补全** — 可通过制表符补全的`@file`/`@url`引用，将文件内容或网页注入到对话中 ([#2482](https://github.com/NousResearch/hermes-agent/pull/2482), [#2343](https://github.com/NousResearch/hermes-agent/pull/2343))
- **`/statusbar`** — 切换持久配置栏，在提示中显示模型+提供商信息 ([#2240](https://github.com/NousResearch/hermes-agent/pull/2240), [#1917](https://github.com/NousResearch/hermes-agent/pull/1917))
- **`/queue`** — 在不中断当前运行的情况下为智能体排队提示 ([#2191](https://github.com/NousResearch/hermes-agent/pull/2191), [#2469](https://github.com/NousResearch/hermes-agent/pull/2469))
- **`/permission`** — 在会话期间动态切换审批模式 ([#2207](https://github.com/NousResearch/hermes-agent/pull/2207))
- **`/browser`** — 来自CLI的交互式浏览器会话 ([#2273](https://github.com/NousResearch/hermes-agent/pull/2273), [#1814](https://github.com/NousResearch/hermes-agent/pull/1814))
- **`/cost`** — 网关模式下的实时定价和使用跟踪 ([#2180](https://github.com/NousResearch/hermes-agent/pull/2180))
- **`/approve` 和 `/deny`** — 用显式命令替换网关中的纯文本审批 ([#2002](https://github.com/NousResearch/hermes-agent/pull/2002))

### 流式传输与显示
- CLI默认启用流式传输 ([#2340](https://github.com/NousResearch/hermes-agent/pull/2340))
- 在流式传输模式下显示spinner和工具进度 ([#2161](https://github.com/NousResearch/hermes-agent/pull/2161))
- 当`show_reasoning`启用时显示推理/思考块 ([#2118](https://github.com/NousResearch/hermes-agent/pull/2118))
- CLI和网关的上下文压力警告 ([#2159](https://github.com/NousResearch/hermes-agent/pull/2159))
- 修复：流式传输块在没有空白的情况下连接 ([#2258](https://github.com/NousResearch/hermes-agent/pull/2258))
- 修复：迭代边界换行防止流连接 ([#2413](https://github.com/NousResearch/hermes-agent/pull/2413))
- 修复：延迟流式传输换行以防止空行堆叠 ([#2473](https://github.com/NousResearch/hermes-agent/pull/2473))
- 修复：在非TTY环境中抑制spinner动画 ([#2216](https://github.com/NousResearch/hermes-agent/pull/2216))
- 修复：在API错误消息中显示提供商和端点 ([#2266](https://github.com/NousResearch/hermes-agent/pull/2266))
- 修复：解决状态打印中的乱码ANSI转义码 ([#2448](https://github.com/NousResearch/hermes-agent/pull/2448))