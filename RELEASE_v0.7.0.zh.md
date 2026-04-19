# Hermes Agent v0.7.0 (v2026.4.3)

**发布日期:** 2026年4月3日

> 弹性发布 — 可插拔内存提供商、凭证池轮换、Camofox反检测浏览器、内联差异预览、跨竞争条件和审批路由的网关加固，以及168个PR和46个已解决问题的深度安全修复。

---

## ✨ 亮点

- **可插拔内存提供商接口** — 内存现在是一个可扩展的插件系统。第三方内存后端（Honcho、向量存储、自定义数据库）实现简单的提供商ABC并通过插件系统注册。内置内存是默认提供商。Honcho集成恢复到完全对等作为参考插件，具有配置文件范围的主机/对等解析。([#4623](https://github.com/NousResearch/hermes-agent/pull/4623), [#4616](https://github.com/NousResearch/hermes-agent/pull/4616), [#4355](https://github.com/NousResearch/hermes-agent/pull/4355))

- **同提供商凭证池** — 为同一提供商配置多个API密钥并自动轮换。线程安全的`least_used`策略在密钥之间分配负载，401失败会触发自动轮换到下一个凭证。通过设置向导或`credential_pool`配置进行设置。([#4188](https://github.com/NousResearch/hermes-agent/pull/4188), [#4300](https://github.com/NousResearch/hermes-agent/pull/4300), [#4361](https://github.com/NousResearch/hermes-agent/pull/4361))

- **Camofox反检测浏览器后端** — 使用Camoufox进行隐身浏览的新本地浏览器后端。带有VNC URL发现的持久会话用于可视化调试，为本地后端配置的SSRF绕过，通过`hermes tools`自动安装。([#4008](https://github.com/NousResearch/hermes-agent/pull/4008), [#4419](https://github.com/NousResearch/hermes-agent/pull/4419), [#4292](https://github.com/NousResearch/hermes-agent/pull/4292))

- **内联差异预览** — 文件写入和补丁操作现在在工具活动馈送中显示内联差异，让您在智能体继续之前直观确认更改内容。([#4411](https://github.com/NousResearch/hermes-agent/pull/4411), [#4423](https://github.com/NousResearch/hermes-agent/pull/4423))

- **API服务器会话连续性和工具流式传输** — API服务器（Open WebUI集成）现在实时流式传输工具进度事件，并支持`X-Hermes-Session-Id`标头用于跨请求的持久会话。会话持久化到共享的SessionDB。([#4092](https://github.com/NousResearch/hermes-agent/pull/4092), [#4478](https://github.com/NousResearch/hermes-agent/pull/4478), [#4802](https://github.com/NousResearch/hermes-agent/pull/4802))

- **ACP: 客户端提供的MCP服务器** — 编辑器集成（VS Code、Zed、JetBrains）现在可以注册自己的MCP服务器，Hermes将其作为额外的智能体工具接收。编辑器的MCP生态系统直接流入智能体。([#4705](https://github.com/NousResearch/hermes-agent/pull/4705))

- **网关加固** — 跨竞争条件、照片媒体传递、 flood 控制、卡住的会话、审批路由和压缩死亡螺旋的主要稳定性改进。网关在生产中更加可靠。([#4727](https://github.com/NousResearch/hermes-agent/pull/4727), [#4750](https://github.com/NousResearch/hermes-agent/pull/4750), [#4798](https://github.com/NousResearch/hermes-agent/pull/4798), [#4557](https://github.com/NousResearch/hermes-agent/pull/4557))

- **安全：秘密泄露阻止** — 浏览器URL和LLM响应现在会扫描秘密模式，阻止通过URL编码、base64或提示注入的泄露尝试。凭证目录保护扩展到`.docker`、`.azure`、`.config/gh`。Execute_code沙箱输出被编辑。([#4483](https://github.com/NousResearch/hermes-agent/pull/4483), [#4360](https://github.com/NousResearch/hermes-agent/pull/4360), [#4305](https://github.com/NousResearch/hermes-agent/pull/4305), [#4327](https://github.com/NousResearch/hermes-agent/pull/4327))

---

## 🏗️ 核心智能体与架构

### 提供商与模型支持
- **同提供商凭证池** — 配置多个API密钥，具有自动`least_used`轮换和401故障转移 ([#4188](https://github.com/NousResearch/hermes-agent/pull/4188), [#4300](https://github.com/NousResearch/hermes-agent/pull/4300))
- **通过智能路由保留凭证池** — 池状态在回退提供商切换中幸存，并在429上延迟急切回退 ([#4361](https://github.com/NousResearch/hermes-agent/pull/4361))
- **每回合主运行时恢复** — 使用回退提供商后，智能体在下一回合自动恢复主提供商，同时进行传输恢复 ([#4624](https://github.com/NousResearch/hermes-agent/pull/4624))
- **GPT-5和Codex模型的`developer`角色** — 对较新模型使用OpenAI推荐的系统消息角色 ([#4498](https://github.com/NousResearch/hermes-agent/pull/4498))
- **Google模型操作指南** — Gemini和Gemma模型获得提供商特定的提示指导 ([#4641](https://github.com/NousResearch/hermes-agent/pull/4641))
- **Anthropic长上下文层级429处理** — 达到层级限制时自动将上下文减少到200k ([#4747](https://github.com/NousResearch/hermes-agent/pull/4747))
- **第三方Anthropic端点的基于URL的认证** + CI测试修复 ([#4148](https://github.com/NousResearch/hermes-agent/pull/4148))
- **MiniMax Anthropic端点的Bearer认证** ([#4028](https://github.com/NousResearch/hermes-agent/pull/4028))
- **Fireworks上下文长度检测** ([#4158](https://github.com/NousResearch/hermes-agent/pull/4158))
- **阿里巴巴提供商的标准DashScope国际端点** ([#4133](https://github.com/NousResearch/hermes-agent/pull/4133), 关闭 [#3912](https://github.com/NousResearch/hermes-agent/issues/3912))
- **自定义提供商context_length** 在卫生压缩中得到尊重 ([#4085](https://github.com/NousResearch/hermes-agent/pull/4085))
- **非sk-ant密钥** 被视为常规API密钥，而不是OAuth令牌 ([#4093](https://github.com/NousResearch/hermes-agent/pull/4093))
- **Claude-sonnet-4.6** 添加到OpenRouter和Nous模型列表 ([#4157](https://github.com/NousResearch/hermes-agent/pull/4157))
- **Qwen 3.6 Plus Preview** 添加到模型列表 ([#4376](https://github.com/NousResearch/hermes-agent/pull/4376))
- **MiniMax M2.7** 添加到hermes模型选择器和OpenCode ([#4208](https://github.com/NousResearch/hermes-agent/pull/4208))
- **从服务器探测自动检测模型** 在自定义端点设置中 ([#4218](https://github.com/NousResearch/hermes-agent/pull/4218))
- **Config.yaml作为端点URL的唯一真实来源** — 不再有环境变量与config.yaml冲突 ([#4165](https://github.com/NousResearch/hermes-agent/pull/4165))
- **设置向导不再覆盖** 自定义端点配置 ([#4180](https://github.com/NousResearch/hermes-agent/pull/4180), 关闭 [#4172](https://github.com/NousResearch/hermes-agent/issues/4172))
- **统一的设置向导提供商选择** 与`hermes model` — 两个流程的单一代码路径 ([#4200](https://github.com/NousResearch/hermes-agent/pull/4200))