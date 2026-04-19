# Hermes Agent v0.6.0 (v2026.3.30)

**发布日期:** 2026年3月30日

> 多实例发布 — 用于运行隔离智能体实例的配置文件、MCP服务器模式、Docker容器、回退提供商链、两个新的消息平台（飞书/Lark和企业微信）、Telegram webhook模式、Slack多工作区OAuth，2天内完成95个PR和16个已解决问题。

---

## ✨ 亮点

- **配置文件 — 多实例Hermes** — 从同一安装运行多个隔离的Hermes实例。每个配置文件都有自己的配置、内存、会话、技能和网关服务。使用`hermes profile create`创建，使用`hermes -p <name>`切换，导出/导入以共享。完全的令牌锁定隔离防止两个配置文件使用相同的机器人凭证。([#3681](https://github.com/NousResearch/hermes-agent/pull/3681))

- **MCP服务器模式** — 通过`hermes mcp serve`将Hermes对话和会话暴露给任何MCP兼容客户端（Claude Desktop、Cursor、VS Code等）。浏览对话、阅读消息、跨会话搜索和管理附件 — 所有这些都通过Model Context Protocol。支持标准输入输出和Streamable HTTP传输。([#3795](https://github.com/NousResearch/hermes-agent/pull/3795))

- **Docker容器** — 用于在容器中运行Hermes Agent的官方Dockerfile。支持带有卷挂载配置的CLI和网关模式。([#3668](https://github.com/NousResearch/hermes-agent/pull/3668), 关闭 [#850](https://github.com/NousResearch/hermes-agent/issues/850))

- **有序回退提供商链** — 配置多个推理提供商并自动故障转移。当您的主要提供商返回错误或无法访问时，Hermes会自动尝试链中的下一个提供商。通过config.yaml中的`fallback_providers`配置。([#3813](https://github.com/NousResearch/hermes-agent/pull/3813), 关闭 [#1734](https://github.com/NousResearch/hermes-agent/issues/1734))

- **飞书/Lark平台支持** — 飞书和Lark的完整网关适配器，带有事件订阅、消息卡片、群聊、图像/文件附件和交互式卡片回调。([#3799](https://github.com/NousResearch/hermes-agent/pull/3799), [#3817](https://github.com/NousResearch/hermes-agent/pull/3817), 关闭 [#1788](https://github.com/NousResearch/hermes-agent/issues/1788))

- **企业微信平台支持** — 企业微信的新网关适配器，支持文本/图像/语音消息、群聊和回调验证。([#3847](https://github.com/NousResearch/hermes-agent/pull/3847))

- **Slack多工作区OAuth** — 通过OAuth令牌文件将单个Hermes网关连接到多个Slack工作区。每个工作区都有自己的机器人令牌，根据传入事件动态解析。([#3903](https://github.com/NousResearch/hermes-agent/pull/3903))

- **Telegram Webhook模式和群组控制** — 以webhook模式运行Telegram适配器，作为轮询的替代方案 — 更快的响应时间，更适合反向代理后面的生产部署。新的群组提及控制，控制机器人何时响应：始终、仅当@提及时，或通过正则表达式触发器。([#3880](https://github.com/NousResearch/hermes-agent/pull/3880), [#3870](https://github.com/NousResearch/hermes-agent/pull/3870))

- **Exa搜索后端** — 添加Exa作为Firecrawl和DuckDuckGo之外的替代网络搜索和内容提取后端。设置`EXA_API_KEY`并将其配置为首选后端。([#3648](https://github.com/NousResearch/hermes-agent/pull/3648))

- **远程后端上的技能和凭证** — 将技能目录和凭证文件挂载到Modal和Docker容器中，使远程终端会话能够访问与本地执行相同的技能和密钥。([#3890](https://github.com/NousResearch/hermes-agent/pull/3890), [#3671](https://github.com/NousResearch/hermes-agent/pull/3671), 关闭 [#3665](https://github.com/NousResearch/hermes-agent/issues/3665), [#3433](https://github.com/NousResearch/hermes-agent/issues/3433))

---

## 🏗️ 核心智能体与架构

### 提供商与模型支持
- **有序回退提供商链** — 多个配置提供商之间的自动故障转移 ([#3813](https://github.com/NousResearch/hermes-agent/pull/3813))
- **修复提供商切换时的api_mode** — 通过`hermes model`切换提供商现在正确清除过时的`api_mode`，而不是硬编码`chat_completions`，修复了具有Anthropic兼容端点的提供商的404错误 ([#3726](https://github.com/NousResearch/hermes-agent/pull/3726), [#3857](https://github.com/NousResearch/hermes-agent/pull/3857), 关闭 [#3685](https://github.com/NousResearch/hermes-agent/issues/3685))
- **停止静默OpenRouter回退** — 当未配置提供商时，Hermes现在会引发明确的错误，而不是静默路由到OpenRouter ([#3807](https://github.com/NousResearch/hermes-agent/pull/3807), [#3862](https://github.com/NousResearch/hermes-agent/pull/3862))
- **Gemini 3.1预览模型** — 添加到OpenRouter和Nous Portal目录 ([#3803](https://github.com/NousResearch/hermes-agent/pull/3803), 关闭 [#3753](https://github.com/NousResearch/hermes-agent/issues/3753))
- **Gemini直接API上下文长度** — 直接Google AI端点的完整上下文长度解析 ([#3876](https://github.com/NousResearch/hermes-agent/pull/3876))
- **gpt-5.4-mini** 添加到Codex回退目录 ([#3855](https://github.com/NousResearch/hermes-agent/pull/3855))
- **首选精选模型列表** 当API探测返回较少模型时，优先于实时API探测 ([#3856](https://github.com/NousResearch/hermes-agent/pull/3856), [#3867](https://github.com/NousResearch/hermes-agent/pull/3867))
- **用户友好的429速率限制消息** 带有Retry-After倒计时 ([#3809](https://github.com/NousResearch/hermes-agent/pull/3809))
- **辅助客户端占位符密钥** 用于没有认证要求的本地服务器 ([#3842](https://github.com/NousResearch/hermes-agent/pull/3842))
- **INFO级日志** 用于辅助提供商解析 ([#3866](https://github.com/NousResearch/hermes-agent/pull/3866))

### 智能体循环与对话
- **子智能体状态报告** — 当摘要存在时报告`completed`状态，而不是通用失败 ([#3829](https://github.com/NousResearch/hermes-agent/pull/3829))
- **压缩期间更新会话日志文件** — 防止上下文压缩后出现过时的文件引用 ([#3835](https://github.com/NousResearch/hermes-agent/pull/3835))
- **省略空工具参数** — 为空时不发送`tools`参数，而不是`None`，修复与严格提供商的兼容性 ([#3820](https://github.com/NousResearch/hermes-agent/pull/3820))