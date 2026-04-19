# Hermes Agent v0.9.0 (v2026.4.13)

**发布日期:** 2026年4月13日
**自v0.8.0以来:** 487个提交 · 269个合并PR · 167个已解决问题 · 493个文件更改 · 63,281个插入 · 24个贡献者

> 无处不在的发布 — Hermes通过Termux/Android进入移动领域，添加iMessage和微信，为OpenAI和Anthropic推出快速模式，引入后台进程监控，启动本地Web仪表板来管理您的智能体，并在16个支持的平台上提供迄今为止最深度的安全加固。

---

## ✨ 亮点

- **本地Web仪表板** — 一个新的基于浏览器的仪表板，用于在本地管理您的Hermes Agent。配置设置、监控会话、浏览技能和管理您的网关 — 所有这些都从干净的Web界面完成，无需触摸配置文件或终端。开始使用Hermes的最简单方法。

- **快速模式 (`/fast`)** — OpenAI和Anthropic模型的优先处理。切换`/fast`以通过优先队列路由，在支持的模型（GPT-5.4、Codex、Claude）上显著降低延迟。扩展到所有OpenAI优先处理模型和Anthropic的快速层级。([#6875](https://github.com/NousResearch/hermes-agent/pull/6875), [#6960](https://github.com/NousResearch/hermes-agent/pull/6960), [#7037](https://github.com/NousResearch/hermes-agent/pull/7037))

- **通过BlueBubbles实现iMessage** — 通过BlueBubbles的完整iMessage集成，将Hermes带入Apple的消息生态系统。自动webhook注册、设置向导集成和崩溃恢复能力。([#6437](https://github.com/NousResearch/hermes-agent/pull/6437), [#6460](https://github.com/NousResearch/hermes-agent/pull/6460), [#6494](https://github.com/NousResearch/hermes-agent/pull/6494))

- **微信（Weixin）和企业微信回调模式** — 通过iLink Bot API的原生微信支持和用于自建企业应用的新企业微信回调模式适配器。流式光标、媒体上传、Markdown链接处理和原子状态持久化。Hermes现在端到端覆盖中国消息生态系统。([#7166](https://github.com/NousResearch/hermes-agent/pull/7166), [#7943](https://github.com/NousResearch/hermes-agent/pull/7943))

- **Termux / Android支持** — 通过Termux在Android上原生运行Hermes。适应的安装路径、针对移动屏幕的TUI优化、语音后端支持，以及`/image`命令在设备上工作。([#6834](https://github.com/NousResearch/hermes-agent/pull/6834))

- **后台进程监控 (`watch_patterns`)** — 设置模式以在后台进程输出中监视，并在它们匹配时实时收到通知。监控错误、等待特定事件（"listening on port"）或监视构建日志 — 所有这些都无需轮询。([#7635](https://github.com/NousResearch/hermes-agent/pull/7635))

- **原生xAI和小米MiMo提供商** — xAI（Grok）和小米MiMo的一流提供商支持，具有直接API访问、模型目录和设置向导集成。加上带有门户请求支持的Qwen OAuth。([#7372](https://github.com/NousResearch/hermes-agent/pull/7372), [#7855](https://github.com/NousResearch/hermes-agent/pull/7855))

- **可插拔上下文引擎** — 上下文管理现在是通过`hermes plugins`的可插拔插槽。替换控制智能体每回合看到内容的自定义上下文引擎 — 过滤、摘要或特定领域的上下文注入。([#7464](https://github.com/NousResearch/hermes-agent/pull/7464))

- **统一代理支持** — SOCKS代理、`DISCORD_PROXY`和跨所有网关平台的系统代理自动检测。企业防火墙后面的Hermes可以正常工作。([#6814](https://github.com/NousResearch/hermes-agent/pull/6814))

- **全面的安全加固** — 检查点管理器中的路径遍历保护、沙箱写入中的shell注入中和、Slack图像上传中的SSRF重定向防护、Twilio webhook签名验证（SMS RCE修复）、API服务器认证强制执行、git参数注入预防和审批按钮授权。([#7933](https://github.com/NousResearch/hermes-agent/pull/7933), [#7944](https://github.com/NousResearch/hermes-agent/pull/7944), [#7940](https://github.com/NousResearch/hermes-agent/pull/7940), [#7151](https://github.com/NousResearch/hermes-agent/pull/7151), [#7156](https://github.com/NousResearch/hermes-agent/pull/7156))

- **`hermes backup`和`hermes import`** — 完整备份和恢复您的Hermes配置、会话、技能和内存。在机器之间迁移或在重大更改前创建快照。([#7997](https://github.com/NousResearch/hermes-agent/pull/7997))

- **16个支持的平台** — 随着BlueBubbles（iMessage）和微信加入Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Email、SMS、钉钉、飞书、企业微信、Mattermost、Home Assistant和Webhooks，Hermes现在开箱即用地运行在16个消息平台上。

- **`/debug`和`hermes debug share`** — 新的调试工具包：跨所有平台的`/debug`斜杠命令用于快速诊断，以及`hermes debug share`用于上传完整的调试报告到pastebin，以便在故障排除时轻松共享。([#8681](https://github.com/NousResearch/hermes-agent/pull/8681))

---

## 🏗️ 核心智能体与架构

### 提供商与模型支持
- **原生xAI（Grok）提供商** 具有直接API访问和模型目录 ([#7372](https://github.com/NousResearch/hermes-agent/pull/7372))
- **小米MiMo作为一流提供商** — 设置向导、模型目录、空响应恢复 ([#7855](https://github.com/NousResearch/hermes-agent/pull/7855))
- **Qwen OAuth提供商** 带有门户请求支持 ([#6282](https://github.com/NousResearch/hermes-agent/pull/6282))
- **快速模式** — `/fast`切换用于OpenAI优先处理 + Anthropic快速层级 ([#6875](https://github.com/NousResearch/hermes-agent/pull/6875), [#6960](https://github.com/NousResearch/hermes-agent/pull/6960), [#7037](https://github.com/NousResearch/hermes-agent/pull/7037))
- **结构化API错误分类** 用于智能故障转移决策 ([#6514](https://github.com/NousResearch/hermes-agent/pull/6514))
- **速率限制标头捕获** 在`/usage`中显示 ([#6541](https://github.com/NousResearch/hermes-agent/pull/6541))
- **API服务器模型名称** 从配置文件名称派生 ([#6857](https://github.com/NousResearch/hermes-agent/pull/6857))
- **自定义提供商** 现在包含在`/model`列表和解析中 ([#7088](https://github.com/NousResearch/hermes-agent/pull/7088))